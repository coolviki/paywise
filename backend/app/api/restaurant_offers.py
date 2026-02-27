"""
Restaurant offers API with SSE streaming.
Fetches real-time dine-in offers from Swiggy Dineout, Zomato, EazyDiner, etc.
"""

import json
import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import get_current_user, verify_token
from ..core.config import settings
from ..models.user import User
from ..services.llm_search import get_llm_search_provider, RestaurantOffer, LLMSearchProvider
from ..services.llm_search.base import Platform, SearchResult

router = APIRouter()


def get_user_from_token_param(
    token: Optional[str] = Query(None, description="Auth token (for SSE)"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Get user from token query param or Authorization header.
    For SSE endpoints that can't use standard auth headers.
    """
    # Try Authorization header first
    actual_token = None
    if authorization and authorization.startswith("Bearer "):
        actual_token = authorization[7:]
    elif token:
        actual_token = token

    if not actual_token:
        return None

    payload = verify_token(actual_token)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user = db.query(User).filter(User.id == user_id).first()
    return user


class RestaurantOffersRequest(BaseModel):
    """Request for restaurant offers."""
    restaurant_name: str
    city: str
    platforms: Optional[list[str]] = None  # ["swiggy_dineout", "zomato"]


class RestaurantOffersResponse(BaseModel):
    """Response with all restaurant offers."""
    restaurant_name: str
    city: str
    offers: list[RestaurantOffer]
    summary: Optional[str] = None
    sources: list[str] = []
    provider: str


def _get_provider() -> Optional[LLMSearchProvider]:
    """Get LLM search provider from config."""
    try:
        return get_llm_search_provider(
            provider_type=settings.llm_search_provider,
            perplexity_api_key=settings.perplexity_api_key,
            tavily_api_key=settings.tavily_api_key,
            gemini_api_key=settings.gemini_api_key,
        )
    except Exception:
        return None


def _parse_platforms(platforms: Optional[list[str]]) -> Optional[list[Platform]]:
    """Parse platform strings to Platform enums."""
    if not platforms:
        return None

    mapping = {
        "swiggy_dineout": Platform.SWIGGY_DINEOUT,
        "swiggy": Platform.SWIGGY_DINEOUT,
        "zomato": Platform.ZOMATO,
        "eazydiner": Platform.EAZYDINER,
        "dineout": Platform.DINEOUT,
        "magicpin": Platform.MAGICPIN,
    }

    return [mapping[p.lower()] for p in platforms if p.lower() in mapping]


@router.post("", response_model=RestaurantOffersResponse)
async def get_restaurant_offers(
    request: RestaurantOffersRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Get dine-in offers for a restaurant from all platforms.
    Returns structured offers from Swiggy Dineout, Zomato, EazyDiner, etc.
    """
    provider = _get_provider()
    if not provider:
        raise HTTPException(
            status_code=503,
            detail="Restaurant offers service not configured. Please set up LLM search provider.",
        )

    platforms = _parse_platforms(request.platforms)

    try:
        result = await provider.search_restaurant_offers(
            restaurant_name=request.restaurant_name,
            city=request.city,
            platforms=platforms,
        )

        return RestaurantOffersResponse(
            restaurant_name=result.restaurant_name,
            city=result.city,
            offers=result.offers,
            summary=result.summary,
            sources=result.sources,
            provider=result.provider,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch restaurant offers: {str(e)}",
        )


@router.get("/stream")
async def stream_restaurant_offers(
    restaurant_name: str = Query(..., description="Restaurant name"),
    city: str = Query(..., description="City name"),
    platforms: Optional[str] = Query(None, description="Comma-separated platforms"),
    user: Optional[User] = Depends(get_user_from_token_param),
):
    """
    Stream restaurant offers via Server-Sent Events (SSE).

    Each event contains a single offer as JSON:
    ```
    data: {"platform": "swiggy_dineout", "discount_text": "40% off", ...}

    data: {"platform": "zomato", "discount_text": "20% off with HDFC", ...}

    event: done
    data: {"summary": "Best deal is 40% off on Swiggy Dineout", "total_offers": 5}
    ```

    Connect using EventSource:
    ```javascript
    const es = new EventSource('/api/restaurant-offers/stream?restaurant_name=Bercos&city=Delhi&token=...');
    es.onmessage = (e) => { const offer = JSON.parse(e.data); };
    es.addEventListener('done', (e) => { es.close(); });
    ```
    """
    # Auth check (SSE requires token via query param since EventSource doesn't support headers)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Pass token as query parameter.",
        )

    provider = _get_provider()
    if not provider:
        raise HTTPException(
            status_code=503,
            detail="Restaurant offers service not configured",
        )

    platform_list = platforms.split(",") if platforms else None
    parsed_platforms = _parse_platforms(platform_list)

    async def event_generator():
        """Generate SSE events for each offer."""
        offers_count = 0
        summary = None

        try:
            # First, send a "start" event
            yield f"event: start\ndata: {json.dumps({'restaurant_name': restaurant_name, 'city': city})}\n\n"

            # Stream offers
            async for offer in provider.search_restaurant_offers_stream(
                restaurant_name=restaurant_name,
                city=city,
                platforms=parsed_platforms,
            ):
                offers_count += 1
                # Send each offer as a message event
                offer_data = offer.model_dump()
                yield f"data: {json.dumps(offer_data)}\n\n"

                # Small delay for better UX (feels more real-time)
                await asyncio.sleep(0.1)

            # If streaming didn't work well, fall back to batch
            if offers_count == 0:
                result = await provider.search_restaurant_offers(
                    restaurant_name=restaurant_name,
                    city=city,
                    platforms=parsed_platforms,
                )
                for offer in result.offers:
                    offers_count += 1
                    offer_data = offer.model_dump()
                    yield f"data: {json.dumps(offer_data)}\n\n"
                    await asyncio.sleep(0.1)
                summary = result.summary

            # Send completion event
            done_data = {
                "summary": summary,
                "total_offers": offers_count,
            }
            yield f"event: done\ndata: {json.dumps(done_data)}\n\n"

        except Exception as e:
            # Send error event
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get("/test")
async def test_offers(
    restaurant_name: str = Query("Bercos", description="Restaurant name"),
    city: str = Query("Delhi", description="City name"),
):
    """
    Test endpoint (no auth required) to verify the service is working.
    Returns mock data if provider is not configured.
    """
    provider = _get_provider()

    if not provider:
        # Return mock data for testing
        return {
            "status": "mock",
            "message": "LLM search provider not configured. Returning mock data.",
            "offers": [
                {
                    "platform": "swiggy_dineout",
                    "platform_display_name": "Swiggy Dineout",
                    "offer_type": "pre-booked",
                    "discount_text": "40% off on pre-booked meals (mock)",
                    "discount_percentage": 40,
                    "max_discount": 200,
                },
                {
                    "platform": "zomato",
                    "platform_display_name": "Zomato",
                    "offer_type": "bank_offer",
                    "discount_text": "20% off up to Rs 500 with HDFC cards (mock)",
                    "discount_percentage": 20,
                    "max_discount": 500,
                    "bank_name": "HDFC",
                },
            ],
        }

    try:
        result = await provider.search_restaurant_offers(
            restaurant_name=restaurant_name,
            city=city,
        )
        return {
            "status": "live",
            "provider": provider.provider_name,
            "restaurant_name": result.restaurant_name,
            "city": result.city,
            "offers": [o.model_dump() for o in result.offers],
            "summary": result.summary,
            "sources": result.sources,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }

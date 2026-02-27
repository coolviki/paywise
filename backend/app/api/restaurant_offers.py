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
from ..models.card import PaymentMethod
from ..services.llm_search import get_llm_search_provider, RestaurantOffer, LLMSearchProvider
from ..services.llm_search.base import Platform, SearchResult


def _get_user_enabled_platforms(db: Session, user_id) -> Optional[list[Platform]]:
    """Get user's enabled dine-out app platforms. Returns None if user hasn't set any (show all)."""
    enabled_apps = (
        db.query(PaymentMethod)
        .filter(
            PaymentMethod.user_id == user_id,
            PaymentMethod.payment_type == "dineout_app",
            PaymentMethod.is_active == True,
        )
        .all()
    )

    if not enabled_apps:
        return None  # No apps selected, show all platforms

    # Map app codes to Platform enums
    platform_map = {
        "swiggy_dineout": Platform.SWIGGY_DINEOUT,
        "zomato_pay": Platform.ZOMATO_PAY,
        "eazydiner": Platform.EAZYDINER,
        "district": Platform.DISTRICT,
    }

    platforms = []
    for pm in enabled_apps:
        if pm.nickname in platform_map:
            platforms.append(platform_map[pm.nickname])

    return platforms if platforms else None

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
    import logging
    logger = logging.getLogger(__name__)

    try:
        # Debug: log what we're getting from settings
        logger.info(f"LLM Search Provider: {settings.llm_search_provider}")
        logger.info(f"Perplexity API Key set: {bool(settings.perplexity_api_key)}")
        logger.info(f"Tavily API Key set: {bool(settings.tavily_api_key)}")

        return get_llm_search_provider(
            provider_type=settings.llm_search_provider,
            perplexity_api_key=settings.perplexity_api_key,
            tavily_api_key=settings.tavily_api_key,
            gemini_api_key=settings.gemini_api_key,
        )
    except Exception as e:
        logger.error(f"Failed to create LLM search provider: {e}")
        return None


def _parse_platforms(platforms: Optional[list[str]]) -> Optional[list[Platform]]:
    """Parse platform strings to Platform enums."""
    if not platforms:
        return None

    mapping = {
        "swiggy_dineout": Platform.SWIGGY_DINEOUT,
        "swiggy": Platform.SWIGGY_DINEOUT,
        "zomato_pay": Platform.ZOMATO_PAY,
        "zomato": Platform.ZOMATO_PAY,
        "eazydiner": Platform.EAZYDINER,
        "district": Platform.DISTRICT,
    }

    return [mapping[p.lower()] for p in platforms if p.lower() in mapping]


@router.post("", response_model=RestaurantOffersResponse)
async def get_restaurant_offers(
    request: RestaurantOffersRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get dine-in offers for a restaurant from user's enabled platforms.
    If no platforms specified in request, uses user's enabled dine-out apps.
    """
    provider = _get_provider()
    if not provider:
        raise HTTPException(
            status_code=503,
            detail="Restaurant offers service not configured. Please set up LLM search provider.",
        )

    # Use platforms from request, or fall back to user's enabled apps
    if request.platforms:
        platforms = _parse_platforms(request.platforms)
    else:
        platforms = _get_user_enabled_platforms(db, current_user.id)

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
    platforms: Optional[str] = Query(None, description="Comma-separated platforms (overrides user settings)"),
    user: Optional[User] = Depends(get_user_from_token_param),
    db: Session = Depends(get_db),
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

    # Use platforms from query param, or fall back to user's enabled apps
    if platforms:
        platform_list = platforms.split(",")
        parsed_platforms = _parse_platforms(platform_list)
    else:
        # Get user's enabled dine-out apps
        parsed_platforms = _get_user_enabled_platforms(db, user.id)

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
        # Return debug info about why provider isn't configured
        return {
            "status": "not_configured",
            "message": "LLM search provider not configured.",
            "debug": {
                "llm_search_provider": settings.llm_search_provider,
                "perplexity_api_key_set": bool(settings.perplexity_api_key),
                "perplexity_api_key_prefix": settings.perplexity_api_key[:10] + "..." if settings.perplexity_api_key else None,
                "tavily_api_key_set": bool(settings.tavily_api_key),
                "gemini_api_key_set": bool(settings.gemini_api_key),
            },
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

"""
Restaurant offers API with SSE streaming.
Fetches real-time dine-in offers from Swiggy Dineout, Zomato, EazyDiner, etc.
"""

import json
import asyncio
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Header, Request
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

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _get_user_enabled_platforms(db: Session, user_id) -> Optional[list[Platform]]:
    """Get user's enabled dine-out app platforms. Returns None if user hasn't set any (show all)."""
    logger.info(f"[PLATFORMS] Fetching enabled platforms for user_id={user_id}")

    enabled_apps = (
        db.query(PaymentMethod)
        .filter(
            PaymentMethod.user_id == user_id,
            PaymentMethod.payment_type == "dineout_app",
            PaymentMethod.is_active == True,
        )
        .all()
    )

    logger.info(f"[PLATFORMS] Found {len(enabled_apps)} enabled dine-out apps for user_id={user_id}")
    for app in enabled_apps:
        logger.info(f"[PLATFORMS]   - {app.nickname} (active={app.is_active})")

    if not enabled_apps:
        logger.info(f"[PLATFORMS] No apps selected for user_id={user_id}, will show all platforms")
        return None  # No apps selected, show all platforms

    # Map app codes to Platform enums
    platform_map = {
        "swiggy_dineout": Platform.SWIGGY_DINEOUT,
        "eazydiner": Platform.EAZYDINER,
        "district": Platform.DISTRICT,
    }

    platforms = []
    for pm in enabled_apps:
        if pm.nickname in platform_map:
            platforms.append(platform_map[pm.nickname])
        else:
            logger.warning(f"[PLATFORMS] Unknown platform nickname: {pm.nickname}")

    logger.info(f"[PLATFORMS] Resolved platforms for user_id={user_id}: {[p.value for p in platforms]}")
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
    request: Request,
    restaurant_name: str = Query(..., description="Restaurant name"),
    city: str = Query(..., description="City name"),
    platforms: Optional[str] = Query(None, description="Comma-separated platforms (overrides user settings)"),
    parallel: bool = Query(True, description="Use parallel LLM calls for each platform (more complete results)"),
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
    # Log request details
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    logger.info(f"[STREAM] ========== NEW REQUEST ==========")
    logger.info(f"[STREAM] Client IP: {client_ip}")
    logger.info(f"[STREAM] User-Agent: {user_agent[:100]}")
    logger.info(f"[STREAM] Restaurant: '{restaurant_name}', City: '{city}'")
    logger.info(f"[STREAM] Platforms param: {platforms}")
    logger.info(f"[STREAM] Parallel mode: {parallel}")

    # Auth check (SSE requires token via query param since EventSource doesn't support headers)
    if not user:
        logger.warning(f"[STREAM] Auth failed - no valid user token")
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Pass token as query parameter.",
        )

    logger.info(f"[STREAM] User: {user.email} (id={user.id})")

    provider = _get_provider()
    if not provider:
        logger.error(f"[STREAM] LLM provider not configured!")
        raise HTTPException(
            status_code=503,
            detail="Restaurant offers service not configured",
        )

    logger.info(f"[STREAM] Using provider: {provider.provider_name}")

    # Use platforms from query param, or fall back to user's enabled apps
    if platforms:
        platform_list = platforms.split(",")
        parsed_platforms = _parse_platforms(platform_list)
        logger.info(f"[STREAM] Using platforms from query param: {[p.value for p in parsed_platforms] if parsed_platforms else 'all'}")
    else:
        # Get user's enabled dine-out apps
        parsed_platforms = _get_user_enabled_platforms(db, user.id)
        logger.info(f"[STREAM] Using user's enabled platforms: {[p.value for p in parsed_platforms] if parsed_platforms else 'all (none configured)'}")

    async def event_generator():
        """Generate SSE events for each offer."""
        offers_count = 0
        summary = None
        request_id = f"{user.id}:{restaurant_name}:{city}"

        try:
            logger.info(f"[STREAM:{request_id}] Starting event generator")

            # First, send a "start" event
            yield f"event: start\ndata: {json.dumps({'restaurant_name': restaurant_name, 'city': city})}\n\n"

            # Stream offers
            logger.info(f"[STREAM:{request_id}] Calling search_restaurant_offers_stream...")
            async for offer in provider.search_restaurant_offers_stream(
                restaurant_name=restaurant_name,
                city=city,
                platforms=parsed_platforms,
                parallel=parallel,
            ):
                offers_count += 1
                platform_name = offer.platform.value if hasattr(offer.platform, 'value') else str(offer.platform)
                logger.info(f"[STREAM:{request_id}] Offer #{offers_count}: {platform_name} - {offer.discount_text[:50] if offer.discount_text else 'N/A'}")
                # Send each offer as a message event
                offer_data = offer.model_dump()
                yield f"data: {json.dumps(offer_data)}\n\n"

                # Small delay for better UX (feels more real-time)
                await asyncio.sleep(0.1)

            logger.info(f"[STREAM:{request_id}] Stream completed with {offers_count} offers")

            # If streaming didn't work well, fall back to batch
            if offers_count == 0:
                logger.info(f"[STREAM:{request_id}] No streaming offers, falling back to batch search...")
                result = await provider.search_restaurant_offers(
                    restaurant_name=restaurant_name,
                    city=city,
                    platforms=parsed_platforms,
                    parallel=parallel,
                )
                logger.info(f"[STREAM:{request_id}] Batch search returned {len(result.offers)} offers")
                for offer in result.offers:
                    offers_count += 1
                    platform_name = offer.platform.value if hasattr(offer.platform, 'value') else str(offer.platform)
                    logger.info(f"[STREAM:{request_id}] Batch offer #{offers_count}: {platform_name} - {offer.discount_text[:50] if offer.discount_text else 'N/A'}")
                    offer_data = offer.model_dump()
                    yield f"data: {json.dumps(offer_data)}\n\n"
                    await asyncio.sleep(0.1)
                summary = result.summary

            # Send completion event
            done_data = {
                "summary": summary,
                "total_offers": offers_count,
            }
            logger.info(f"[STREAM:{request_id}] ========== COMPLETE: {offers_count} offers ==========")
            yield f"event: done\ndata: {json.dumps(done_data)}\n\n"

        except Exception as e:
            logger.error(f"[STREAM:{request_id}] ERROR: {str(e)}", exc_info=True)
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

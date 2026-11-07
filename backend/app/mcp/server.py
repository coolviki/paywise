"""PayWise MCP server - lets Claude (web, desktop, mobile) answer
"which card should I use?" from the user's own cards and live offers.

Security model (Phase 1):
  * Every request to /mcp must carry `Authorization: Bearer pw_live_...`
    (a personal key the user generates in Settings > Connect to Claude).
  * McpBearerAuth resolves the key to a user and stores the user id on the
    request. Tools read it from there.
  * NO tool takes a user id / email argument, so Claude cannot ask for
    another user's data even if prompted to.
  * All tools are read-only.
"""
import asyncio
import logging
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from starlette.responses import JSONResponse

from ..core.database import SessionLocal
from ..models.campaign import Campaign
from ..models.card import Card
from ..models.offer import Offer
from ..api.restaurant_offers import _get_provider, _get_user_enabled_platforms
from ..services.llm_search.base import Platform
from ..services.location_service import LocationService
from ..services.mcp_key_service import McpKeyService
from ..services.recommendation_service import (
    _get_category_type,
    load_user_payment_methods,
    rank_cards_for_user,
)

logger = logging.getLogger(__name__)

USER_STATE_KEY = "paywise_user_id"
RESTAURANT_SEARCH_TIMEOUT_S = 50

PLATFORM_ALIASES = {
    "swiggy": Platform.SWIGGY_DINEOUT,
    "swiggy_dineout": Platform.SWIGGY_DINEOUT,
    "dineout": Platform.SWIGGY_DINEOUT,
    "eazydiner": Platform.EAZYDINER,
    "district": Platform.DISTRICT,
    # Zomato's dining-out business moved to District
    "zomato": Platform.DISTRICT,
}
ALL_DINEOUT_PLATFORMS = [Platform.SWIGGY_DINEOUT, Platform.EAZYDINER, Platform.DISTRICT]

_GENERIC_BANK_WORDS = {"bank", "card", "cards", "credit", "debit", "ltd", "limited", "of", "the", "india", "&", "and"}
_BANK_SYNONYMS = {"american": "amex", "express": "amex", "state": "sbi", "kotak": "kotak", "hongkong": "hsbc"}


def _bank_tokens(name: Optional[str]) -> set:
    """Distinctive words of a bank name: "HDFC Bank" -> {"hdfc"}, "Bank of Baroda" -> {"baroda"}."""
    if not name:
        return set()
    words = name.lower().replace(".", " ").replace("-", " ").split()
    return {_BANK_SYNONYMS.get(w, w) for w in words if w not in _GENERIC_BANK_WORDS}

INSTRUCTIONS = """PayWise knows which credit/debit cards this user holds and the
reward rates, brand ecosystem benefits and bank offers that apply to them (India, INR).

How to answer "which card should I use?":
1. If the merchant is ambiguous, call find_place to identify it and its category.
2. Call recommend_card with the merchant name, amount (if known) and category.
   The ranking is computed by PayWise - trust its numbers, do not recalculate rates.
3. Optionally call get_card_offers for time-limited bank offers at that merchant.
4. For RESTAURANTS / dining out, ALSO call get_restaurant_offers (needs the city) to get
   Swiggy Dineout, EazyDiner and District (formerly Zomato dining) deals. These stack with
   the card reward: suggest the best app deal + the best card to pay with. If an app offer is
   bank-specific and matches_your_cards is true, that usually beats the plain card reward.
5. Answer with the best card first, the estimated reward in rupees, and the runner-up.
   Mention validity dates for campaigns/offers. Never invent offers that no tool returned.
If the user has no cards saved, tell them to add cards at paywise.vikramkumar.org."""

READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False)

paywise_mcp = FastMCP(
    name="PayWise",
    instructions=INSTRUCTIONS,
    stateless_http=True,
    json_response=True,
    streamable_http_path="/mcp",
    # The SDK auto-enables localhost-only Host checks, which would reject
    # requests on Railway's public domain. Auth is enforced by bearer key instead.
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)


# ---------------------------------------------------------------------------
# MCP Apps views (interactive cards rendered inside Claude)
# Source: app/mcp/ui/src  ->  built by `npm run build` into app/mcp/ui/dist
# ---------------------------------------------------------------------------
MCP_APP_MIME_TYPE = "text/html;profile=mcp-app"
UI_DIST = Path(__file__).parent / "ui" / "dist"
RESTAURANT_OFFERS_UI = "ui://paywise/restaurant-offers.html"
CARD_RANKING_UI = "ui://paywise/card-ranking.html"


def _ui_meta(uri: str) -> dict:
    # "ui/resourceUri" is the legacy key some hosts still read
    return {"ui": {"resourceUri": uri}, "ui/resourceUri": uri}


@lru_cache(maxsize=None)
def _load_view(name: str) -> str:
    return (UI_DIST / f"{name}.html").read_text(encoding="utf-8")


# Views are fully self-contained (inline CSS/JS), so no CSP domains are needed.
_VIEW_RESOURCE_META = {"ui": {"prefersBorder": False}}


@paywise_mcp.resource(
    RESTAURANT_OFFERS_UI,
    name="restaurant_offers_view",
    title="Dine-out offers card",
    mime_type=MCP_APP_MIME_TYPE,
    meta=_VIEW_RESOURCE_META,
)
def restaurant_offers_view() -> str:
    return _load_view("restaurant-offers")


@paywise_mcp.resource(
    CARD_RANKING_UI,
    name="card_ranking_view",
    title="Card ranking card",
    mime_type=MCP_APP_MIME_TYPE,
    meta=_VIEW_RESOURCE_META,
)
def card_ranking_view() -> str:
    return _load_view("card-ranking")


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class McpBearerAuth:
    """ASGI wrapper: rejects requests without a valid PayWise key and records
    which user the key belongs to."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        auth = headers.get("authorization", "")
        raw_key = auth[7:].strip() if auth.lower().startswith("bearer ") else None

        db = SessionLocal()
        try:
            user = McpKeyService.authenticate(db, raw_key)
            user_id = user.id if user else None
        finally:
            db.close()

        if user_id is None:
            response = JSONResponse(
                {
                    "error": "unauthorized",
                    "error_description": "Missing or invalid PayWise API key. "
                    "Generate one in PayWise > Settings > Connect to Claude.",
                },
                status_code=401,
                headers={"WWW-Authenticate": 'Bearer realm="PayWise"'},
            )
            await response(scope, receive, send)
            return

        scope.setdefault("state", {})[USER_STATE_KEY] = str(user_id)
        await self.app(scope, receive, send)


def _current_user_id(ctx: Context) -> UUID:
    """The ONLY way tools learn who the user is."""
    request = ctx.request_context.request
    user_id = getattr(request.state, USER_STATE_KEY, None) if request is not None else None
    if not user_id:
        # Should be impossible behind McpBearerAuth - fail closed.
        raise PermissionError("Not authenticated")
    return UUID(user_id)


# ---------------------------------------------------------------------------
# Tools (all read-only)
# ---------------------------------------------------------------------------
@paywise_mcp.tool(annotations=READ_ONLY)
def list_my_cards(ctx: Context) -> dict:
    """List the credit/debit cards the user has saved in PayWise, with each
    card's reward type, base reward rate and annual fee."""
    user_id = _current_user_id(ctx)
    db = SessionLocal()
    try:
        cards = []
        for pm in load_user_payment_methods(db, user_id):
            if not pm.card:
                continue
            cards.append({
                "card_name": pm.card.name,
                "bank": pm.card.bank.name if pm.card.bank else None,
                "nickname": pm.nickname,
                "card_type": pm.card.card_type,
                "network": pm.card.card_network,
                "reward_type": pm.card.reward_type,
                "base_reward_rate_percent": float(pm.card.base_reward_rate) if pm.card.base_reward_rate else None,
                "annual_fee_inr": float(pm.card.annual_fee) if pm.card.annual_fee else None,
            })
        return {"count": len(cards), "cards": cards}
    finally:
        db.close()


@paywise_mcp.tool(annotations=READ_ONLY, meta=_ui_meta(CARD_RANKING_UI))
def recommend_card(
    ctx: Context,
    merchant: str,
    amount_inr: Optional[float] = None,
    category: Optional[str] = None,
) -> dict:
    """Rank ALL of the user's cards for a purchase at a merchant, best first.

    Args:
        merchant: Merchant or brand name, e.g. "Taj Mahal Palace", "BigBasket", "Croma".
        amount_inr: Purchase amount in rupees, if known. Used to estimate the reward in INR.
        category: Optional category hint, e.g. "restaurant", "hotel", "fuel", "grocery",
            "electronics", "travel". Use find_place to get one if unsure.
    """
    user_id = _current_user_id(ctx)
    db = SessionLocal()
    try:
        ranked = rank_cards_for_user(db, user_id, merchant, category, amount_inr)
        if not ranked:
            return {
                "merchant": merchant,
                "ranking": [],
                "note": "No cards saved in PayWise yet. Add cards at paywise.vikramkumar.org.",
            }
        return {
            "merchant": merchant,
            "amount_inr": amount_inr,
            "category_detected": _get_category_type(category),
            "best_card": ranked[0]["card_name"],
            "ranking": ranked,
        }
    finally:
        db.close()


@paywise_mcp.tool(annotations=READ_ONLY)
def get_card_offers(ctx: Context, merchant: Optional[str] = None, limit: int = 15) -> dict:
    """Current bank offers and limited-time campaigns on the user's cards.

    Args:
        merchant: Optional merchant/brand name to filter by (matches offer title,
            description or merchant name). Omit to list all current offers.
        limit: Maximum number of offers to return (1-50).
    """
    user_id = _current_user_id(ctx)
    limit = max(1, min(limit, 50))
    today = date.today()
    db = SessionLocal()
    try:
        card_ids = [pm.card_id for pm in load_user_payment_methods(db, user_id)]
        if not card_ids:
            return {"offers": [], "campaigns": [], "note": "No cards saved in PayWise yet."}

        offer_q = (
            db.query(Offer)
            .options(joinedload(Offer.card).joinedload(Card.bank), joinedload(Offer.merchant))
            .filter(
                Offer.card_id.in_(card_ids),
                Offer.is_active == True,  # noqa: E712
                or_(Offer.valid_until.is_(None), Offer.valid_until >= today),
                or_(Offer.valid_from.is_(None), Offer.valid_from <= today),
            )
        )
        if merchant:
            like = f"%{merchant}%"
            offer_q = offer_q.filter(or_(Offer.title.ilike(like), Offer.description.ilike(like)))

        offers = [
            {
                "card_name": o.card.name if o.card else None,
                "bank": o.card.bank.name if o.card and o.card.bank else None,
                "title": o.title,
                "description": o.description,
                "merchant": o.merchant.name if o.merchant else None,
                "discount_type": o.discount_type,
                "discount_value": float(o.discount_value),
                "min_transaction_inr": float(o.min_transaction) if o.min_transaction else None,
                "max_discount_inr": float(o.max_discount) if o.max_discount else None,
                "valid_until": o.valid_until.isoformat() if o.valid_until else None,
                "source_url": o.source_url,
                "last_updated": o.updated_at.isoformat() if o.updated_at else None,
            }
            for o in offer_q.limit(limit).all()
        ]

        camp_q = (
            db.query(Campaign)
            .options(joinedload(Campaign.card), joinedload(Campaign.brand))
            .filter(
                Campaign.card_id.in_(card_ids),
                Campaign.is_active == True,  # noqa: E712
                Campaign.start_date <= today,
                Campaign.end_date >= today,
            )
        )
        campaigns = []
        for c in camp_q.limit(limit).all():
            brand_name = c.brand.name if c.brand else None
            if merchant and brand_name and merchant.lower() not in brand_name.lower() \
                    and brand_name.lower() not in merchant.lower():
                continue
            campaigns.append({
                "card_name": c.card.name if c.card else None,
                "brand": brand_name,
                "benefit_rate_percent": float(c.benefit_rate),
                "benefit_type": c.benefit_type,
                "description": c.description,
                "valid_until": c.end_date.isoformat(),
                "terms_url": c.terms_url,
            })

        return {"merchant_filter": merchant, "offers": offers, "campaigns": campaigns}
    finally:
        db.close()


@paywise_mcp.tool(annotations=READ_ONLY)
async def find_place(ctx: Context, query: str) -> dict:
    """Look up a merchant/place (Google Places) to confirm its name and category
    before calling recommend_card. Example query: "Wok in the Clouds Gurgaon"."""
    _current_user_id(ctx)  # authenticated callers only (protects the Places quota)
    results = await LocationService.search_google_places(query)
    places = []
    for p in results[:5]:
        types = p.get("types", []) or []
        places.append({
            "name": p.get("name"),
            "address": p.get("formatted_address"),
            "types": types[:5],
            "suggested_category": _get_category_type(" ".join(types)),
        })
    return {"query": query, "places": places}

@paywise_mcp.tool(
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=True),
    meta=_ui_meta(RESTAURANT_OFFERS_UI),
)
async def get_restaurant_offers(
    ctx: Context,
    restaurant: str,
    city: str,
    platforms: Optional[List[str]] = None,
) -> dict:
    """Live dine-out offers for a restaurant from Swiggy Dineout, EazyDiner and District
    (Zomato's dining-out offers now live on District). Includes pre-booked/walk-in discounts
    and bank-specific deals, flagged when they match the user's own cards.
    Searches the web live, so it can take 10-40 seconds.

    Args:
        restaurant: Restaurant name, e.g. "Wok in the Clouds".
        city: City, e.g. "Gurgaon", "Delhi", "Mumbai".
        platforms: Optional subset: "swiggy_dineout", "eazydiner", "district" (or "zomato").
            Omit to use the dine-out apps the user enabled in PayWise (or all three).
    """
    user_id = _current_user_id(ctx)

    db = SessionLocal()
    try:
        if platforms:
            selected = []
            for p in platforms:
                plat = PLATFORM_ALIASES.get(p.strip().lower())
                if plat and plat not in selected:
                    selected.append(plat)
        else:
            selected = _get_user_enabled_platforms(db, user_id)
        selected = selected or list(ALL_DINEOUT_PLATFORMS)

        user_banks = sorted({
            pm.card.bank.name for pm in load_user_payment_methods(db, user_id)
            if pm.card and pm.card.bank
        })
        ranked = rank_cards_for_user(db, user_id, restaurant, "restaurant")
        pay_with = None
        if ranked:
            top = ranked[0]
            pay_with = {k: top[k] for k in ("card_name", "bank", "reward_rate_percent", "reward_type", "reason")}
    finally:
        db.close()

    provider = _get_provider()
    if not provider:
        return {"restaurant": restaurant, "city": city, "offers": [],
                "note": "Dine-out offer search is not configured on the PayWise server."}

    try:
        result = await asyncio.wait_for(
            provider.search_restaurant_offers(restaurant_name=restaurant, city=city, platforms=selected),
            timeout=RESTAURANT_SEARCH_TIMEOUT_S,
        )
    except asyncio.TimeoutError:
        return {"restaurant": restaurant, "city": city, "offers": [],
                "note": "Dine-out offer search timed out. Try again, or narrow platforms."}
    except Exception as e:  # provider/network failure should not break the chat
        logger.exception("get_restaurant_offers failed")
        return {"restaurant": restaurant, "city": city, "offers": [],
                "note": f"Could not fetch dine-out offers right now ({type(e).__name__})."}

    user_bank_tokens = [_bank_tokens(b) for b in user_banks]

    def _matches(bank_name: Optional[str]) -> bool:
        tokens = _bank_tokens(bank_name)
        return bool(tokens) and any(tokens & ub for ub in user_bank_tokens)

    offers = []
    for o in result.offers:
        d = o.model_dump() if hasattr(o, "model_dump") else dict(o)
        d["platform"] = getattr(d.get("platform"), "value", d.get("platform"))
        d["matches_your_cards"] = _matches(d.get("bank_name"))
        offers.append({k: v for k, v in d.items() if v not in (None, "")})

    return {
        "restaurant": result.restaurant_name,
        "city": result.city,
        "platforms_searched": [p.value for p in selected],
        "your_card_banks": user_banks,
        "pay_with": pay_with,
        "offers": offers,
        "summary": result.summary,
        "sources": result.sources[:8],
    }

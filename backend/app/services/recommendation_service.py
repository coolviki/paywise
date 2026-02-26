from typing import List, Optional, Dict, Tuple
from uuid import UUID
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session, joinedload

from ..models.card import Card, PaymentMethod, CardEcosystemBenefit
from ..models.merchant import BrandKeyword
from ..models.campaign import Campaign
from ..schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
    CardRecommendation,
)


# Bank source URLs for T&C
BANK_SOURCE_URLS = {
    "HDFC Bank": "https://www.hdfcbank.com/personal/pay/cards/credit-cards",
    "ICICI Bank": "https://www.icicibank.com/personal-banking/cards/credit-card",
    "SBI Card": "https://www.sbicard.com/en/personal/credit-cards.page",
    "Axis Bank": "https://www.axisbank.com/retail/cards/credit-card",
    "Kotak Bank": "https://www.kotak.com/en/personal-banking/cards/credit-cards.html",
    "AMEX": "https://www.americanexpress.com/in/credit-cards/",
}

# Category mapping for insights
CATEGORY_HINTS = {
    "restaurant": "dining",
    "cafe": "dining",
    "bar": "dining",
    "food": "dining",
    "bakery": "dining",
    "gas_station": "fuel",
    "fuel": "fuel",
    "petrol": "fuel",
    "grocery": "grocery",
    "supermarket": "grocery",
    "store": "shopping",
    "mall": "shopping",
    "shopping": "shopping",
    "clothing": "shopping",
    "electronics": "shopping",
    "airport": "travel",
    "hotel": "travel",
    "travel": "travel",
    "airline": "travel",
}


def _resolve_ecosystem_benefits(
    db: Session,
    place_name: str,
    payment_methods: List[PaymentMethod],
) -> Dict[str, dict]:
    """
    Match the place name against brand keywords.
    Returns {card_id_str: benefit_dict} for cards that have an ecosystem
    benefit or active campaign for the matched brand.
    Uses whichever has the higher rate (campaign or ecosystem benefit).
    Returns {} when no brand keyword matches.
    """
    place_lower = place_name.lower()

    # Load all keywords with their brand eagerly (small table, safe to load all)
    all_keywords = (
        db.query(BrandKeyword)
        .options(joinedload(BrandKeyword.brand))
        .all()
    )

    matched_brand = None
    for bk in all_keywords:
        if bk.keyword in place_lower:
            matched_brand = bk.brand
            break

    if not matched_brand:
        return {}

    # Fetch active ecosystem benefits for this brand
    benefits = (
        db.query(CardEcosystemBenefit)
        .filter(
            CardEcosystemBenefit.brand_id == matched_brand.id,
            CardEcosystemBenefit.is_active == True,
        )
        .all()
    )

    benefit_by_card = {str(b.card_id): b for b in benefits}

    # Fetch active campaigns for this brand (within date range)
    today = date.today()
    campaigns = (
        db.query(Campaign)
        .filter(
            Campaign.brand_id == matched_brand.id,
            Campaign.is_active == True,
            Campaign.start_date <= today,
            Campaign.end_date >= today,
        )
        .all()
    )

    campaign_by_card = {str(c.card_id): c for c in campaigns}

    # Only return benefits for cards the user actually holds
    result = {}
    for pm in payment_methods:
        card_id_str = str(pm.card_id)

        ecosystem_benefit = benefit_by_card.get(card_id_str)
        campaign = campaign_by_card.get(card_id_str)

        # Determine which has higher rate
        eco_rate = float(ecosystem_benefit.benefit_rate) if ecosystem_benefit else 0
        camp_rate = float(campaign.benefit_rate) if campaign else 0

        if campaign and camp_rate >= eco_rate:
            # Use campaign (higher or equal rate)
            result[card_id_str] = {
                "brand_name": matched_brand.name,
                "benefit_rate": camp_rate,
                "benefit_type": campaign.benefit_type,
                "description": campaign.description,
                "is_campaign": True,
                "campaign_end_date": campaign.end_date.isoformat(),
            }
        elif ecosystem_benefit:
            # Use ecosystem benefit
            result[card_id_str] = {
                "brand_name": matched_brand.name,
                "benefit_rate": eco_rate,
                "benefit_type": ecosystem_benefit.benefit_type,
                "description": ecosystem_benefit.description,
                "is_campaign": False,
                "campaign_end_date": None,
            }

    return result


def _get_category_type(place_category: Optional[str]) -> str:
    """Map place category to reward category."""
    if not place_category:
        return "general"
    cat_lower = place_category.lower()
    for keyword, category_type in CATEGORY_HINTS.items():
        if keyword in cat_lower:
            return category_type
    return "general"


def _get_effective_rate(
    pm: PaymentMethod,
    ecosystem_benefits: Dict[str, dict],
) -> Tuple[float, str, Optional[str]]:
    """
    Get effective reward rate for a card.
    Returns (rate, reward_type, benefit_description).
    """
    card_id_str = str(pm.card_id)
    benefit = ecosystem_benefits.get(card_id_str)

    if benefit:
        return (
            benefit["benefit_rate"],
            benefit["benefit_type"],
            benefit.get("description"),
        )

    base_rate = float(pm.card.base_reward_rate) if pm.card.base_reward_rate else 0.0
    reward_type = pm.card.reward_type or "rewards"
    return (base_rate, reward_type, None)


def _format_savings(rate: float, reward_type: str, transaction_amount: Optional[float] = None) -> str:
    """Format estimated savings string."""
    if transaction_amount and rate > 0:
        savings_amount = (rate / 100) * transaction_amount
        return f"₹{savings_amount:.0f} {reward_type} ({rate}%)"
    return f"{rate}% {reward_type}"


def _generate_reason(
    pm: PaymentMethod,
    ecosystem_benefits: Dict[str, dict],
    place_name: str,
) -> str:
    """Generate a reason for the recommendation."""
    card_id_str = str(pm.card_id)
    benefit = ecosystem_benefits.get(card_id_str)

    if benefit:
        return f"{benefit['benefit_rate']}% {benefit['benefit_type']} on {benefit['brand_name']}"

    rate = float(pm.card.base_reward_rate) if pm.card.base_reward_rate else 0.0
    reward_type = pm.card.reward_type or "rewards"
    return f"{rate}% {reward_type} on all purchases"


def _generate_insight(
    best_pm: PaymentMethod,
    ecosystem_benefits: Dict[str, dict],
    place_name: str,
    category_type: str,
) -> str:
    """Generate an insight for the recommendation."""
    card_id_str = str(best_pm.card_id)
    benefit = ecosystem_benefits.get(card_id_str)
    card_name = best_pm.card.name

    if benefit:
        base_insight = f"Use {card_name} at {place_name} to earn {benefit['benefit_rate']}% {benefit['benefit_type']}."
        # Add campaign end date if it's a time-limited campaign
        if benefit.get("is_campaign") and benefit.get("campaign_end_date"):
            end_date = benefit["campaign_end_date"]
            # Format the date nicely
            from datetime import datetime
            try:
                end_dt = datetime.fromisoformat(end_date)
                formatted_date = end_dt.strftime("%b %d")
                base_insight += f" Limited time offer until {formatted_date}!"
            except:
                pass
        return base_insight

    rate = float(best_pm.card.base_reward_rate) if best_pm.card.base_reward_rate else 0.0
    reward_type = best_pm.card.reward_type or "rewards"

    if category_type != "general":
        return f"{card_name} gives you {rate}% {reward_type} on {category_type} purchases."

    return f"{card_name} earns {rate}% {reward_type} on this purchase."


class RecommendationService:
    @staticmethod
    async def get_recommendation(
        db: Session,
        user_id: UUID,
        request: RecommendationRequest,
    ) -> Optional[RecommendationResponse]:
        """Get payment recommendation using database logic."""

        # Get user's payment methods
        payment_methods = (
            db.query(PaymentMethod)
            .options(
                joinedload(PaymentMethod.card).joinedload(Card.bank),
            )
            .filter(
                PaymentMethod.user_id == user_id,
                PaymentMethod.is_active == True,
                PaymentMethod.card_id.isnot(None),
            )
            .all()
        )

        if not payment_methods:
            return None

        # Resolve brand ecosystem benefits for this place
        ecosystem_benefits = _resolve_ecosystem_benefits(
            db=db,
            place_name=request.place_name,
            payment_methods=payment_methods,
        )

        transaction_amount = float(request.transaction_amount) if request.transaction_amount else None
        category_type = _get_category_type(request.place_category)

        # Rank cards by effective rate (ecosystem benefit or base rate)
        ranked_cards: List[Tuple[PaymentMethod, float, str, Optional[str]]] = []
        for pm in payment_methods:
            if pm.card:
                rate, reward_type, description = _get_effective_rate(pm, ecosystem_benefits)
                ranked_cards.append((pm, rate, reward_type, description))

        # Sort by rate descending
        ranked_cards.sort(key=lambda x: x[1], reverse=True)

        if not ranked_cards:
            return None

        # Best card
        best_pm, best_rate, best_reward_type, _ = ranked_cards[0]
        best_bank_name = best_pm.card.bank.name if best_pm.card.bank else "Unknown"

        best_option = CardRecommendation(
            card_id=best_pm.card_id,
            card_name=best_pm.card.name,
            bank_name=best_bank_name,
            estimated_savings=_format_savings(best_rate, best_reward_type, transaction_amount),
            reason=_generate_reason(best_pm, ecosystem_benefits, request.place_name),
            offers=[],
            source_url=BANK_SOURCE_URLS.get(best_bank_name),
        )

        # Alternatives (up to 2)
        alternatives = []
        for pm, rate, reward_type, _ in ranked_cards[1:3]:
            bank_name = pm.card.bank.name if pm.card.bank else "Unknown"
            alternatives.append(
                CardRecommendation(
                    card_id=pm.card_id,
                    card_name=pm.card.name,
                    bank_name=bank_name,
                    estimated_savings=_format_savings(rate, reward_type, transaction_amount),
                    reason=_generate_reason(pm, ecosystem_benefits, request.place_name),
                    offers=[],
                    source_url=BANK_SOURCE_URLS.get(bank_name),
                )
            )

        return RecommendationResponse(
            place_name=request.place_name,
            place_category=request.place_category,
            best_option=best_option,
            alternatives=alternatives,
            ai_insight=_generate_insight(best_pm, ecosystem_benefits, request.place_name, category_type),
        )

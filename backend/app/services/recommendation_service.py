from typing import List, Optional, Dict
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload

from ..models.card import Card, PaymentMethod, CardEcosystemBenefit
from ..models.merchant import BrandKeyword
from ..schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
    CardRecommendation,
)
from ..agents.recommendation_agent import RecommendationAgent


# Bank source URLs for T&C
BANK_SOURCE_URLS = {
    "HDFC Bank": "https://www.hdfcbank.com/personal/pay/cards/credit-cards",
    "ICICI Bank": "https://www.icicibank.com/personal-banking/cards/credit-card",
    "SBI Card": "https://www.sbicard.com/en/personal/credit-cards.page",
    "Axis Bank": "https://www.axisbank.com/retail/cards/credit-card",
    "Kotak Bank": "https://www.kotak.com/en/personal-banking/cards/credit-cards.html",
    "AMEX": "https://www.americanexpress.com/in/credit-cards/",
}


def _resolve_ecosystem_benefits(
    db: Session,
    place_name: str,
    payment_methods: List[PaymentMethod],
) -> Dict[str, dict]:
    """
    Match the place name against brand keywords.
    Returns {card_id_str: benefit_dict} for cards that have an ecosystem
    benefit for the matched brand. Returns {} when no brand keyword matches.
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

    # Only return benefits for cards the user actually holds
    result = {}
    for pm in payment_methods:
        card_id_str = str(pm.card_id)
        if card_id_str in benefit_by_card:
            b = benefit_by_card[card_id_str]
            result[card_id_str] = {
                "brand_name": matched_brand.name,
                "benefit_rate": float(b.benefit_rate),
                "benefit_type": b.benefit_type,
                "description": b.description,
            }

    return result


class RecommendationService:
    @staticmethod
    async def get_recommendation(
        db: Session,
        user_id: UUID,
        request: RecommendationRequest,
    ) -> Optional[RecommendationResponse]:
        """Get payment recommendation for a place using LLM."""

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

        # Call LLM for recommendation
        transaction_amount = float(request.transaction_amount) if request.transaction_amount else None

        llm_result = await RecommendationAgent.get_recommendation(
            place_name=request.place_name,
            place_category=request.place_category,
            payment_methods=payment_methods,
            transaction_amount=transaction_amount,
            ecosystem_benefits=ecosystem_benefits,
        )

        if not llm_result:
            # Fallback: return first card with basic info
            pm = payment_methods[0]
            return RecommendationResponse(
                place_name=request.place_name,
                place_category=request.place_category,
                best_option=CardRecommendation(
                    card_id=pm.card_id,
                    card_name=pm.card.name,
                    bank_name=pm.card.bank.name if pm.card.bank else "Unknown",
                    estimated_savings="Check for offers",
                    reason="Default card",
                    offers=[],
                ),
                alternatives=[],
                ai_insight="Add your cards to get personalized recommendations.",
            )

        # Build card lookup
        card_lookup = {str(pm.card_id): pm for pm in payment_methods}

        # Parse best option
        best_data = llm_result.get("best_card", {})
        best_card_id = best_data.get("card_id")
        best_pm = card_lookup.get(best_card_id)

        if not best_pm:
            # Fallback to first card if LLM returned invalid card_id
            best_pm = payment_methods[0]
            best_card_id = str(best_pm.card_id)

        best_bank_name = best_pm.card.bank.name if best_pm.card.bank else "Unknown"
        best_option = CardRecommendation(
            card_id=UUID(best_card_id) if best_card_id else best_pm.card_id,
            card_name=best_pm.card.name,
            bank_name=best_bank_name,
            estimated_savings=best_data.get("estimated_savings", "Check for offers"),
            reason=best_data.get("reason", "Best available option"),
            offers=best_data.get("offers", []),
            source_url=BANK_SOURCE_URLS.get(best_bank_name),
        )

        # Parse alternatives
        alternatives = []
        for alt_data in llm_result.get("alternatives", [])[:2]:  # Max 2 alternatives
            alt_card_id = alt_data.get("card_id")
            alt_pm = card_lookup.get(alt_card_id)

            if alt_pm and alt_card_id != best_card_id:
                alt_bank_name = alt_pm.card.bank.name if alt_pm.card.bank else "Unknown"
                alternatives.append(
                    CardRecommendation(
                        card_id=UUID(alt_card_id),
                        card_name=alt_pm.card.name,
                        bank_name=alt_bank_name,
                        estimated_savings=alt_data.get("estimated_savings", ""),
                        reason=alt_data.get("reason", ""),
                        offers=alt_data.get("offers", []),
                        source_url=BANK_SOURCE_URLS.get(alt_bank_name),
                    )
                )

        return RecommendationResponse(
            place_name=request.place_name,
            place_category=request.place_category,
            best_option=best_option,
            alternatives=alternatives,
            ai_insight=llm_result.get("insight"),
        )

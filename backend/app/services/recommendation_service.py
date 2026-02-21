from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload

from ..models.card import Card, PaymentMethod
from ..schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
    CardRecommendation,
)
from ..agents.recommendation_agent import RecommendationAgent


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

        # Call LLM for recommendation
        transaction_amount = float(request.transaction_amount) if request.transaction_amount else None

        llm_result = await RecommendationAgent.get_recommendation(
            place_name=request.place_name,
            place_category=request.place_category,
            payment_methods=payment_methods,
            transaction_amount=transaction_amount,
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

        best_option = CardRecommendation(
            card_id=UUID(best_card_id) if best_card_id else best_pm.card_id,
            card_name=best_pm.card.name,
            bank_name=best_pm.card.bank.name if best_pm.card.bank else "Unknown",
            estimated_savings=best_data.get("estimated_savings", "Check for offers"),
            reason=best_data.get("reason", "Best available option"),
            offers=best_data.get("offers", []),
        )

        # Parse alternatives
        alternatives = []
        for alt_data in llm_result.get("alternatives", [])[:2]:  # Max 2 alternatives
            alt_card_id = alt_data.get("card_id")
            alt_pm = card_lookup.get(alt_card_id)

            if alt_pm and alt_card_id != best_card_id:
                alternatives.append(
                    CardRecommendation(
                        card_id=UUID(alt_card_id),
                        card_name=alt_pm.card.name,
                        bank_name=alt_pm.card.bank.name if alt_pm.card.bank else "Unknown",
                        estimated_savings=alt_data.get("estimated_savings", ""),
                        reason=alt_data.get("reason", ""),
                        offers=alt_data.get("offers", []),
                    )
                )

        return RecommendationResponse(
            place_name=request.place_name,
            place_category=request.place_category,
            best_option=best_option,
            alternatives=alternatives,
            ai_insight=llm_result.get("insight"),
        )

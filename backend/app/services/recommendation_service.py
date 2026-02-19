from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from ..models.card import Card, PaymentMethod
from ..models.merchant import Merchant
from ..models.offer import Offer, RecommendationLog
from ..schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
    CardRecommendation,
    OfferResponse,
)
from ..agents.recommendation_agent import RecommendationAgent


class RecommendationService:
    @staticmethod
    def get_applicable_offers(
        db: Session,
        merchant_id: UUID,
        card_ids: List[UUID],
        category_id: Optional[UUID] = None,
    ) -> List[Offer]:
        """Get all applicable offers for given cards and merchant."""
        today = date.today()

        query = (
            db.query(Offer)
            .options(joinedload(Offer.card).joinedload(Card.bank))
            .filter(
                Offer.is_active == True,
                Offer.card_id.in_(card_ids),
                or_(Offer.valid_from.is_(None), Offer.valid_from <= today),
                or_(Offer.valid_until.is_(None), Offer.valid_until >= today),
            )
        )

        # Filter by merchant or category
        conditions = []
        conditions.append(Offer.merchant_id == merchant_id)
        if category_id:
            conditions.append(Offer.category_id == category_id)
        conditions.append(and_(Offer.merchant_id.is_(None), Offer.category_id.is_(None)))

        query = query.filter(or_(*conditions))

        return query.all()

    @staticmethod
    def calculate_savings(
        offer: Offer, transaction_amount: Optional[Decimal] = None
    ) -> Decimal:
        """Calculate estimated savings from an offer."""
        amount = transaction_amount or Decimal("1000")  # Default assumption

        if offer.min_transaction and amount < offer.min_transaction:
            return Decimal("0")

        if offer.discount_type == "percentage":
            savings = amount * (offer.discount_value / 100)
        elif offer.discount_type in ["flat", "cashback"]:
            savings = offer.discount_value
        elif offer.discount_type == "points":
            # Assume 1 point = 0.25 INR value
            points_per_100 = offer.discount_value
            savings = (amount / 100) * points_per_100 * Decimal("0.25")
        else:
            savings = Decimal("0")

        if offer.max_discount and savings > offer.max_discount:
            savings = offer.max_discount

        return savings

    @staticmethod
    async def get_recommendation(
        db: Session,
        user_id: UUID,
        request: RecommendationRequest,
    ) -> Optional[RecommendationResponse]:
        """Get payment recommendation for a merchant."""
        # Get merchant
        merchant = (
            db.query(Merchant)
            .options(joinedload(Merchant.category))
            .filter(Merchant.id == request.merchant_id)
            .first()
        )

        if not merchant:
            return None

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

        card_ids = [pm.card_id for pm in payment_methods if pm.card_id]

        # Get applicable offers
        category_id = merchant.category_id if merchant.category else None
        offers = RecommendationService.get_applicable_offers(
            db, merchant.id, card_ids, category_id
        )

        # Calculate savings for each card
        card_recommendations = []
        for pm in payment_methods:
            if not pm.card:
                continue

            card_offers = [o for o in offers if o.card_id == pm.card_id]
            best_offer = None
            max_savings = Decimal("0")

            for offer in card_offers:
                savings = RecommendationService.calculate_savings(
                    offer, request.transaction_amount
                )
                if savings > max_savings:
                    max_savings = savings
                    best_offer = offer

            # Consider base reward rate if no offer
            if not best_offer and pm.card.base_reward_rate:
                amount = request.transaction_amount or Decimal("1000")
                base_savings = amount * (pm.card.base_reward_rate / 100)
                if pm.card.reward_type == "points":
                    base_savings = base_savings * Decimal("0.25")
                max_savings = base_savings

            offer_response = None
            if best_offer:
                offer_response = OfferResponse(
                    id=best_offer.id,
                    card_id=best_offer.card_id,
                    card_name=pm.card.name,
                    bank_name=pm.card.bank.name if pm.card.bank else None,
                    title=best_offer.title,
                    description=best_offer.description,
                    discount_type=best_offer.discount_type,
                    discount_value=best_offer.discount_value,
                    min_transaction=best_offer.min_transaction,
                    max_discount=best_offer.max_discount,
                    valid_until=best_offer.valid_until,
                )

            reason = ""
            if best_offer:
                reason = f"{best_offer.discount_value}% {best_offer.discount_type}"
                if best_offer.discount_type == "percentage":
                    reason = f"{best_offer.discount_value}% instant discount"
                elif best_offer.discount_type == "cashback":
                    reason = f"Rs.{best_offer.discount_value} cashback"
            elif pm.card.base_reward_rate:
                reason = f"{pm.card.base_reward_rate}% base rewards"

            card_recommendations.append(
                CardRecommendation(
                    card_id=pm.card_id,
                    card_name=pm.card.name,
                    bank_name=pm.card.bank.name if pm.card.bank else "Unknown",
                    estimated_savings=f"Rs.{max_savings:.0f}" if max_savings > 0 else "No savings",
                    reason=reason or "Standard rewards",
                    offer=offer_response,
                )
            )

        # Sort by savings (extract numeric value)
        card_recommendations.sort(
            key=lambda x: float(x.estimated_savings.replace("Rs.", "").replace("No savings", "0")),
            reverse=True,
        )

        if not card_recommendations:
            return None

        best = card_recommendations[0]
        alternatives = card_recommendations[1:3]

        # Generate AI insight
        ai_insight = None
        try:
            ai_insight = await RecommendationAgent.generate_insight(
                merchant=merchant,
                best_option=best,
                alternatives=alternatives,
            )
        except Exception:
            pass  # AI insight is optional

        # Log recommendation
        log = RecommendationLog(
            user_id=user_id,
            merchant_id=merchant.id,
            location_id=request.location_id,
            recommended_card_id=best.card_id,
            all_options=[r.model_dump() for r in card_recommendations],
            llm_response=ai_insight,
        )
        db.add(log)
        db.commit()

        return RecommendationResponse(
            merchant_id=merchant.id,
            merchant_name=merchant.name,
            category=merchant.category.name if merchant.category else None,
            best_option=best,
            alternatives=alternatives,
            ai_insight=ai_insight,
        )

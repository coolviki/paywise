from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from ..core.database import SessionLocal
from ..models.card import Bank, Card
from ..models.offer import Offer, OfferFetchLog
from ..agents.offer_agent import OfferAgent


class OfferFetcher:
    """Scheduled task for fetching offers from bank websites."""

    def __init__(self):
        self.agent = OfferAgent()

    async def fetch_offers_for_bank(
        self,
        db: Session,
        bank: Bank,
        fetch_type: str = "scheduled",
    ) -> int:
        """Fetch offers for a specific bank."""
        log = OfferFetchLog(
            bank_id=bank.id,
            fetch_type=fetch_type,
            status="started",
        )
        db.add(log)
        db.commit()

        try:
            # TODO: Implement actual web scraping for bank offer pages
            # For now, this is a placeholder
            offers_count = 0

            log.status = "completed"
            log.offers_count = offers_count
            log.completed_at = datetime.utcnow()
            db.commit()

            return offers_count

        except Exception as e:
            log.status = "failed"
            log.error_message = str(e)
            log.completed_at = datetime.utcnow()
            db.commit()
            raise

    async def fetch_all_offers(self, fetch_type: str = "scheduled") -> dict:
        """Fetch offers from all active banks."""
        db = SessionLocal()
        try:
            banks = db.query(Bank).filter(Bank.is_active == True).all()
            results = {}

            for bank in banks:
                try:
                    count = await self.fetch_offers_for_bank(db, bank, fetch_type)
                    results[bank.code] = {"status": "success", "count": count}
                except Exception as e:
                    results[bank.code] = {"status": "error", "error": str(e)}

            return results

        finally:
            db.close()

    @staticmethod
    def create_offer_from_data(
        db: Session,
        bank_id: UUID,
        card_name: str,
        offer_data: dict,
    ) -> Optional[Offer]:
        """Create an offer from extracted data."""
        # Find the card
        card = (
            db.query(Card)
            .filter(
                Card.bank_id == bank_id,
                Card.name.ilike(f"%{card_name}%"),
            )
            .first()
        )

        if not card:
            return None

        offer = Offer(
            card_id=card.id,
            title=offer_data.get("title", f"{card_name} Offer"),
            description=offer_data.get("terms"),
            discount_type=offer_data.get("discount_type", "percentage"),
            discount_value=offer_data.get("discount_value", 0),
            min_transaction=offer_data.get("min_transaction"),
            max_discount=offer_data.get("max_discount"),
            valid_from=offer_data.get("valid_from"),
            valid_until=offer_data.get("valid_until"),
            terms=offer_data.get("terms"),
        )

        db.add(offer)
        db.commit()
        db.refresh(offer)

        return offer

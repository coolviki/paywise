"""Scraper service that coordinates bank scrapers and manages pending changes."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session

from ...models import Card, Brand, BrandKeyword, CardEcosystemBenefit, PendingEcosystemChange, PendingBrandChange
from .base import ScrapedBenefit
from .hdfc import HDFCScraper
from .icici import ICICIScraper
from .sbi import SBIScraper

logger = logging.getLogger(__name__)


class ScraperStatus:
    """Holds the current scraper status."""

    def __init__(self):
        self.is_running = False
        self.current_bank: Optional[str] = None
        self.last_run: Optional[datetime] = None
        self.last_result: Optional[str] = None
        self.benefits_found: int = 0
        self.pending_created: int = 0
        self.brands_created: int = 0
        self.errors: List[str] = []


# Global status instance
scraper_status = ScraperStatus()


class ScraperService:
    """Service to coordinate scraping and manage pending changes."""

    SCRAPERS = {
        "hdfc": HDFCScraper,
        "icici": ICICIScraper,
        "sbi": SBIScraper,
    }

    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)

    def run_sync(self, bank: Optional[str] = None) -> Dict:
        """
        Run scrapers synchronously and create pending changes.

        Args:
            bank: Optional bank name to scrape (hdfc, icici, sbi). If None, scrapes all.

        Returns:
            Dict with scraping results
        """
        global scraper_status

        if scraper_status.is_running:
            return {"error": "Scraper is already running"}

        try:
            scraper_status.is_running = True
            scraper_status.errors = []
            scraper_status.benefits_found = 0
            scraper_status.pending_created = 0
            scraper_status.brands_created = 0

            scrapers_to_run = []
            if bank:
                if bank.lower() not in self.SCRAPERS:
                    return {"error": f"Unknown bank: {bank}"}
                scrapers_to_run = [(bank.lower(), self.SCRAPERS[bank.lower()])]
            else:
                scrapers_to_run = list(self.SCRAPERS.items())

            all_benefits = []

            for bank_name, scraper_class in scrapers_to_run:
                scraper_status.current_bank = bank_name
                self.logger.info(f"Running {bank_name} scraper...")

                try:
                    scraper = scraper_class()
                    # Run the async scraper in a sync context
                    benefits = asyncio.run(scraper.scrape())
                    all_benefits.extend(benefits)
                    scraper_status.benefits_found += len(benefits)
                except Exception as e:
                    error_msg = f"Error scraping {bank_name}: {str(e)}"
                    self.logger.error(error_msg)
                    scraper_status.errors.append(error_msg)

            # Process benefits and create pending changes
            pending_count = self._create_pending_changes(all_benefits)
            scraper_status.pending_created = pending_count

            scraper_status.last_run = datetime.utcnow()
            scraper_status.last_result = "success" if not scraper_status.errors else "partial"
            scraper_status.current_bank = None

            return {
                "status": "completed",
                "benefits_found": scraper_status.benefits_found,
                "pending_created": scraper_status.pending_created,
                "brands_created": scraper_status.brands_created,
                "errors": scraper_status.errors
            }

        except Exception as e:
            scraper_status.last_result = "failed"
            scraper_status.errors.append(str(e))
            self.logger.error(f"Scraper failed: {e}")
            return {"error": str(e)}

        finally:
            scraper_status.is_running = False
            scraper_status.current_bank = None

    def _create_pending_changes(self, benefits: List[ScrapedBenefit]) -> int:
        """Create pending ecosystem changes from scraped benefits."""
        global scraper_status
        pending_count = 0
        pending_brands_created = set()  # Track brands we've already created pending entries for

        for benefit in benefits:
            try:
                # Find matching card
                card = self._find_card(benefit.card_name)
                if not card:
                    self.logger.debug(f"Card not found: {benefit.card_name}")
                    continue

                # Find brand
                brand = self._find_brand(benefit.brand_name)
                if not brand:
                    # Create pending brand if not already pending
                    brand_code = benefit.brand_name.lower().replace(" ", "_").replace("-", "_")

                    if brand_code not in pending_brands_created:
                        # Check if there's already a pending brand with this code
                        existing_pending_brand = self._find_existing_pending_brand(brand_code)
                        if not existing_pending_brand:
                            pending_brand = PendingBrandChange(
                                name=benefit.brand_name,
                                code=brand_code,
                                description=f"Auto-discovered from {benefit.card_name} scraping",
                                keywords=[benefit.brand_name.lower()],
                                source_url=benefit.source_url,
                                source_bank=scraper_status.current_bank,
                                status="pending"
                            )
                            self.db.add(pending_brand)
                            pending_brands_created.add(brand_code)
                            scraper_status.brands_created += 1
                            self.logger.info(f"Created pending brand: {benefit.brand_name}")

                    # Skip benefit creation since brand doesn't exist yet
                    continue

                # Check if benefit already exists
                existing = self._find_existing_benefit(card.id, brand.id)

                # Check if there's already a pending change for this card/brand
                existing_pending = self._find_existing_pending(card.id, brand.id)
                if existing_pending:
                    self.logger.debug(f"Pending change already exists for {card.name} - {brand.name}")
                    continue

                if existing:
                    # Create update if rate changed
                    if float(existing.benefit_rate) != benefit.benefit_rate:
                        change = PendingEcosystemChange(
                            card_id=card.id,
                            brand_id=brand.id,
                            benefit_rate=benefit.benefit_rate,
                            benefit_type=benefit.benefit_type,
                            description=benefit.description,
                            source_url=benefit.source_url,
                            change_type="update",
                            old_values={
                                "benefit_rate": float(existing.benefit_rate),
                                "benefit_type": existing.benefit_type,
                                "description": existing.description
                            },
                            status="pending"
                        )
                        self.db.add(change)
                        pending_count += 1
                else:
                    # Create new benefit
                    change = PendingEcosystemChange(
                        card_id=card.id,
                        brand_id=brand.id,
                        benefit_rate=benefit.benefit_rate,
                        benefit_type=benefit.benefit_type,
                        description=benefit.description,
                        source_url=benefit.source_url,
                        change_type="new",
                        status="pending"
                    )
                    self.db.add(change)
                    pending_count += 1

            except Exception as e:
                self.logger.error(f"Error processing benefit: {e}")
                continue

        self.db.commit()
        return pending_count

    def _find_existing_pending_brand(self, code: str) -> Optional[PendingBrandChange]:
        """Find existing pending brand by code."""
        return self.db.query(PendingBrandChange).filter(
            and_(
                PendingBrandChange.code == code,
                PendingBrandChange.status == "pending"
            )
        ).first()

    def _find_card(self, card_name: str) -> Optional[Card]:
        """Find a card by name (fuzzy matching)."""
        # Try exact match first
        card = self.db.query(Card).filter(Card.name.ilike(f"%{card_name}%")).first()

        if card:
            return card

        # Try matching with bank prefix
        for bank in ["HDFC", "ICICI", "SBI"]:
            card = self.db.query(Card).filter(Card.name.ilike(f"%{bank}%{card_name}%")).first()
            if card:
                return card

        return None

    def _find_brand(self, brand_name: str) -> Optional[Brand]:
        """Find a brand by name or keyword."""
        # Try exact match on brand name
        brand = self.db.query(Brand).filter(Brand.name.ilike(f"%{brand_name}%")).first()

        if brand:
            return brand

        # Try matching by keyword
        brand = self.db.query(Brand).join(BrandKeyword).filter(
            BrandKeyword.keyword.ilike(f"%{brand_name.lower()}%")
        ).first()

        return brand

    def _find_existing_benefit(self, card_id: UUID, brand_id: UUID) -> Optional[CardEcosystemBenefit]:
        """Find existing ecosystem benefit."""
        return self.db.query(CardEcosystemBenefit).filter(
            and_(
                CardEcosystemBenefit.card_id == card_id,
                CardEcosystemBenefit.brand_id == brand_id
            )
        ).first()

    def _find_existing_pending(self, card_id: UUID, brand_id: UUID) -> Optional[PendingEcosystemChange]:
        """Find existing pending change."""
        return self.db.query(PendingEcosystemChange).filter(
            and_(
                PendingEcosystemChange.card_id == card_id,
                PendingEcosystemChange.brand_id == brand_id,
                PendingEcosystemChange.status == "pending"
            )
        ).first()

    def get_pending_changes(self, status: Optional[str] = None) -> List[PendingEcosystemChange]:
        """Get all pending changes, optionally filtered by status."""
        query = self.db.query(PendingEcosystemChange)

        if status:
            query = query.filter(PendingEcosystemChange.status == status)

        query = query.order_by(PendingEcosystemChange.created_at.desc())

        return query.all()

    def approve_change(self, change_id: UUID, reviewer_id: UUID) -> bool:
        """Approve a pending change and apply it to production."""
        change = self.db.query(PendingEcosystemChange).filter(
            PendingEcosystemChange.id == change_id
        ).first()

        if not change or change.status != "pending":
            return False

        try:
            if change.change_type == "new":
                # Create new ecosystem benefit
                benefit = CardEcosystemBenefit(
                    card_id=change.card_id,
                    brand_id=change.brand_id,
                    benefit_rate=change.benefit_rate,
                    benefit_type=change.benefit_type,
                    description=change.description
                )
                self.db.add(benefit)

            elif change.change_type == "update":
                # Update existing benefit
                benefit = self.db.query(CardEcosystemBenefit).filter(
                    and_(
                        CardEcosystemBenefit.card_id == change.card_id,
                        CardEcosystemBenefit.brand_id == change.brand_id
                    )
                ).first()
                if benefit:
                    benefit.benefit_rate = change.benefit_rate
                    benefit.benefit_type = change.benefit_type
                    benefit.description = change.description

            elif change.change_type == "delete":
                # Delete existing benefit
                benefit = self.db.query(CardEcosystemBenefit).filter(
                    and_(
                        CardEcosystemBenefit.card_id == change.card_id,
                        CardEcosystemBenefit.brand_id == change.brand_id
                    )
                ).first()
                if benefit:
                    self.db.delete(benefit)

            # Update change status
            change.status = "approved"
            change.reviewed_at = datetime.utcnow()
            change.reviewed_by = reviewer_id

            self.db.commit()
            return True

        except Exception as e:
            self.logger.error(f"Error approving change: {e}")
            self.db.rollback()
            return False

    def reject_change(self, change_id: UUID, reviewer_id: UUID) -> bool:
        """Reject a pending change."""
        change = self.db.query(PendingEcosystemChange).filter(
            PendingEcosystemChange.id == change_id
        ).first()

        if not change or change.status != "pending":
            return False

        change.status = "rejected"
        change.reviewed_at = datetime.utcnow()
        change.reviewed_by = reviewer_id

        self.db.commit()
        return True

    def update_pending_change(
        self,
        change_id: UUID,
        benefit_rate: Optional[float] = None,
        benefit_type: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[PendingEcosystemChange]:
        """Update a pending change before approval."""
        change = self.db.query(PendingEcosystemChange).filter(
            PendingEcosystemChange.id == change_id
        ).first()

        if not change or change.status != "pending":
            return None

        if benefit_rate is not None:
            change.benefit_rate = benefit_rate
        if benefit_type is not None:
            change.benefit_type = benefit_type
        if description is not None:
            change.description = description

        self.db.commit()
        self.db.refresh(change)

        return change

    def bulk_approve(self, change_ids: List[UUID], reviewer_id: UUID) -> Dict:
        """Approve multiple changes at once."""
        approved = 0
        failed = 0

        for change_id in change_ids:
            if self.approve_change(change_id, reviewer_id):
                approved += 1
            else:
                failed += 1

        return {"approved": approved, "failed": failed}

    def delete_pending_change(self, change_id: UUID) -> bool:
        """Delete a pending change."""
        change = self.db.query(PendingEcosystemChange).filter(
            PendingEcosystemChange.id == change_id
        ).first()

        if not change:
            return False

        self.db.delete(change)
        self.db.commit()
        return True

    @staticmethod
    def get_status() -> Dict:
        """Get current scraper status."""
        return {
            "is_running": scraper_status.is_running,
            "current_bank": scraper_status.current_bank,
            "last_run": scraper_status.last_run.isoformat() if scraper_status.last_run else None,
            "last_result": scraper_status.last_result,
            "benefits_found": scraper_status.benefits_found,
            "pending_created": scraper_status.pending_created,
            "brands_created": scraper_status.brands_created,
            "errors": scraper_status.errors
        }

    # ============================================
    # PENDING BRAND OPERATIONS
    # ============================================

    def get_pending_brands(self, status: Optional[str] = None) -> List[PendingBrandChange]:
        """Get all pending brand changes, optionally filtered by status."""
        query = self.db.query(PendingBrandChange)

        if status:
            query = query.filter(PendingBrandChange.status == status)

        query = query.order_by(PendingBrandChange.created_at.desc())

        return query.all()

    def approve_brand(self, brand_id: UUID, reviewer_id: UUID) -> Optional[Brand]:
        """Approve a pending brand and create it in the database."""
        pending = self.db.query(PendingBrandChange).filter(
            PendingBrandChange.id == brand_id
        ).first()

        if not pending or pending.status != "pending":
            return None

        try:
            # Create the brand
            brand = Brand(
                name=pending.name,
                code=pending.code,
                description=pending.description,
                is_active=True
            )
            self.db.add(brand)
            self.db.flush()  # Get the brand ID

            # Create keywords
            if pending.keywords:
                for kw in pending.keywords:
                    keyword = BrandKeyword(brand_id=brand.id, keyword=kw.lower())
                    self.db.add(keyword)

            # Update pending status
            pending.status = "approved"
            pending.reviewed_at = datetime.utcnow()
            pending.reviewed_by = reviewer_id

            self.db.commit()
            return brand

        except Exception as e:
            self.logger.error(f"Error approving brand: {e}")
            self.db.rollback()
            return None

    def reject_brand(self, brand_id: UUID, reviewer_id: UUID) -> bool:
        """Reject a pending brand."""
        pending = self.db.query(PendingBrandChange).filter(
            PendingBrandChange.id == brand_id
        ).first()

        if not pending or pending.status != "pending":
            return False

        pending.status = "rejected"
        pending.reviewed_at = datetime.utcnow()
        pending.reviewed_by = reviewer_id

        self.db.commit()
        return True

    def update_pending_brand(
        self,
        brand_id: UUID,
        name: Optional[str] = None,
        code: Optional[str] = None,
        description: Optional[str] = None,
        keywords: Optional[List[str]] = None
    ) -> Optional[PendingBrandChange]:
        """Update a pending brand before approval."""
        pending = self.db.query(PendingBrandChange).filter(
            PendingBrandChange.id == brand_id
        ).first()

        if not pending or pending.status != "pending":
            return None

        if name is not None:
            pending.name = name
        if code is not None:
            pending.code = code
        if description is not None:
            pending.description = description
        if keywords is not None:
            pending.keywords = keywords

        self.db.commit()
        self.db.refresh(pending)

        return pending

    def delete_pending_brand(self, brand_id: UUID) -> bool:
        """Delete a pending brand."""
        pending = self.db.query(PendingBrandChange).filter(
            PendingBrandChange.id == brand_id
        ).first()

        if not pending:
            return False

        self.db.delete(pending)
        self.db.commit()
        return True

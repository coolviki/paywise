import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Date, Boolean, Numeric, ForeignKey, Text
from sqlalchemy.orm import relationship
from ..core.database import Base
from ..core.types import UUID


class Campaign(Base):
    """Time-bound promotional campaigns for cards at specific brands."""
    __tablename__ = "campaigns"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    card_id = Column(UUID, ForeignKey("cards.id", ondelete="CASCADE"), nullable=False)
    brand_id = Column(UUID, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    benefit_rate = Column(Numeric(5, 2), nullable=False)
    benefit_type = Column(String(50), nullable=False)  # cashback, points, discount
    description = Column(Text, nullable=True)
    terms_url = Column(String(500), nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    card = relationship("Card", back_populates="campaigns")
    brand = relationship("Brand", back_populates="campaigns")

    def __repr__(self):
        return f"<Campaign {self.card_id} → {self.brand_id} @ {self.benefit_rate}% ({self.start_date} to {self.end_date})>"

    @property
    def is_currently_active(self) -> bool:
        """Check if campaign is currently active based on dates."""
        today = date.today()
        return self.is_active and self.start_date <= today <= self.end_date


class PendingCampaign(Base):
    """Pending campaign changes awaiting admin approval."""
    __tablename__ = "pending_campaigns"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    card_id = Column(UUID, ForeignKey("cards.id", ondelete="CASCADE"), nullable=False)
    brand_id = Column(UUID, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    benefit_rate = Column(Numeric(5, 2), nullable=False)
    benefit_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    terms_url = Column(String(500), nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    source_url = Column(String(500), nullable=True)
    change_type = Column(String(20), nullable=False)  # 'new', 'update', 'delete'
    existing_campaign_id = Column(UUID, ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(20), nullable=False, default="pending")  # 'pending', 'approved', 'rejected'
    scraped_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(UUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    card = relationship("Card")
    brand = relationship("Brand")
    existing_campaign = relationship("Campaign", foreign_keys=[existing_campaign_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    def __repr__(self):
        return f"<PendingCampaign {self.id} ({self.change_type}, {self.status})>"

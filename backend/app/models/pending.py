import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from ..core.database import Base
from ..core.types import UUID


class PendingEcosystemChange(Base):
    __tablename__ = "pending_ecosystem_changes"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    card_id = Column(UUID, ForeignKey("cards.id", ondelete="CASCADE"), nullable=False)
    brand_id = Column(UUID, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    benefit_rate = Column(Numeric(5, 2), nullable=False)
    benefit_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    source_url = Column(String(500), nullable=True)
    change_type = Column(String(20), nullable=False)  # 'new', 'update', 'delete'
    old_values = Column(JSONB, nullable=True)  # For updates, store previous values
    status = Column(String(20), nullable=False, default="pending")  # 'pending', 'approved', 'rejected'
    scraped_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(UUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    card = relationship("Card")
    brand = relationship("Brand")
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    def __repr__(self):
        return f"<PendingEcosystemChange {self.id} ({self.change_type})>"


class PendingBrandChange(Base):
    __tablename__ = "pending_brand_changes"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    code = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    keywords = Column(JSONB, nullable=True)  # Array of keywords
    source_url = Column(String(500), nullable=True)
    source_bank = Column(String(50), nullable=True)  # hdfc, icici, sbi
    status = Column(String(20), nullable=False, default="pending")  # 'pending', 'approved', 'rejected'
    scraped_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(UUID, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    def __repr__(self):
        return f"<PendingBrandChange {self.name} ({self.status})>"

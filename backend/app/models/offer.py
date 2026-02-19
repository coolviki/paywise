import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Numeric, ForeignKey, Date, Integer, Text, JSON
from sqlalchemy.orm import relationship
from ..core.database import Base
from ..core.types import UUID


class Offer(Base):
    __tablename__ = "offers"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    card_id = Column(UUID, ForeignKey("cards.id"), nullable=True)
    merchant_id = Column(UUID, ForeignKey("merchants.id"), nullable=True)
    category_id = Column(UUID, ForeignKey("categories.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    discount_type = Column(String(50), nullable=False)  # 'percentage', 'flat', 'cashback', 'points'
    discount_value = Column(Numeric(10, 2), nullable=False)
    min_transaction = Column(Numeric(10, 2), nullable=True)
    max_discount = Column(Numeric(10, 2), nullable=True)
    terms = Column(Text, nullable=True)
    valid_from = Column(Date, nullable=True)
    valid_until = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    source_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    card = relationship("Card", back_populates="offers")
    merchant = relationship("Merchant", back_populates="offers")
    category = relationship("Category", back_populates="offers")

    def __repr__(self):
        return f"<Offer {self.title}>"


class OfferFetchLog(Base):
    __tablename__ = "offer_fetch_logs"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    bank_id = Column(UUID, ForeignKey("banks.id"), nullable=True)
    fetch_type = Column(String(50), nullable=True)  # 'scheduled', 'manual'
    status = Column(String(50), nullable=True)  # 'started', 'completed', 'failed'
    offers_count = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    bank = relationship("Bank", back_populates="offer_fetch_logs")

    def __repr__(self):
        return f"<OfferFetchLog {self.status}>"


class LLMPrompt(Base):
    __tablename__ = "llm_prompts"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    template = Column(Text, nullable=False)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<LLMPrompt {self.name}>"


class RecommendationLog(Base):
    __tablename__ = "recommendation_logs"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=True)
    merchant_id = Column(UUID, ForeignKey("merchants.id"), nullable=True)
    location_id = Column(UUID, ForeignKey("merchant_locations.id"), nullable=True)
    recommended_card_id = Column(UUID, ForeignKey("cards.id"), nullable=True)
    all_options = Column(JSON, nullable=True)
    llm_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="recommendation_logs")
    merchant = relationship("Merchant", back_populates="recommendation_logs")
    location = relationship("MerchantLocation", back_populates="recommendation_logs")

    def __repr__(self):
        return f"<RecommendationLog {self.id}>"


class Configuration(Base):
    __tablename__ = "configurations"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Configuration {self.key}>"

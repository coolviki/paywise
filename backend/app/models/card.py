import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Numeric, ForeignKey, Text
from sqlalchemy.orm import relationship
from ..core.database import Base
from ..core.types import UUID


class Bank(Base):
    __tablename__ = "banks"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    logo_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    cards = relationship("Card", back_populates="bank")
    payment_methods = relationship("PaymentMethod", back_populates="bank")
    offer_fetch_logs = relationship("OfferFetchLog", back_populates="bank")

    def __repr__(self):
        return f"<Bank {self.name}>"


class Card(Base):
    __tablename__ = "cards"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    bank_id = Column(UUID, ForeignKey("banks.id"), nullable=False)
    name = Column(String(255), nullable=False)
    card_type = Column(String(50), nullable=False)  # 'credit', 'debit'
    card_network = Column(String(50), nullable=True)  # 'visa', 'mastercard', 'rupay', 'amex'
    annual_fee = Column(Numeric(10, 2), nullable=True)
    reward_type = Column(String(50), nullable=True)  # 'cashback', 'points', 'miles'
    base_reward_rate = Column(Numeric(5, 2), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bank = relationship("Bank", back_populates="cards")
    payment_methods = relationship("PaymentMethod", back_populates="card")
    offers = relationship("Offer", back_populates="card")
    ecosystem_benefits = relationship("CardEcosystemBenefit", back_populates="card")

    def __repr__(self):
        return f"<Card {self.name}>"


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    bank_id = Column(UUID, ForeignKey("banks.id"), nullable=True)
    card_id = Column(UUID, ForeignKey("cards.id"), nullable=True)
    payment_type = Column(String(50), nullable=False)  # 'credit_card', 'debit_card', 'upi', 'wallet'
    last_four_digits = Column(String(4), nullable=True)
    nickname = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="payment_methods")
    bank = relationship("Bank", back_populates="payment_methods")
    card = relationship("Card", back_populates="payment_methods")

    def __repr__(self):
        return f"<PaymentMethod {self.nickname or self.card_id}>"


class CardEcosystemBenefit(Base):
    __tablename__ = "card_ecosystem_benefits"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    card_id = Column(UUID, ForeignKey("cards.id", ondelete="CASCADE"), nullable=False)
    brand_id = Column(UUID, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    benefit_rate = Column(Numeric(5, 2), nullable=False)
    benefit_type = Column(String(50), nullable=False)  # 'neucoins', 'cashback', 'points'
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    card = relationship("Card", back_populates="ecosystem_benefits")
    brand = relationship("Brand", back_populates="ecosystem_benefits")

    def __repr__(self):
        return f"<CardEcosystemBenefit {self.card_id} → {self.brand_id} @ {self.benefit_rate}%>"

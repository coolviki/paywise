import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Numeric, ForeignKey, Text
from sqlalchemy.orm import relationship
from ..core.database import Base
from ..core.types import UUID


class Brand(Base):
    __tablename__ = "brands"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    code = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    keywords = relationship("BrandKeyword", back_populates="brand", cascade="all, delete-orphan")
    ecosystem_benefits = relationship("CardEcosystemBenefit", back_populates="brand")
    campaigns = relationship("Campaign", back_populates="brand")

    def __repr__(self):
        return f"<Brand {self.name}>"


class BrandKeyword(Base):
    __tablename__ = "brand_keywords"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    brand_id = Column(UUID, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    keyword = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    brand = relationship("Brand", back_populates="keywords")

    def __repr__(self):
        return f"<BrandKeyword {self.keyword}>"


class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    icon = Column(String(50), nullable=True)
    parent_id = Column(UUID, ForeignKey("categories.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    merchants = relationship("Merchant", back_populates="category")
    offers = relationship("Offer", back_populates="category")
    children = relationship("Category", backref="parent", remote_side=[id])

    def __repr__(self):
        return f"<Category {self.name}>"


class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    category_id = Column(UUID, ForeignKey("categories.id"), nullable=True)
    logo_url = Column(String, nullable=True)
    google_place_id = Column(String(255), nullable=True)
    is_chain = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category = relationship("Category", back_populates="merchants")
    locations = relationship("MerchantLocation", back_populates="merchant", cascade="all, delete-orphan")
    offers = relationship("Offer", back_populates="merchant")
    recommendation_logs = relationship("RecommendationLog", back_populates="merchant")

    def __repr__(self):
        return f"<Merchant {self.name}>"


class MerchantLocation(Base):
    __tablename__ = "merchant_locations"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID, ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False)
    google_place_id = Column(String(255), nullable=True)
    address = Column(String, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=True)
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    merchant = relationship("Merchant", back_populates="locations")
    recommendation_logs = relationship("RecommendationLog", back_populates="location")

    def __repr__(self):
        return f"<MerchantLocation {self.address}>"

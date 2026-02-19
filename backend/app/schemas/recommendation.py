from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import date
from decimal import Decimal


class SearchQuery(BaseModel):
    query: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    limit: int = 10


class MerchantLocationResult(BaseModel):
    id: UUID
    address: Optional[str] = None
    city: Optional[str] = None
    distance_km: Optional[float] = None
    has_offer: bool = False

    class Config:
        from_attributes = True


class MerchantSearchResult(BaseModel):
    id: UUID
    name: str
    category: Optional[str] = None
    logo_url: Optional[str] = None
    is_chain: bool
    locations: List[MerchantLocationResult] = []
    offer_count: int = 0

    class Config:
        from_attributes = True


class OfferResponse(BaseModel):
    id: UUID
    card_id: Optional[UUID] = None
    card_name: Optional[str] = None
    bank_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    discount_type: str
    discount_value: Decimal
    min_transaction: Optional[Decimal] = None
    max_discount: Optional[Decimal] = None
    valid_until: Optional[date] = None

    class Config:
        from_attributes = True


class RecommendationRequest(BaseModel):
    merchant_id: UUID
    location_id: Optional[UUID] = None
    transaction_amount: Optional[Decimal] = None


class CardRecommendation(BaseModel):
    card_id: UUID
    card_name: str
    bank_name: str
    estimated_savings: str
    reason: str
    offer: Optional[OfferResponse] = None


class RecommendationResponse(BaseModel):
    merchant_id: UUID
    merchant_name: str
    category: Optional[str] = None
    best_option: CardRecommendation
    alternatives: List[CardRecommendation] = []
    ai_insight: Optional[str] = None

    class Config:
        from_attributes = True

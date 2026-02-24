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
    id: str  # Changed to string for Google Places IDs
    address: Optional[str] = None
    city: Optional[str] = None
    distance_km: Optional[float] = None
    has_offer: bool = False

    class Config:
        from_attributes = True


class MerchantSearchResult(BaseModel):
    id: str  # Changed to string for Google Places IDs
    name: str
    category: Optional[str] = None
    logo_url: Optional[str] = None
    is_chain: bool = False
    locations: List[MerchantLocationResult] = []
    offer_count: int = 0

    class Config:
        from_attributes = True


# New simplified request - takes place name instead of merchant_id
class RecommendationRequest(BaseModel):
    place_name: str
    place_id: Optional[str] = None  # Google Places ID
    place_category: Optional[str] = None
    place_address: Optional[str] = None
    transaction_amount: Optional[Decimal] = None


# Simplified card recommendation
class CardRecommendation(BaseModel):
    card_id: UUID
    card_name: str
    bank_name: str
    estimated_savings: str
    reason: str
    offers: List[str] = []  # List of offer descriptions from LLM
    source_url: Optional[str] = None  # Link to bank's T&C page


class RecommendationResponse(BaseModel):
    place_name: str
    place_category: Optional[str] = None
    best_option: CardRecommendation
    alternatives: List[CardRecommendation] = []
    ai_insight: Optional[str] = None

    class Config:
        from_attributes = True

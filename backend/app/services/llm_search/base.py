"""
Base class and types for LLM search providers.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, AsyncIterator
from pydantic import BaseModel
from enum import Enum


class Platform(str, Enum):
    """Supported restaurant/dineout platforms."""
    SWIGGY_DINEOUT = "swiggy_dineout"
    ZOMATO = "zomato"
    EAZYDINER = "eazydiner"
    DINEOUT = "dineout"
    MAGICPIN = "magicpin"
    UNKNOWN = "unknown"


class RestaurantOffer(BaseModel):
    """Structured restaurant offer from a platform."""
    platform: Platform
    platform_display_name: str  # "Swiggy Dineout", "Zomato", etc.
    offer_type: str  # "pre-booked", "walk-in", "bank_offer", "coupon"
    discount_text: str  # "40% off on pre-booked meals"
    discount_percentage: Optional[float] = None
    max_discount: Optional[float] = None
    min_order: Optional[float] = None
    bank_name: Optional[str] = None  # If it's a bank-specific offer
    card_type: Optional[str] = None  # "credit", "debit", etc.
    conditions: Optional[str] = None  # "Valid on weekdays only"
    coupon_code: Optional[str] = None
    valid_days: Optional[str] = None  # "Mon-Thu", "All days"
    source_url: Optional[str] = None

    class Config:
        use_enum_values = True


class SearchResult(BaseModel):
    """Result from LLM search."""
    restaurant_name: str
    city: str
    offers: List[RestaurantOffer]
    summary: Optional[str] = None  # AI-generated summary
    sources: List[str] = []  # URLs used for info
    cached: bool = False
    provider: str = "unknown"


class LLMSearchProvider(ABC):
    """
    Abstract base class for LLM-powered search providers.
    Implement this to add new providers (Perplexity, Tavily, OpenAI, etc.)
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'perplexity', 'tavily')."""
        pass

    @abstractmethod
    async def search_restaurant_offers(
        self,
        restaurant_name: str,
        city: str,
        platforms: Optional[List[Platform]] = None,
    ) -> SearchResult:
        """
        Search for restaurant offers across dineout platforms.

        Args:
            restaurant_name: Name of the restaurant
            city: City where the restaurant is located
            platforms: Optional list of platforms to search (default: all)

        Returns:
            SearchResult with structured offers
        """
        pass

    @abstractmethod
    async def search_restaurant_offers_stream(
        self,
        restaurant_name: str,
        city: str,
        platforms: Optional[List[Platform]] = None,
    ) -> AsyncIterator[RestaurantOffer]:
        """
        Stream restaurant offers as they are found.
        Useful for SSE endpoints.

        Yields:
            RestaurantOffer objects as they are extracted
        """
        pass

    def _build_search_prompt(
        self,
        restaurant_name: str,
        city: str,
        platforms: Optional[List[Platform]] = None,
    ) -> str:
        """Build the search prompt for the LLM."""
        platform_names = []
        if platforms:
            platform_map = {
                Platform.SWIGGY_DINEOUT: "Swiggy Dineout",
                Platform.ZOMATO: "Zomato",
                Platform.EAZYDINER: "EazyDiner",
                Platform.DINEOUT: "Dineout",
                Platform.MAGICPIN: "Magicpin",
            }
            platform_names = [platform_map.get(p, p.value) for p in platforms]
        else:
            platform_names = ["Swiggy Dineout", "Zomato", "EazyDiner", "Dineout", "Magicpin"]

        platforms_str = ", ".join(platform_names)

        return f"""Find current dine-in offers and deals for "{restaurant_name}" in {city} from these platforms: {platforms_str}.

For each platform, extract:
1. Pre-booking discounts (e.g., "40% off on pre-booked meals")
2. Walk-in/Pay via app discounts
3. Bank card offers (HDFC, ICICI, Axis, SBI, etc.)
4. Coupon codes if any
5. Day-specific offers (weekday specials, etc.)

Format each offer clearly with:
- Platform name
- Offer type (pre-booked/walk-in/bank offer/coupon)
- Discount percentage and max cap
- Conditions and validity
- Bank name if it's a card-specific offer

Be specific and factual. Only include currently valid offers."""

    def _parse_offer_text(self, text: str, platform: Platform) -> Optional[RestaurantOffer]:
        """
        Parse raw offer text into a structured RestaurantOffer.
        Override in subclasses for provider-specific parsing.
        """
        import re

        # Extract discount percentage
        discount_match = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
        discount_pct = float(discount_match.group(1)) if discount_match else None

        # Extract max discount
        max_match = re.search(r'(?:max|upto|up to|capped at)[:\s]*₹?\s*(\d+)', text.lower())
        max_discount = float(max_match.group(1)) if max_match else None

        # Detect bank offers
        bank_patterns = {
            'hdfc': 'HDFC',
            'icici': 'ICICI',
            'axis': 'Axis',
            'sbi': 'SBI',
            'kotak': 'Kotak',
            'amex': 'American Express',
            'american express': 'American Express',
            'rbl': 'RBL',
            'idfc': 'IDFC First',
            'yes bank': 'Yes Bank',
        }
        bank_name = None
        for pattern, name in bank_patterns.items():
            if pattern in text.lower():
                bank_name = name
                break

        # Detect offer type
        offer_type = "general"
        if 'pre-book' in text.lower() or 'pre book' in text.lower():
            offer_type = "pre-booked"
        elif 'walk-in' in text.lower() or 'walkin' in text.lower() or 'pay via app' in text.lower():
            offer_type = "walk-in"
        elif bank_name:
            offer_type = "bank_offer"
        elif 'coupon' in text.lower() or 'code' in text.lower():
            offer_type = "coupon"

        # Extract coupon code
        coupon_match = re.search(r'\b([A-Z0-9]{4,15})\b', text)
        coupon_code = None
        if coupon_match and offer_type == "coupon":
            potential_code = coupon_match.group(1)
            # Filter out common non-codes
            if potential_code not in ['HDFC', 'ICICI', 'AXIS', 'SBI']:
                coupon_code = potential_code

        platform_names = {
            Platform.SWIGGY_DINEOUT: "Swiggy Dineout",
            Platform.ZOMATO: "Zomato",
            Platform.EAZYDINER: "EazyDiner",
            Platform.DINEOUT: "Dineout",
            Platform.MAGICPIN: "Magicpin",
            Platform.UNKNOWN: "Unknown",
        }

        return RestaurantOffer(
            platform=platform,
            platform_display_name=platform_names.get(platform, platform.value),
            offer_type=offer_type,
            discount_text=text.strip(),
            discount_percentage=discount_pct,
            max_discount=max_discount,
            bank_name=bank_name,
            coupon_code=coupon_code,
        )

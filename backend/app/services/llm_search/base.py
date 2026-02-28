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
    EAZYDINER = "eazydiner"
    DISTRICT = "district"
    UNKNOWN = "unknown"


# Platform metadata with URLs and display names
PLATFORM_INFO = {
    Platform.SWIGGY_DINEOUT: {
        "display_name": "Swiggy Dineout",
        "website": "https://www.swiggy.com/dineout",
        "app_link": "swiggy://dineout",
        "search_url": "https://www.swiggy.com/dineout/search?query={restaurant}",
    },
    Platform.EAZYDINER: {
        "display_name": "EazyDiner",
        "website": "https://www.eazydiner.com",
        "app_link": "eazydiner://",
        "search_url": "https://www.eazydiner.com/search?q={restaurant}&city={city}",
    },
    Platform.DISTRICT: {
        "display_name": "District",
        "website": "https://www.district.in/dining/",
        "app_link": "district://dining",
        "search_url": "https://www.district.in/dining/{city}?q={restaurant}",
    },
    Platform.UNKNOWN: {
        "display_name": "Unknown",
        "website": None,
        "app_link": None,
        "search_url": None,
    },
}


class RestaurantOffer(BaseModel):
    """Structured restaurant offer from a platform."""
    platform: Platform
    platform_display_name: str  # "Swiggy Dineout", "Zomato Pay", etc.
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
    source_url: Optional[str] = None  # Link to the offer/restaurant on platform
    platform_url: Optional[str] = None  # Deep link to app/website
    app_link: Optional[str] = None  # App deep link

    class Config:
        use_enum_values = True

    @classmethod
    def with_platform_links(
        cls,
        platform: Platform,
        restaurant_name: str,
        city: str,
        **kwargs
    ) -> "RestaurantOffer":
        """Create offer with platform links auto-populated."""
        info = PLATFORM_INFO.get(platform, PLATFORM_INFO[Platform.UNKNOWN])

        # Build search URL
        platform_url = None
        if info.get("search_url"):
            platform_url = info["search_url"].format(
                restaurant=restaurant_name.replace(" ", "+"),
                city=city.lower().replace(" ", "-"),
            )

        return cls(
            platform=platform,
            platform_display_name=info["display_name"],
            platform_url=platform_url,
            app_link=info.get("app_link"),
            **kwargs
        )


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
        parallel: bool = True,
    ) -> SearchResult:
        """
        Search for restaurant offers across dineout platforms.

        Args:
            restaurant_name: Name of the restaurant
            city: City where the restaurant is located
            platforms: Optional list of platforms to search (default: all)
            parallel: If True and multiple platforms, make parallel calls per platform

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
        parallel: bool = True,
    ) -> AsyncIterator[RestaurantOffer]:
        """
        Stream restaurant offers as they are found.
        Useful for SSE endpoints.

        Args:
            parallel: If True and multiple platforms, make parallel calls per platform

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
        # Default to the main 3 platforms
        if platforms:
            platform_names = [PLATFORM_INFO.get(p, {}).get("display_name", p.value) for p in platforms]
        else:
            platform_names = ["Swiggy Dineout", "EazyDiner", "District"]

        platforms_str = ", ".join(platform_names)

        return f"""Find current dine-in payment offers for "{restaurant_name}" in {city} from these payment apps: {platforms_str}.

Look for:
1. **Flat discounts** - e.g., "Flat 20% off up to ₹200"
2. **Pre-booking offers** - discounts for reserving tables in advance
3. **Walk-in/Pay via app** - discounts when paying through the app at restaurant
4. **Bank card offers** - extra discounts with HDFC, ICICI, Axis, SBI, Kotak, Amex cards
5. **Weekday/Weekend specials** - day-specific offers
6. **Promo codes** - any active coupon codes

For each offer found, provide:
- Platform name (Swiggy Dineout / EazyDiner / District)
- Discount amount (percentage and max cap in ₹)
- Conditions (minimum order, valid days, card restrictions)
- Bank name if it's a bank-specific offer

Important: Only include currently active offers. Be specific with numbers (e.g., "30% off up to ₹150" not just "discount available")."""

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
            Platform.ZOMATO_PAY: "Zomato Pay",
            Platform.EAZYDINER: "EazyDiner",
            Platform.DISTRICT: "District",
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

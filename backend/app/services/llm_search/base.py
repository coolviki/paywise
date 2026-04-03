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
        "app_link": "swiggy://dineout/search?query={restaurant}",
        "search_url": "https://www.swiggy.com/dineout/{city_slug}/s?query={restaurant}",
    },
    Platform.EAZYDINER: {
        "display_name": "EazyDiner",
        "website": "https://www.eazydiner.com",
        "app_link": "eazydiner://search?query={restaurant}",
        "search_url": "https://www.eazydiner.com/{city_slug}/s?query={restaurant}",
    },
    Platform.DISTRICT: {
        "display_name": "District",
        "website": "https://www.district.in/dining/",
        "app_link": "district://dining/{city_slug}",
        "search_url": "https://www.district.in/dining/{city_slug}",
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

        # Map city to platform-specific city slugs
        city_slug_map = {
            # Swiggy/EazyDiner city slugs
            "delhi": "delhi-ncr",
            "new delhi": "delhi-ncr",
            "gurgaon": "delhi-ncr",
            "gurugram": "delhi-ncr",
            "noida": "delhi-ncr",
            "cyber hub": "delhi-ncr",
            "dlf cyber city": "delhi-ncr",
            "mumbai": "mumbai",
            "bangalore": "bangalore",
            "bengaluru": "bangalore",
            "hyderabad": "hyderabad",
            "chennai": "chennai",
            "pune": "pune",
            "kolkata": "kolkata",
        }
        city_slug = city_slug_map.get(city.lower().strip(), city.lower().replace(" ", "-"))

        # For District, use different city codes
        if platform == Platform.DISTRICT:
            district_city_map = {
                "delhi": "ncr", "new delhi": "ncr", "gurgaon": "ncr",
                "gurugram": "ncr", "noida": "ncr", "cyber hub": "ncr",
                "mumbai": "mumbai", "bangalore": "bangalore",
                "bengaluru": "bangalore", "hyderabad": "hyderabad",
            }
            city_slug = district_city_map.get(city.lower().strip(), "ncr")

        # URL-encode restaurant name
        import urllib.parse
        restaurant_encoded = urllib.parse.quote(restaurant_name)

        # Build search URL
        platform_url = None
        if info.get("search_url"):
            platform_url = info["search_url"].format(
                restaurant=restaurant_encoded,
                city_slug=city_slug,
            )

        # Build app link
        app_link = None
        if info.get("app_link"):
            app_link = info["app_link"].format(
                restaurant=restaurant_encoded,
                city_slug=city_slug,
            )

        return cls(
            platform=platform,
            platform_display_name=info["display_name"],
            platform_url=platform_url,
            app_link=app_link,
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

        return f"""Find current dine-in offers for "{restaurant_name}" in {city} from: {platforms_str}.

There are TWO types of offers that can be COMBINED/STACKED:

**TYPE 1: RESTAURANT OFFERS** (base discount from the restaurant)
- Pre-booking discount (e.g., "40% off when you pre-book via Swiggy Dineout")
- Walk-in discount (e.g., "10% off on Food & Soft Beverages")
- These are available to ALL customers regardless of payment method

**TYPE 2: BANK/PAYMENT OFFERS** (additional discount with specific bank cards)
- HDFC, ICICI, Axis, SBI, Kotak, IndusInd, RBL, IDFC, Yes Bank, Amex offers
- Example: "25% off up to ₹1000 with IndusInd Bank Credit Card"
- These are ADDITIONAL and can be STACKED with restaurant offers

IMPORTANT RULES:
1. List restaurant offers and bank offers SEPARATELY (not combined)
2. Do NOT include loyalty points (like "EazyPoints", "Dineout Coins") - only actual discounts
3. Do NOT include cashback or rewards - only instant discounts on bill
4. For EazyDiner: "Payeazy" is the payment method, not an offer - look for actual % discounts
5. Be specific with numbers: "25% off up to ₹500" not just "discount available"

For each offer, provide:
- Platform name
- Whether it's a "restaurant" offer or "bank_offer"
- Discount percentage and max cap in ₹
- Bank name (only for bank offers)
- Conditions (min bill, valid days)"""

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
        text_lower = text.lower()
        if 'pre-book' in text_lower or 'pre book' in text_lower:
            offer_type = "pre-booked"
        elif 'walk-in' in text_lower or 'walkin' in text_lower or 'pay via app' in text_lower:
            offer_type = "walk-in"
        elif bank_name:
            offer_type = "bank_offer"
        elif 'coupon' in text_lower or 'code' in text_lower:
            offer_type = "coupon"
        elif 'food' in text_lower or 'beverage' in text_lower or 'restaurant offer' in text_lower:
            # Base restaurant discount (not bank-specific)
            offer_type = "restaurant"

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

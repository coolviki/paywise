"""
Direct scraper for District.in restaurant offers.
Since District offers aren't well-indexed by search engines,
we directly fetch and parse the restaurant page.
"""

import re
import logging
from typing import List, Optional
from urllib.parse import quote
import httpx
from bs4 import BeautifulSoup

from .base import RestaurantOffer, Platform, PLATFORM_INFO

logger = logging.getLogger(__name__)


class DistrictScraper:
    """Scraper for District.in restaurant offers."""

    BASE_URL = "https://www.district.in"
    SEARCH_URL = "https://www.district.in/api/v2/search"

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                }
            )
        return self._client

    async def search_restaurant(self, restaurant_name: str, city: str) -> Optional[str]:
        """
        Search for a restaurant on District and return its page URL.
        """
        client = await self._get_client()

        # Map city names to District's city codes
        city_map = {
            "delhi": "ncr",
            "new delhi": "ncr",
            "ncr": "ncr",
            "gurgaon": "ncr",
            "gurugram": "ncr",
            "noida": "ncr",
            "mumbai": "mumbai",
            "bangalore": "bangalore",
            "bengaluru": "bangalore",
            "hyderabad": "hyderabad",
            "chennai": "chennai",
            "pune": "pune",
            "kolkata": "kolkata",
            "ahmedabad": "ahmedabad",
            "jaipur": "jaipur",
        }

        district_city = city_map.get(city.lower(), city.lower())

        # Try to search via the dining listing page
        try:
            # First, try the dining search page
            search_url = f"{self.BASE_URL}/dining/{district_city}"
            response = await client.get(search_url)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                # Look for restaurant links that match
                restaurant_lower = restaurant_name.lower()
                for link in soup.find_all("a", href=True):
                    href = link.get("href", "")
                    text = link.get_text().lower()

                    # Check if this link points to a restaurant page
                    if "/dining/" in href and district_city in href:
                        # Check if restaurant name matches
                        if self._fuzzy_match(restaurant_lower, text) or self._fuzzy_match(restaurant_lower, href):
                            full_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"
                            return full_url

        except Exception as e:
            logger.warning(f"Error searching District: {e}")

        # Fallback: construct URL based on common patterns
        slug = self._make_slug(restaurant_name)
        guessed_url = f"{self.BASE_URL}/dining/{district_city}/{slug}"

        # Verify the URL exists
        try:
            response = await client.head(guessed_url)
            if response.status_code == 200:
                return guessed_url
        except:
            pass

        return None

    def _fuzzy_match(self, search: str, text: str) -> bool:
        """Check if search term fuzzy matches text."""
        search_words = search.lower().split()
        text_lower = text.lower()

        # Check if most words from search appear in text
        matches = sum(1 for word in search_words if word in text_lower)
        return matches >= len(search_words) * 0.6

    def _make_slug(self, name: str) -> str:
        """Convert restaurant name to URL slug."""
        # Remove special characters, convert to lowercase, replace spaces with hyphens
        slug = re.sub(r'[^\w\s-]', '', name.lower())
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')

    async def get_offers(self, restaurant_name: str, city: str) -> List[RestaurantOffer]:
        """
        Get all offers for a restaurant from District.
        """
        offers = []
        client = await self._get_client()

        # First, find the restaurant page
        restaurant_url = await self.search_restaurant(restaurant_name, city)

        if not restaurant_url:
            # Try direct URL construction with variations
            city_map = {
                "delhi": "ncr",
                "new delhi": "ncr",
                "mumbai": "mumbai",
                "bangalore": "bangalore",
            }
            district_city = city_map.get(city.lower(), city.lower())

            # Try different slug variations
            slugs = [
                self._make_slug(restaurant_name),
                self._make_slug(f"{restaurant_name} {city}"),
                self._make_slug(restaurant_name.replace("'", "")),
            ]

            for slug in slugs:
                test_url = f"{self.BASE_URL}/dining/{district_city}/{slug}"
                try:
                    response = await client.get(test_url)
                    if response.status_code == 200 and "offers" in response.text.lower():
                        restaurant_url = test_url
                        break
                except:
                    continue

        if not restaurant_url:
            logger.info(f"Could not find {restaurant_name} on District")
            return offers

        # Fetch the restaurant page
        try:
            response = await client.get(restaurant_url)
            if response.status_code != 200:
                logger.warning(f"Failed to fetch District page: {response.status_code}")
                return offers

            offers = self._parse_offers(response.text, restaurant_url)

        except Exception as e:
            logger.error(f"Error fetching District offers: {e}")

        return offers

    def _parse_offers(self, html: str, source_url: str) -> List[RestaurantOffer]:
        """Parse offers from District restaurant page HTML."""
        offers = []
        soup = BeautifulSoup(html, "html.parser")

        platform_info = PLATFORM_INFO.get(Platform.DISTRICT, {})

        # Look for offer sections - District typically shows offers in cards/sections
        # Common patterns: "% OFF", "₹ OFF", "Flat", etc.

        # Find all text containing offer patterns
        offer_patterns = [
            r'flat\s*(\d+)%?\s*off',
            r'(\d+)%\s*off',
            r'flat\s*₹?\s*(\d+)\s*off',
            r'₹\s*(\d+)\s*off',
            r'up\s*to\s*₹?\s*(\d+)',
            r'save\s*₹?\s*(\d+)',
        ]

        # Get all text blocks that might contain offers
        text_blocks = soup.find_all(['div', 'span', 'p', 'li', 'h3', 'h4'])

        seen_offers = set()

        for block in text_blocks:
            text = block.get_text(strip=True)
            text_lower = text.lower()

            # Skip if too short or too long
            if len(text) < 10 or len(text) > 500:
                continue

            # Check if this looks like an offer
            if any(keyword in text_lower for keyword in ['off', 'discount', 'cashback', 'save', '₹']):

                # Extract discount percentage
                pct_match = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
                discount_pct = float(pct_match.group(1)) if pct_match else None

                # Extract max discount amount
                max_match = re.search(r'(?:up\s*to|max|upto)\s*₹?\s*(\d+)', text_lower)
                max_discount = float(max_match.group(1)) if max_match else None

                # If no max from "up to", try to find flat amount
                if not max_discount:
                    flat_match = re.search(r'(?:flat\s*)?₹\s*(\d+)\s*off', text_lower)
                    if flat_match:
                        max_discount = float(flat_match.group(1))

                # Detect bank name
                bank_name = self._detect_bank(text)

                # Detect offer type
                offer_type = self._detect_offer_type(text, bank_name)

                # Skip if we've seen this exact offer text
                offer_key = f"{discount_pct}:{max_discount}:{bank_name}"
                if offer_key in seen_offers:
                    continue
                seen_offers.add(offer_key)

                # Only add if we have some discount info
                if discount_pct or max_discount:
                    offers.append(RestaurantOffer(
                        platform=Platform.DISTRICT,
                        platform_display_name="District",
                        offer_type=offer_type,
                        discount_text=text[:200],
                        discount_percentage=discount_pct,
                        max_discount=max_discount,
                        bank_name=bank_name,
                        conditions=self._extract_conditions(text),
                        platform_url=source_url,
                        app_link=platform_info.get("app_link"),
                    ))

        # Deduplicate and sort by discount
        offers = self._dedupe_offers(offers)

        return offers

    def _detect_bank(self, text: str) -> Optional[str]:
        """Detect bank name from offer text."""
        text_lower = text.lower()

        bank_patterns = {
            'hdfc': 'HDFC',
            'icici': 'ICICI',
            'axis': 'Axis',
            'sbi': 'SBI',
            'kotak': 'Kotak',
            'amex': 'American Express',
            'american express': 'American Express',
            'hsbc': 'HSBC',
            'rbl': 'RBL',
            'idfc': 'IDFC First',
            'yes bank': 'Yes Bank',
            'au bank': 'AU Bank',
            'federal': 'Federal Bank',
            'indusind': 'IndusInd',
        }

        for pattern, name in bank_patterns.items():
            if pattern in text_lower:
                return name

        return None

    def _detect_offer_type(self, text: str, bank_name: Optional[str]) -> str:
        """Detect offer type from text."""
        text_lower = text.lower()

        if bank_name:
            return "bank_offer"
        elif 'pre-book' in text_lower or 'prebook' in text_lower or 'booking' in text_lower:
            return "pre-booked"
        elif 'walk-in' in text_lower or 'walkin' in text_lower:
            return "walk-in"
        elif 'coupon' in text_lower or 'code' in text_lower:
            return "coupon"
        else:
            return "general"

    def _extract_conditions(self, text: str) -> Optional[str]:
        """Extract conditions from offer text."""
        text_lower = text.lower()

        conditions = []

        # Min amount
        min_match = re.search(r'min(?:imum)?\s*(?:spend|order|bill)?\s*(?:of\s*)?₹?\s*(\d+)', text_lower)
        if min_match:
            conditions.append(f"Min ₹{min_match.group(1)}")

        # Valid days
        if 'weekday' in text_lower:
            conditions.append("Weekdays only")
        elif 'weekend' in text_lower:
            conditions.append("Weekends only")

        # Card type
        if 'credit' in text_lower and 'debit' not in text_lower:
            conditions.append("Credit cards only")
        elif 'debit' in text_lower and 'credit' not in text_lower:
            conditions.append("Debit cards only")

        return ", ".join(conditions) if conditions else None

    def _dedupe_offers(self, offers: List[RestaurantOffer]) -> List[RestaurantOffer]:
        """Remove duplicate offers, keeping the best one."""
        seen = {}

        for offer in offers:
            # Create a key based on bank and offer type
            key = f"{offer.bank_name or 'general'}:{offer.offer_type}"

            if key not in seen:
                seen[key] = offer
            else:
                # Keep the one with higher discount
                existing = seen[key]
                if (offer.discount_percentage or 0) > (existing.discount_percentage or 0):
                    seen[key] = offer
                elif (offer.max_discount or 0) > (existing.max_discount or 0):
                    seen[key] = offer

        return list(seen.values())

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()


# Singleton instance
_district_scraper: Optional[DistrictScraper] = None


def get_district_scraper() -> DistrictScraper:
    """Get or create District scraper instance."""
    global _district_scraper
    if _district_scraper is None:
        _district_scraper = DistrictScraper()
    return _district_scraper

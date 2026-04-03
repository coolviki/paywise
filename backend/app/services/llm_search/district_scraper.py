"""
Direct scraper for District.in restaurant offers.
Since District offers aren't well-indexed by search engines,
we directly fetch and parse the restaurant page.
"""

import re
import json
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

    def _make_slug(self, name: str, strip_location: bool = False) -> str:
        """Convert restaurant name to URL slug.

        Args:
            name: Restaurant name
            strip_location: If True, remove common location words from the name
        """
        slug = name.lower()

        # Optionally strip location suffixes that users might append to restaurant names
        # Be careful NOT to strip words that might be part of the actual restaurant name
        if strip_location:
            # Only strip these when they appear at the END or are clearly location suffixes
            # Don't strip "delhi" alone as it could be part of names like "Cafe Delhi Heights"
            location_suffixes = [
                # These are safe to strip as they're clearly locations appended to names
                r'\s+cyber\s*hub$', r'\s+cyberhub$', r'\s+dlf\s+cyber\s+city$',
                r'\s+dlf\s+cyber\s+hub$', r'\s+cyber\s+city$',
                r'\s+khan\s+market$', r'\s+connaught\s+place$', r'\s+cp$',
                r'\s+saket$', r'\s+hauz\s+khas$', r'\s+hkv$',
                r'\s+defence\s+colony$', r'\s+greater\s+kailash$', r'\s+gk$',
                r'\s+vasant\s+kunj$', r'\s+aerocity$',
                r'\s+gurgaon$', r'\s+gurugram$', r'\s+noida$',
                r'\s+bandra$', r'\s+andheri$', r'\s+juhu$', r'\s+lower\s+parel$',
                r'\s+worli$', r'\s+colaba$', r'\s+bkc$', r'\s+powai$',
                r'\s+indiranagar$', r'\s+koramangala$', r'\s+whitefield$',
                r'\s+mg\s+road$', r'\s+brigade\s+road$',
                r'\s+sector\s+\d+$',  # Sector 29, Sector 24, etc.
            ]
            for pattern in location_suffixes:
                slug = re.sub(pattern, '', slug, flags=re.IGNORECASE)

        # Remove special characters, convert to lowercase, replace spaces with hyphens
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')

    async def get_offers(self, restaurant_name: str, city: str) -> List[RestaurantOffer]:
        """
        Get all offers for a restaurant from District.
        """
        logger.info(f"[DISTRICT] get_offers called: restaurant='{restaurant_name}', city='{city}'")
        offers = []
        client = await self._get_client()

        # First, find the restaurant page
        restaurant_url = await self.search_restaurant(restaurant_name, city)
        logger.info(f"[DISTRICT] Restaurant URL found: {restaurant_url}")

        if not restaurant_url:
            # Try direct URL construction with variations
            city_map = {
                "delhi": "ncr",
                "new delhi": "ncr",
                "gurgaon": "ncr",
                "gurugram": "ncr",
                "noida": "ncr",
                "cyber hub": "ncr",
                "cyberhub": "ncr",
                "dlf cyber city": "ncr",
                "dlf cyber hub": "ncr",
                "mumbai": "mumbai",
                "bangalore": "bangalore",
                "bengaluru": "bangalore",
                "hyderabad": "hyderabad",
                "chennai": "chennai",
                "pune": "pune",
                "kolkata": "kolkata",
            }
            district_city = city_map.get(city.lower().strip(), "ncr")  # Default to NCR

            # Common location suffixes for each city
            location_suffixes = {
                "ncr": [
                    "dlf-cyber-city", "cyber-hub", "cyberhub", "cyber-city",
                    "khan-market", "connaught-place", "cp", "saket", "select-citywalk",
                    "gurgaon", "gurugram", "delhi", "new-delhi", "noida",
                    "hauz-khas", "defence-colony", "greater-kailash", "gk",
                    "vasant-kunj", "janpath", "nehru-place", "aerocity",
                    "dlf-phase", "sector-29", "mg-road", "sohna-road",
                ],
                "mumbai": [
                    "bandra", "andheri", "juhu", "lower-parel", "worli",
                    "colaba", "fort", "bkc", "powai", "goregaon", "malad",
                ],
                "bangalore": [
                    "indiranagar", "koramangala", "whitefield", "mg-road",
                    "brigade-road", "jp-nagar", "hsr-layout", "electronic-city",
                ],
            }

            # Create slugs - try with location stripped first (handles "Cafe Delhi Heights Cyber Hub")
            base_slug_clean = self._make_slug(restaurant_name, strip_location=True)
            base_slug_raw = self._make_slug(restaurant_name, strip_location=False)
            suffixes = location_suffixes.get(district_city, [])

            # Build list of slugs to try
            slugs = []

            # First priority: clean slug (location stripped) + location suffixes
            slugs.append(base_slug_clean)
            for suffix in suffixes:
                slugs.append(f"{base_slug_clean}-{suffix}")

            # Second priority: raw slug (if different from clean)
            if base_slug_raw != base_slug_clean:
                slugs.append(base_slug_raw)
                for suffix in suffixes:
                    slugs.append(f"{base_slug_raw}-{suffix}")

            # Also try with city name and without apostrophes
            slugs.append(self._make_slug(f"{restaurant_name} {city}"))
            slugs.append(self._make_slug(restaurant_name.replace("'", ""), strip_location=True))

            # Remove duplicates while preserving order
            seen = set()
            unique_slugs = []
            for s in slugs:
                if s not in seen:
                    seen.add(s)
                    unique_slugs.append(s)
            slugs = unique_slugs

            logger.info(f"[DISTRICT] Trying {len(slugs)} URL variations...")

            for slug in slugs:
                test_url = f"{self.BASE_URL}/dining/{district_city}/{slug}"
                try:
                    response = await client.head(test_url, follow_redirects=True)
                    if response.status_code == 200:
                        # Verify it's a real page with content
                        full_response = await client.get(test_url)
                        if full_response.status_code == 200 and len(full_response.text) > 5000:
                            logger.info(f"[DISTRICT] Found working URL: {test_url}")
                            restaurant_url = test_url
                            break
                except:
                    continue

        if not restaurant_url:
            logger.info(f"[DISTRICT] Could not find {restaurant_name} on District - returning empty offers")
            return offers

        # Fetch the restaurant page
        try:
            logger.info(f"[DISTRICT] Fetching page: {restaurant_url}")
            response = await client.get(restaurant_url)
            logger.info(f"[DISTRICT] Response status: {response.status_code}, content length: {len(response.text)} chars")

            if response.status_code != 200:
                logger.warning(f"[DISTRICT] Failed to fetch District page: {response.status_code}")
                return offers

            offers = self._parse_offers(response.text, restaurant_url)
            logger.info(f"[DISTRICT] Parsed {len(offers)} offers from page")
            for i, offer in enumerate(offers):
                logger.info(f"[DISTRICT]   #{i+1}: {offer.offer_type} - {offer.discount_text[:50] if offer.discount_text else 'N/A'}")

        except Exception as e:
            logger.error(f"[DISTRICT] Error fetching District offers: {e}", exc_info=True)

        return offers

    def _parse_offers(self, html: str, source_url: str) -> List[RestaurantOffer]:
        """Parse offers from District restaurant page.

        District is a Next.js app that embeds offer data in escaped JSON format.
        The JSON uses double-escaped quotes like \\" instead of ".
        """
        offers = []
        platform_info = PLATFORM_INFO.get(Platform.DISTRICT, {})

        # Extract city_slug from source_url to build proper app_link
        # URL format: https://www.district.in/dining/{city_slug}/{restaurant-slug}
        city_slug = "ncr"  # Default
        url_match = re.search(r'/dining/([^/]+)/', source_url)
        if url_match:
            city_slug = url_match.group(1)

        # Build app_link with proper city_slug substitution
        app_link = None
        if platform_info.get("app_link"):
            try:
                app_link = platform_info["app_link"].format(city_slug=city_slug)
            except KeyError:
                app_link = platform_info.get("app_link")

        try:
            # Strategy 1: Parse escaped JSON for restaurant offers (allOffers)
            # Pattern matches: \"allOffers\":[{...}],\"bankOffers
            all_offers_pattern = r'\\"allOffers\\":\s*(\[.*?\])\s*,\s*\\"bankOffers'
            all_offers_match = re.search(all_offers_pattern, html)

            if all_offers_match:
                escaped_json = all_offers_match.group(1)
                # Unescape the JSON: \\" -> " and \\n -> space
                unescaped = escaped_json.replace('\\"', '"').replace('\\\\n', ' ').replace('\\n', ' ')

                try:
                    all_offers_data = json.loads(unescaped)
                    logger.info(f"[DISTRICT] Found {len(all_offers_data)} restaurant offers in JSON")

                    for offer_data in all_offers_data:
                        offer_title = offer_data.get("offerTitle", "").strip()
                        title = offer_data.get("title", "")
                        subtitle = offer_data.get("subTitle", "")

                        # Parse "FLAT 10% OFF" style
                        pct_match = re.search(r'(\d+)%', offer_title)
                        discount_pct = float(pct_match.group(1)) if pct_match else None

                        # Clean up the offer text
                        discount_text = f"{offer_title} ({title})" if title else offer_title

                        offers.append(RestaurantOffer(
                            platform=Platform.DISTRICT,
                            platform_display_name="District",
                            offer_type="restaurant",
                            discount_text=discount_text,
                            discount_percentage=discount_pct,
                            conditions=subtitle if subtitle else None,
                            platform_url=source_url,
                            app_link=app_link,
                        ))
                except json.JSONDecodeError as e:
                    logger.warning(f"[DISTRICT] Failed to parse allOffers JSON: {e}")

            # Strategy 2: Parse bank offers from escaped JSON
            # Pattern matches: \"title\":\"15% OFF up to ₹1500 on Amex...\"
            bank_offer_pattern = r'\\"title\\":\\"((?:Flat|[0-9]+%)[^\\]*(?:OFF|off)[^\\]*)\\"'
            bank_matches = re.findall(bank_offer_pattern, html, re.IGNORECASE)

            logger.info(f"[DISTRICT] Found {len(bank_matches)} potential bank offer matches")

            seen_bank_offers = set()
            for offer_text in bank_matches:
                # Decode unicode escapes (₹ is \u20b9)
                try:
                    offer_text = offer_text.encode('utf-8').decode('unicode_escape')
                except:
                    pass

                # Skip if we've seen this exact text
                if offer_text in seen_bank_offers:
                    continue
                seen_bank_offers.add(offer_text)

                # Detect bank/card name
                bank_name = self._detect_bank(offer_text)

                # Skip generic offers without bank name (like "Flat ₹50 OFF using MobiKwik")
                if not bank_name and 'mobikwik' not in offer_text.lower():
                    # Check if it's a credit/debit card offer
                    if 'credit' not in offer_text.lower() and 'debit' not in offer_text.lower():
                        continue

                # Parse discount percentage
                pct_match = re.search(r'(\d+)%', offer_text)
                discount_pct = float(pct_match.group(1)) if pct_match else None

                # Parse max discount (flat amount or "up to" amount)
                flat_match = re.search(r'₹\s*(\d+)', offer_text)
                max_discount = float(flat_match.group(1)) if flat_match else None

                upto_match = re.search(r'up\s*to\s*₹?\s*(\d+)', offer_text, re.IGNORECASE)
                if upto_match:
                    max_discount = float(upto_match.group(1))

                logger.info(f"[DISTRICT] Bank offer: {offer_text[:60]}... (bank={bank_name})")

                offers.append(RestaurantOffer(
                    platform=Platform.DISTRICT,
                    platform_display_name="District",
                    offer_type="bank_offer",
                    discount_text=offer_text,
                    discount_percentage=discount_pct,
                    max_discount=max_discount,
                    bank_name=bank_name if bank_name else "Credit/Debit Card",
                    platform_url=source_url,
                    app_link=app_link,
                ))

        except Exception as e:
            logger.error(f"[DISTRICT] Error parsing JSON offers: {e}", exc_info=True)

        # Strategy 2: Fallback to HTML parsing if no JSON offers found
        if not offers:
            logger.info("[DISTRICT] No JSON offers found, falling back to HTML parsing")
            offers = self._parse_offers_html(html, source_url, app_link)

        return offers

    def _parse_offers_html(self, html: str, source_url: str, app_link: Optional[str] = None) -> List[RestaurantOffer]:
        """Fallback HTML parsing for offers."""
        offers = []
        soup = BeautifulSoup(html, "html.parser")

        text_blocks = soup.find_all(['div', 'span', 'p', 'li', 'h3', 'h4'])
        seen_offers = set()

        for block in text_blocks:
            text = block.get_text(strip=True)
            text_lower = text.lower()

            if len(text) < 10 or len(text) > 500:
                continue

            if any(keyword in text_lower for keyword in ['off', 'discount', 'cashback', 'save', '₹']):
                pct_match = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
                discount_pct = float(pct_match.group(1)) if pct_match else None

                max_match = re.search(r'(?:up\s*to|max|upto)\s*₹?\s*(\d+)', text_lower)
                max_discount = float(max_match.group(1)) if max_match else None

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
                        app_link=app_link,
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
            'pnb': 'PNB',
            'punjab national': 'PNB',
            'bob': 'Bank of Baroda',
            'bank of baroda': 'Bank of Baroda',
            'canara': 'Canara Bank',
            'union bank': 'Union Bank',
            'indian bank': 'Indian Bank',
            'citi': 'Citi',
            'citibank': 'Citi',
            'standard chartered': 'Standard Chartered',
            'sc bank': 'Standard Chartered',
            'dbs': 'DBS',
            'taj': 'Taj (IHCL)',
            'tide': 'Tide',
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

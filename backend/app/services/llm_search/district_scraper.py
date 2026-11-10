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
from .restaurant_match import LOCATION_ABBREVIATIONS, name_matches, page_restaurant_name, score_candidate, split_query, tokens as tokens_in_order

logger = logging.getLogger(__name__)


CITY_WORDS = {"new", "delhi", "ncr", "india", "gurgaon", "gurugram", "noida", "mumbai", "bangalore",
              "bengaluru", "hyderabad", "chennai", "pune", "kolkata", "ahmedabad", "jaipur", "chandigarh"}


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

    # District city codes. Localities map to their metro so "Connaught Place" / "CP" work as a city.
    CITY_CODES = {
        "delhi": "ncr", "new delhi": "ncr", "ncr": "ncr", "delhi ncr": "ncr", "gurgaon": "ncr",
        "gurugram": "ncr", "noida": "ncr", "greater noida": "ncr", "faridabad": "ncr",
        "mumbai": "mumbai", "bombay": "mumbai", "bangalore": "bangalore", "bengaluru": "bangalore",
        "hyderabad": "hyderabad", "chennai": "chennai", "pune": "pune", "kolkata": "kolkata",
        "ahmedabad": "ahmedabad", "jaipur": "jaipur", "chandigarh": "chandigarh",
    }
    LOCALITY_CITY = {
        "connaught": "ncr", "janpath": "ncr", "khan": "ncr", "hauz": "ncr", "saket": "ncr",
        "aerocity": "ncr", "cyber": "ncr", "cyberhub": "ncr", "defence": "ncr", "kailash": "ncr",
        "vasant": "ncr", "chanakyapuri": "ncr", "sector": "ncr", "dlf": "ncr",
        "bandra": "mumbai", "andheri": "mumbai", "juhu": "mumbai", "worli": "mumbai", "parel": "mumbai",
        "colaba": "mumbai", "powai": "mumbai", "bkc": "mumbai",
        "indiranagar": "bangalore", "koramangala": "bangalore", "whitefield": "bangalore",
    }
    MAX_GUESSES = 12

    def _city_code(self, city: str, loc_tokens) -> str:
        c = re.sub(r"\s+", " ", (city or "").lower().split(",")[-1]).strip()
        if c in self.CITY_CODES:
            return self.CITY_CODES[c]
        for part in (city or "").lower().split(","):
            if part.strip() in self.CITY_CODES:
                return self.CITY_CODES[part.strip()]
        for w in loc_tokens:
            if w in self.CITY_CODES:
                return self.CITY_CODES[w]
            if w in self.LOCALITY_CITY:
                return self.LOCALITY_CITY[w]
        return "ncr"

    async def _fetch(self, url: str) -> Optional[httpx.Response]:
        client = await self._get_client()
        try:
            resp = await client.get(url)
            return resp if resp.status_code == 200 else None
        except Exception as e:
            logger.info(f"[DISTRICT] fetch failed {url}: {type(e).__name__}")
            return None

    async def _listing_candidates(self, city_code: str, name_tokens, loc_tokens) -> List[str]:
        """Restaurant links on District's listing pages whose NAME matches, best first."""
        scored = {}
        for listing in (f"{self.BASE_URL}/dining/{city_code}", f"{self.BASE_URL}/dining/{city_code}/restaurants"):
            resp = await self._fetch(listing)
            if not resp:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if f"/dining/{city_code}/" not in href or href.rstrip("/").endswith("/restaurants"):
                    continue
                url = href if href.startswith("http") else f"{self.BASE_URL}{href}"
                # Score on the link's NAME text only (District link text is just the name);
                # area words in the URL never make a match on their own.
                text = link.get_text(" ", strip=True)
                score = score_candidate(name_tokens, loc_tokens, text, url) if text else None
                if score is not None and score > scored.get(url, float("-inf")):
                    scored[url] = score
        ranked = sorted(scored, key=lambda u: scored[u], reverse=True)
        logger.info(f"[DISTRICT] Listing candidates: {ranked[:5]}")
        return ranked

    def _guessed_urls(self, restaurant_name: str, city_code: str, name_tokens, loc_tokens) -> List[str]:
        """District slugs look like {name}-{area}-{city}, e.g. drama-connaught-place-new-delhi."""
        name_slug = "-".join(name_tokens)
        raw_slug = self._make_slug(restaurant_name)
        # Area words in the order the user wrote them, with abbreviations expanded (cp -> connaught place)
        area_words = " ".join(LOCATION_ABBREVIATIONS.get(w, w) for w in tokens_in_order(restaurant_name)).split()
        area_words = [w for w in area_words if w in loc_tokens and w not in CITY_WORDS]
        loc_slug = "-".join(dict.fromkeys(area_words))
        city_suffix = {"ncr": ["new-delhi", "gurgaon", "noida", "delhi"]}.get(city_code, [city_code])
        slugs = [raw_slug, name_slug]
        if loc_slug:
            slugs += [f"{name_slug}-{loc_slug}-{c}" for c in city_suffix] + [f"{name_slug}-{loc_slug}"]
            slugs += [f"{name_slug}-1-{loc_slug}-{c}" for c in city_suffix[:1]]
        seen, out = set(), []
        for sl in slugs:
            sl = sl.strip("-")
            if sl and sl not in seen:
                seen.add(sl)
                out.append(f"{self.BASE_URL}/dining/{city_code}/{sl}")
        return out[: self.MAX_GUESSES]

    async def find_restaurant_page(self, restaurant_name: str, city: str) -> Optional[tuple]:
        """Return (url, html, page_name) for the page that IS this restaurant, or None.

        Every candidate is fetched and its title checked against the requested name;
        a page for a different restaurant is rejected instead of returned.
        """
        name_tokens, loc_tokens = split_query(restaurant_name, city)
        city_code = self._city_code(city, loc_tokens)
        logger.info(f"[DISTRICT] Lookup name={name_tokens} location={sorted(loc_tokens)} city_code={city_code}")

        candidates = await self._listing_candidates(city_code, name_tokens, loc_tokens)
        candidates += [u for u in self._guessed_urls(restaurant_name, city_code, name_tokens, loc_tokens)
                       if u not in candidates]

        for url in candidates:
            resp = await self._fetch(url)
            if not resp or len(resp.text) < 2000:
                continue
            page_name = page_restaurant_name(resp.text)
            final_url = str(resp.url)
            if name_matches(name_tokens, page_name):
                logger.info(f"[DISTRICT] Verified page '{page_name}' at {final_url}")
                return final_url, resp.text, page_name
            logger.warning(f"[DISTRICT] Rejected {final_url}: page is '{page_name}', not '{restaurant_name}'")
        logger.info(f"[DISTRICT] No verified District page for '{restaurant_name}' ({city})")
        return None

    def _make_slug(self, name: str) -> str:
        slug = re.sub(r"[^\w\s-]", "", name.lower())
        slug = re.sub(r"[\s_]+", "-", slug)
        return re.sub(r"-+", "-", slug).strip("-")

    async def get_offers(self, restaurant_name: str, city: str) -> List[RestaurantOffer]:
        """Get all offers for a restaurant from District (only from its verified page)."""
        logger.info(f"[DISTRICT] get_offers called: restaurant='{restaurant_name}', city='{city}'")
        found = await self.find_restaurant_page(restaurant_name, city)
        if not found:
            return []
        url, html, page_name = found
        try:
            offers = self._parse_offers(html, url)
        except Exception as e:
            logger.error(f"[DISTRICT] Error parsing District offers: {e}", exc_info=True)
            return []
        for o in offers:
            o.matched_restaurant = page_name
        logger.info(f"[DISTRICT] Parsed {len(offers)} offers for '{page_name}'")
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

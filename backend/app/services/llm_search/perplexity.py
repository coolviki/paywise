"""
Perplexity API provider for LLM search.
Uses Perplexity's sonar model which has built-in web search.
"""

import json
import re
import asyncio
import logging
from typing import List, Optional, AsyncIterator
import httpx

from .base import LLMSearchProvider, RestaurantOffer, SearchResult, Platform, PLATFORM_INFO
from .district_scraper import get_district_scraper

logger = logging.getLogger(__name__)


class PerplexityProvider(LLMSearchProvider):
    """
    Perplexity API provider.
    Docs: https://docs.perplexity.ai/
    """

    BASE_URL = "https://api.perplexity.ai"

    def __init__(self, api_key: str, model: str = "sonar"):
        self.api_key = api_key
        self.model = model
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def provider_name(self) -> str:
        return "perplexity"

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=60.0,
            )
        return self._client

    async def search_restaurant_offers(
        self,
        restaurant_name: str,
        city: str,
        platforms: Optional[List[Platform]] = None,
        parallel: bool = True,
    ) -> SearchResult:
        """Search for restaurant offers using Perplexity."""
        # If multiple platforms and parallel mode, make parallel calls for each platform
        if parallel and platforms and len(platforms) > 1:
            return await self._search_parallel(restaurant_name, city, platforms)

        # Single platform, all platforms, or non-parallel mode - single call
        return await self._search_single_platform(restaurant_name, city, platforms)

    async def _search_single_platform(
        self,
        restaurant_name: str,
        city: str,
        platforms: Optional[List[Platform]] = None,
    ) -> SearchResult:
        """Search for offers on a single platform."""
        offers = []
        sources = []

        # If searching specifically for District, use direct scraper
        if platforms and len(platforms) == 1 and platforms[0] == Platform.DISTRICT:
            logger.info(f"Using District scraper for {restaurant_name} in {city}")
            district_offers = await self._get_district_offers(restaurant_name, city)
            return SearchResult(
                restaurant_name=restaurant_name,
                city=city,
                offers=district_offers,
                summary=f"Found {len(district_offers)} offers on District" if district_offers else None,
                sources=["district.in"],
                provider=self.provider_name,
            )

        # Use Perplexity for non-District platforms
        client = await self._get_client()

        # Build prompt excluding District (we'll fetch that separately)
        non_district_platforms = None
        if platforms:
            non_district_platforms = [p for p in platforms if p != Platform.DISTRICT]

        if non_district_platforms or platforms is None:
            prompt = self._build_search_prompt(restaurant_name, city, non_district_platforms if non_district_platforms else None)

            system_prompt = """You are a helpful assistant that finds restaurant dine-in offers.
Return your response in the following JSON format:
{
    "offers": [
        {
            "platform": "swiggy_dineout|eazydiner|district",
            "offer_type": "pre-booked|walk-in|bank_offer|coupon|general",
            "discount_text": "Full description of the offer",
            "discount_percentage": 40.0,
            "max_discount": 500,
            "bank_name": "HDFC" or null,
            "conditions": "Valid on weekdays" or null,
            "coupon_code": "CODE123" or null
        }
    ],
    "summary": "Brief summary of best deals available"
}

Platform mapping:
- Swiggy Dineout, Dineout → "swiggy_dineout"
- EazyDiner → "eazydiner"
- District → "district"

IMPORTANT: List ALL offers found, including all bank-specific offers separately."""

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "return_citations": True,
            }

            response = await client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"]
            sources = data.get("citations", [])

            offers = self._parse_response(content, restaurant_name)

        # If District is in the platforms list (or no filter), also fetch from District scraper
        if platforms is None or Platform.DISTRICT in platforms:
            logger.info(f"Also fetching District offers for {restaurant_name} in {city}")
            district_offers = await self._get_district_offers(restaurant_name, city)
            offers.extend(district_offers)
            if district_offers:
                sources.append("district.in")

        # Filter offers by platform if specified
        if platforms:
            offers = [o for o in offers if o.platform in platforms]

        # Build summary
        summary = None
        if 'content' in locals() and content:
            summary = self._extract_summary(content)

        return SearchResult(
            restaurant_name=restaurant_name,
            city=city,
            offers=offers,
            summary=summary,
            sources=sources,
            provider=self.provider_name,
        )

    async def _get_district_offers(self, restaurant_name: str, city: str) -> List[RestaurantOffer]:
        """Get offers from District using direct scraper."""
        try:
            scraper = get_district_scraper()
            return await scraper.get_offers(restaurant_name, city)
        except Exception as e:
            logger.error(f"Error fetching District offers: {e}")
            return []

    async def _search_parallel(
        self,
        restaurant_name: str,
        city: str,
        platforms: List[Platform],
    ) -> SearchResult:
        """Search multiple platforms in parallel and merge results."""
        # Create tasks for each platform
        tasks = [
            self._search_single_platform(restaurant_name, city, [platform])
            for platform in platforms
        ]

        # Run all searches in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge results
        all_offers = []
        all_sources = []
        summaries = []

        for result in results:
            if isinstance(result, Exception):
                # Log error but continue with other results
                continue
            all_offers.extend(result.offers)
            all_sources.extend(result.sources)
            if result.summary:
                summaries.append(result.summary)

        # Dedupe sources
        unique_sources = list(set(all_sources))

        return SearchResult(
            restaurant_name=restaurant_name,
            city=city,
            offers=all_offers,
            summary=" | ".join(summaries) if summaries else None,
            sources=unique_sources,
            provider=self.provider_name,
        )

    async def search_restaurant_offers_stream(
        self,
        restaurant_name: str,
        city: str,
        platforms: Optional[List[Platform]] = None,
        parallel: bool = True,
    ) -> AsyncIterator[RestaurantOffer]:
        """Stream offers as they are found."""
        # If multiple platforms and parallel mode, use parallel calls and yield results
        if parallel and platforms and len(platforms) > 1:
            async for offer in self._stream_parallel(restaurant_name, city, platforms):
                yield offer
            return

        # Single platform or non-parallel mode - use actual streaming
        async for offer in self._stream_single_platform(restaurant_name, city, platforms):
            yield offer

    async def _stream_parallel(
        self,
        restaurant_name: str,
        city: str,
        platforms: List[Platform],
    ) -> AsyncIterator[RestaurantOffer]:
        """Make parallel calls for each platform and yield all offers."""
        # Use the parallel search method
        result = await self._search_parallel(restaurant_name, city, platforms)

        # Yield offers one by one
        for offer in result.offers:
            yield offer

    async def _stream_single_platform(
        self,
        restaurant_name: str,
        city: str,
        platforms: Optional[List[Platform]] = None,
    ) -> AsyncIterator[RestaurantOffer]:
        """Stream offers from a single platform."""
        client = await self._get_client()

        prompt = self._build_search_prompt(restaurant_name, city, platforms)

        system_prompt = """You are a helpful assistant that finds restaurant dine-in offers.
For each offer you find, output it on a separate line in this format:
OFFER: [Platform] | [Offer Type] | [Discount] | [Bank if any] | [Conditions]

Use EXACTLY these platform names:
- "Swiggy Dineout" for Swiggy Dineout / Dineout offers
- "EazyDiner" for EazyDiner offers
- "District" for District offers

Example:
OFFER: Swiggy Dineout | bank_offer | 10% off up to Rs 500 | HDFC Infinia | Min Rs 3500
OFFER: Swiggy Dineout | bank_offer | 10% off up to Rs 400 | HDFC Diners | Min Rs 3000
OFFER: EazyDiner | walk-in | 25% off on bill | - | Pay via EazyDiner
OFFER: District | pre-booked | 20% off | - | Book via District app

After all offers, add:
SUMMARY: Brief summary

List ALL offers including all bank-specific offers separately."""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "stream": True,
        }

        async with client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            buffer = ""

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    json_str = line[6:]
                    if json_str.strip() == "[DONE]":
                        break

                    try:
                        chunk = json.loads(json_str)
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        buffer += content

                        # Check for complete offer lines
                        while "\n" in buffer:
                            line_content, buffer = buffer.split("\n", 1)
                            offer = self._parse_offer_line(line_content)
                            if offer:
                                # Filter by user's selected platforms
                                if platforms is None or offer.platform in platforms:
                                    yield offer
                    except json.JSONDecodeError:
                        continue

            # Process remaining buffer
            if buffer.strip():
                offer = self._parse_offer_line(buffer)
                if offer:
                    if platforms is None or offer.platform in platforms:
                        yield offer

    def _parse_response(self, content: str, restaurant_name: str) -> List[RestaurantOffer]:
        """Parse JSON response into RestaurantOffer objects."""
        offers = []

        # Try to extract JSON
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                data = json.loads(json_match.group())
                for item in data.get("offers", []):
                    platform = self._map_platform(item.get("platform", "unknown"))
                    platform_info = PLATFORM_INFO.get(platform, {})
                    offers.append(RestaurantOffer(
                        platform=platform,
                        platform_display_name=self._get_platform_display_name(platform),
                        offer_type=item.get("offer_type", "general"),
                        discount_text=item.get("discount_text", ""),
                        discount_percentage=item.get("discount_percentage"),
                        max_discount=item.get("max_discount"),
                        bank_name=item.get("bank_name"),
                        conditions=item.get("conditions"),
                        coupon_code=item.get("coupon_code"),
                        app_link=platform_info.get("app_link"),
                        platform_url=platform_info.get("website"),
                    ))
            except json.JSONDecodeError:
                # Fall back to text parsing
                offers = self._parse_text_response(content)

        return offers

    def _parse_text_response(self, content: str) -> List[RestaurantOffer]:
        """Parse unstructured text response."""
        offers = []
        lines = content.split("\n")

        for line in lines:
            if "%" in line and any(p in line.lower() for p in ["swiggy", "eazydiner", "dineout", "district"]):
                platform = self._detect_platform(line)
                offer = self._parse_offer_text(line, platform)
                if offer:
                    offers.append(offer)

        return offers

    def _parse_offer_line(self, line: str) -> Optional[RestaurantOffer]:
        """Parse a single OFFER: formatted line."""
        if not line.strip().startswith("OFFER:"):
            return None

        parts = line.replace("OFFER:", "").split("|")
        if len(parts) < 3:
            return None

        platform_str = parts[0].strip().lower()
        platform = self._map_platform(platform_str)
        offer_type = parts[1].strip() if len(parts) > 1 else "general"
        discount_text = parts[2].strip() if len(parts) > 2 else ""
        bank_name = parts[3].strip() if len(parts) > 3 and parts[3].strip() != "-" else None
        conditions = parts[4].strip() if len(parts) > 4 and parts[4].strip() != "-" else None

        # Extract percentage
        pct_match = re.search(r'(\d+(?:\.\d+)?)\s*%', discount_text)
        discount_pct = float(pct_match.group(1)) if pct_match else None

        # Extract max discount
        max_match = re.search(r'(?:up to|upto|max)[:\s]*(?:Rs\.?|₹)?\s*(\d+)', discount_text.lower())
        max_discount = float(max_match.group(1)) if max_match else None

        platform_info = PLATFORM_INFO.get(platform, {})
        return RestaurantOffer(
            platform=platform,
            platform_display_name=self._get_platform_display_name(platform),
            offer_type=offer_type,
            discount_text=discount_text,
            discount_percentage=discount_pct,
            max_discount=max_discount,
            bank_name=bank_name,
            conditions=conditions,
            app_link=platform_info.get("app_link"),
            platform_url=platform_info.get("website"),
        )

    def _detect_platform(self, text: str) -> Platform:
        """Detect platform from text."""
        text_lower = text.lower()
        if "swiggy" in text_lower or "dineout" in text_lower:
            return Platform.SWIGGY_DINEOUT
        elif "eazydiner" in text_lower or "eazy diner" in text_lower:
            return Platform.EAZYDINER
        elif "district" in text_lower:
            return Platform.DISTRICT
        return Platform.UNKNOWN

    def _map_platform(self, platform_str: str) -> Platform:
        """Map string to Platform enum."""
        # Normalize: lowercase, remove extra spaces, replace hyphens with spaces
        normalized = platform_str.lower().strip()
        normalized = " ".join(normalized.split())  # Collapse multiple spaces
        normalized_no_hyphen = normalized.replace("-", " ")

        mapping = {
            # Swiggy Dineout variations
            "swiggy_dineout": Platform.SWIGGY_DINEOUT,
            "swiggy dineout": Platform.SWIGGY_DINEOUT,
            "swiggy dine out": Platform.SWIGGY_DINEOUT,
            "swiggy": Platform.SWIGGY_DINEOUT,
            "dineout": Platform.SWIGGY_DINEOUT,
            "dine out": Platform.SWIGGY_DINEOUT,
            "dine-out": Platform.SWIGGY_DINEOUT,
            # EazyDiner variations
            "eazydiner": Platform.EAZYDINER,
            "eazy diner": Platform.EAZYDINER,
            "eazy_diner": Platform.EAZYDINER,
            "easy diner": Platform.EAZYDINER,
            "easydiner": Platform.EAZYDINER,
            # District variations
            "district": Platform.DISTRICT,
            "district app": Platform.DISTRICT,
        }

        # Try exact match first
        if normalized in mapping:
            return mapping[normalized]

        # Try with hyphens replaced by spaces
        if normalized_no_hyphen in mapping:
            return mapping[normalized_no_hyphen]

        # Fallback to unknown
        return Platform.UNKNOWN

    def _get_platform_display_name(self, platform: Platform) -> str:
        """Get display name for platform."""
        from .base import PLATFORM_INFO
        return PLATFORM_INFO.get(platform, {}).get("display_name", "Unknown")

    def _extract_summary(self, content: str) -> Optional[str]:
        """Extract summary from response."""
        # Try JSON first
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return data.get("summary")
            except json.JSONDecodeError:
                pass

        # Try SUMMARY: format
        summary_match = re.search(r'SUMMARY:\s*(.+)', content)
        if summary_match:
            return summary_match.group(1).strip()

        return None

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()

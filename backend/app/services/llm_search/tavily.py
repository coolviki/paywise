"""
Tavily API provider for LLM search.
Tavily is a search API optimized for LLMs - we combine it with Gemini for extraction.
"""

import json
import re
import asyncio
from typing import List, Optional, AsyncIterator
import httpx

from .base import LLMSearchProvider, RestaurantOffer, SearchResult, Platform, PLATFORM_INFO


class TavilyProvider(LLMSearchProvider):
    """
    Tavily Search API + Gemini for extraction.
    Docs: https://docs.tavily.com/
    """

    TAVILY_URL = "https://api.tavily.com"
    GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, tavily_api_key: str, gemini_api_key: str, gemini_model: str = "gemini-2.0-flash"):
        self.tavily_api_key = tavily_api_key
        self.gemini_api_key = gemini_api_key
        self.gemini_model = gemini_model
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def provider_name(self) -> str:
        return "tavily"

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client

    async def _tavily_search(self, query: str) -> dict:
        """Perform Tavily search."""
        client = await self._get_client()

        payload = {
            "api_key": self.tavily_api_key,
            "query": query,
            "search_depth": "advanced",
            "include_answer": True,
            "include_raw_content": False,
            "max_results": 10,
            "include_domains": [
                "swiggy.com",
                "eazydiner.com",
                "dineout.co.in",
                "district.in",
                "thedistrict.in",
                "magicpin.in",
            ],
        }

        response = await client.post(f"{self.TAVILY_URL}/search", json=payload)
        response.raise_for_status()
        return response.json()

    async def _gemini_extract(self, search_results: dict, restaurant_name: str, city: str) -> dict:
        """Use Gemini to extract structured offers from search results."""
        client = await self._get_client()

        # Build context from search results
        context_parts = []
        if search_results.get("answer"):
            context_parts.append(f"Summary: {search_results['answer']}")

        for result in search_results.get("results", []):
            context_parts.append(f"Source: {result['url']}\nContent: {result['content']}\n")

        context = "\n\n".join(context_parts)

        prompt = f"""Based on the following search results about restaurant offers for "{restaurant_name}" in {city}, extract all dine-in offers in JSON format.

Search Results:
{context}

Return JSON in this exact format:
{{
    "offers": [
        {{
            "platform": "swiggy_dineout|eazydiner|district",
            "offer_type": "pre-booked|walk-in|bank_offer|coupon|general",
            "discount_text": "Full description of the offer",
            "discount_percentage": 40.0,
            "max_discount": 500,
            "bank_name": "HDFC" or null,
            "conditions": "Valid on weekdays" or null,
            "coupon_code": "CODE123" or null
        }}
    ],
    "summary": "Brief summary of best deals available"
}}

Platform mapping:
- Swiggy Dineout, Dineout → "swiggy_dineout"
- EazyDiner → "eazydiner"
- District → "district"

Only include currently valid offers. Return empty offers array if no valid offers found."""

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "topP": 0.8,
                "maxOutputTokens": 2048,
            },
        }

        url = f"{self.GEMINI_URL}/models/{self.gemini_model}:generateContent?key={self.gemini_api_key}"
        response = await client.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        content = data["candidates"][0]["content"]["parts"][0]["text"]

        # Parse JSON from response
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return {"offers": [], "summary": None}

    async def search_restaurant_offers(
        self,
        restaurant_name: str,
        city: str,
        platforms: Optional[List[Platform]] = None,
        parallel: bool = True,
    ) -> SearchResult:
        """Search for restaurant offers using Tavily + Gemini."""
        # If multiple platforms and parallel mode, make parallel calls for each platform
        if parallel and platforms and len(platforms) > 1:
            return await self._search_parallel(restaurant_name, city, platforms)

        return await self._search_single_platform(restaurant_name, city, platforms)

    async def _search_single_platform(
        self,
        restaurant_name: str,
        city: str,
        platforms: Optional[List[Platform]] = None,
    ) -> SearchResult:
        """Search for offers on a single platform."""
        # Build search query
        platform_names = ["Swiggy Dineout", "EazyDiner", "District"]
        if platforms:
            platform_map = {
                Platform.SWIGGY_DINEOUT: "Swiggy Dineout",
                Platform.EAZYDINER: "EazyDiner",
                Platform.DISTRICT: "District",
            }
            platform_names = [platform_map.get(p, p.value) for p in platforms]

        query = f"{restaurant_name} {city} dine-in offers discounts {' '.join(platform_names)} bank card offers 2024"

        # Search
        search_results = await self._tavily_search(query)

        # Extract sources
        sources = [r["url"] for r in search_results.get("results", [])]

        # Extract structured offers
        extracted = await self._gemini_extract(search_results, restaurant_name, city)

        # Convert to RestaurantOffer objects
        offers = []
        for item in extracted.get("offers", []):
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

        # Filter offers by user's selected platforms
        if platforms:
            offers = [o for o in offers if o.platform in platforms]

        return SearchResult(
            restaurant_name=restaurant_name,
            city=city,
            offers=offers,
            summary=extracted.get("summary"),
            sources=sources,
            provider=self.provider_name,
        )

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
                continue
            all_offers.extend(result.offers)
            all_sources.extend(result.sources)
            if result.summary:
                summaries.append(result.summary)

        return SearchResult(
            restaurant_name=restaurant_name,
            city=city,
            offers=all_offers,
            summary=" | ".join(summaries) if summaries else None,
            sources=list(set(all_sources)),
            provider=self.provider_name,
        )

    async def search_restaurant_offers_stream(
        self,
        restaurant_name: str,
        city: str,
        platforms: Optional[List[Platform]] = None,
        parallel: bool = True,
    ) -> AsyncIterator[RestaurantOffer]:
        """
        Stream offers. Tavily doesn't natively stream, so we fetch all
        and yield one by one.
        """
        result = await self.search_restaurant_offers(restaurant_name, city, platforms, parallel=parallel)

        for offer in result.offers:
            yield offer

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

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()

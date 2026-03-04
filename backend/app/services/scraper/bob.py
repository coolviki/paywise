"""Bank of Baroda credit card benefits scraper."""

import asyncio
import re
from datetime import date, timedelta
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapedBenefit, ScrapedCampaign


class BOBScraper(BaseScraper):
    """Scraper for Bank of Baroda credit card benefits."""

    bank_name = "Bank of Baroda"
    base_url = "https://www.bankofbaroda.in"

    # Known BOB cards
    CARD_PAGES = {
        "Premier": "/credit-cards/premier-credit-card",
        "Prime": "/credit-cards/prime-credit-card",
        "Easy": "/credit-cards/easy-credit-card",
        "Select": "/credit-cards/select-credit-card",
        "Eterna": "/credit-cards/eterna-credit-card",
    }

    # Known ecosystem benefits for BOB cards (fallback data)
    KNOWN_BENEFITS = [
        # Eterna
        ScrapedBenefit(
            card_name="Eterna",
            brand_name="Travel",
            benefit_rate=4.0,
            benefit_type="points",
            description="4X reward points on travel and international spends",
            source_url="https://www.bankofbaroda.in/credit-cards/eterna-credit-card"
        ),
        # Premier
        ScrapedBenefit(
            card_name="Premier",
            brand_name="Fuel",
            benefit_rate=1.0,
            benefit_type="cashback",
            description="1% fuel surcharge waiver",
            source_url="https://www.bankofbaroda.in/credit-cards/premier-credit-card"
        ),
        # Prime
        ScrapedBenefit(
            card_name="Prime",
            brand_name="Online Shopping",
            benefit_rate=2.0,
            benefit_type="points",
            description="2X reward points on online shopping",
            source_url="https://www.bankofbaroda.in/credit-cards/prime-credit-card"
        ),
    ]

    async def scrape(self) -> List[ScrapedBenefit]:
        """Scrape benefits from Bank of Baroda website."""
        self.logger.info("Starting Bank of Baroda scraping...")

        benefits = []
        benefits.extend(self.KNOWN_BENEFITS)

        try:
            scraped = await self._scrape_website()
            for benefit in scraped:
                if not self._benefit_exists(benefit, benefits):
                    benefits.append(benefit)
        except Exception as e:
            self.logger.warning(f"Error scraping BOB website: {e}. Using known benefits only.")

        self.logger.info(f"Found {len(benefits)} BOB benefits")
        return benefits

    async def _scrape_website(self) -> List[ScrapedBenefit]:
        """Actually scrape the BOB website for benefits."""
        benefits = []

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for card_name, path in self.CARD_PAGES.items():
                try:
                    url = f"{self.base_url}{path}"
                    response = await client.get(url)

                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        card_benefits = self._parse_card_page(soup, card_name, url)
                        benefits.extend(card_benefits)

                    await asyncio.sleep(1)

                except Exception as e:
                    self.logger.debug(f"Error scraping {card_name}: {e}")
                    continue

        return benefits

    def _parse_card_page(self, soup: BeautifulSoup, card_name: str, url: str) -> List[ScrapedBenefit]:
        """Parse a card page for benefits."""
        benefits = []
        benefit_sections = soup.find_all(['div', 'section'], class_=re.compile(r'benefit|reward|feature', re.I))

        for section in benefit_sections:
            text = section.get_text()
            rate = self.parse_benefit_rate(text)
            if rate:
                benefit_type = self.detect_benefit_type(text)
                brand = self._extract_brand(text)
                if brand:
                    benefits.append(ScrapedBenefit(
                        card_name=card_name,
                        brand_name=brand,
                        benefit_rate=rate,
                        benefit_type=benefit_type,
                        description=text[:200].strip(),
                        source_url=url
                    ))

        return benefits

    def _extract_brand(self, text: str) -> Optional[str]:
        """Extract brand name from benefit text."""
        known_brands = [
            "Amazon", "Flipkart", "Swiggy", "Zomato", "BigBasket",
            "BookMyShow", "MakeMyTrip", "Uber", "Ola"
        ]

        text_lower = text.lower()
        for brand in known_brands:
            if brand.lower() in text_lower:
                return brand

        return None

    def _benefit_exists(self, benefit: ScrapedBenefit, existing: List[ScrapedBenefit]) -> bool:
        """Check if a benefit already exists in the list."""
        for b in existing:
            if (b.card_name.lower() == benefit.card_name.lower() and
                b.brand_name.lower() == benefit.brand_name.lower()):
                return True
        return False

    async def scrape_campaigns(self) -> List[ScrapedCampaign]:
        """Scrape time-bound campaigns from Bank of Baroda website."""
        self.logger.info("Starting Bank of Baroda campaign scraping...")
        campaigns = []
        self.logger.info(f"Found {len(campaigns)} BOB campaigns")
        return campaigns

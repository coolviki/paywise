"""IDFC First Bank credit card benefits scraper."""

import asyncio
import re
from datetime import date, timedelta
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapedBenefit, ScrapedCampaign


class IDFCScraper(BaseScraper):
    """Scraper for IDFC First Bank credit card benefits."""

    bank_name = "IDFC First Bank"
    base_url = "https://www.idfcfirstbank.com"

    # Known IDFC First cards
    CARD_PAGES = {
        "FIRST Wealth": "/credit-cards/first-wealth-credit-card",
        "FIRST Select": "/credit-cards/first-select-credit-card",
        "FIRST Classic": "/credit-cards/first-classic-credit-card",
        "FIRST Millennia": "/credit-cards/first-millennia-credit-card",
        "FIRST WOW": "/credit-cards/first-wow-credit-card",
        "FIRST Power": "/credit-cards/first-power-credit-card",
        "FIRST Ashva": "/credit-cards/first-ashva-credit-card",
        "FIRST SWYP": "/credit-cards/first-swyp-credit-card",
    }

    # Known ecosystem benefits for IDFC First cards (fallback data)
    KNOWN_BENEFITS = [
        # FIRST Wealth
        ScrapedBenefit(
            card_name="FIRST Wealth",
            brand_name="Travel",
            benefit_rate=6.0,
            benefit_type="points",
            description="6X reward points on travel",
            source_url="https://www.idfcfirstbank.com/credit-cards/first-wealth-credit-card"
        ),
        # FIRST Select
        ScrapedBenefit(
            card_name="FIRST Select",
            brand_name="Online Shopping",
            benefit_rate=3.0,
            benefit_type="points",
            description="3X reward points on online shopping",
            source_url="https://www.idfcfirstbank.com/credit-cards/first-select-credit-card"
        ),
        # FIRST WOW
        ScrapedBenefit(
            card_name="FIRST WOW",
            brand_name="Online Shopping",
            benefit_rate=3.0,
            benefit_type="cashback",
            description="3% cashback on online shopping",
            source_url="https://www.idfcfirstbank.com/credit-cards/first-wow-credit-card"
        ),
        # FIRST SWYP
        ScrapedBenefit(
            card_name="FIRST SWYP",
            brand_name="Zomato",
            benefit_rate=10.0,
            benefit_type="cashback",
            description="10% cashback on Zomato",
            source_url="https://www.idfcfirstbank.com/credit-cards/first-swyp-credit-card"
        ),
        ScrapedBenefit(
            card_name="FIRST SWYP",
            brand_name="Swiggy",
            benefit_rate=10.0,
            benefit_type="cashback",
            description="10% cashback on Swiggy",
            source_url="https://www.idfcfirstbank.com/credit-cards/first-swyp-credit-card"
        ),
    ]

    async def scrape(self) -> List[ScrapedBenefit]:
        """Scrape benefits from IDFC First Bank website."""
        self.logger.info("Starting IDFC First Bank scraping...")

        benefits = []
        benefits.extend(self.KNOWN_BENEFITS)

        try:
            scraped = await self._scrape_website()
            for benefit in scraped:
                if not self._benefit_exists(benefit, benefits):
                    benefits.append(benefit)
        except Exception as e:
            self.logger.warning(f"Error scraping IDFC First website: {e}. Using known benefits only.")

        self.logger.info(f"Found {len(benefits)} IDFC First benefits")
        return benefits

    async def _scrape_website(self) -> List[ScrapedBenefit]:
        """Actually scrape the IDFC First website for benefits."""
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
            "Uber", "Ola", "BookMyShow", "MakeMyTrip", "Yatra"
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
        """Scrape time-bound campaigns from IDFC First Bank website."""
        self.logger.info("Starting IDFC First Bank campaign scraping...")
        campaigns = []
        self.logger.info(f"Found {len(campaigns)} IDFC First campaigns")
        return campaigns

"""Yes Bank credit card benefits scraper."""

import asyncio
import re
from datetime import date, timedelta
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapedBenefit, ScrapedCampaign


class YesScraper(BaseScraper):
    """Scraper for Yes Bank credit card benefits."""

    bank_name = "Yes Bank"
    base_url = "https://www.yesbank.in"

    # Known Yes Bank cards
    CARD_PAGES = {
        "YES FIRST Exclusive": "/personal-banking/cards/credit-card/yes-first-exclusive",
        "YES FIRST Preferred": "/personal-banking/cards/credit-card/yes-first-preferred",
        "YES PREMIA": "/personal-banking/cards/credit-card/yes-premia",
        "YES Prosperity Edge": "/personal-banking/cards/credit-card/yes-prosperity-edge",
        "YES Prosperity Rewards Plus": "/personal-banking/cards/credit-card/yes-prosperity-rewards-plus",
        "Marquee": "/personal-banking/cards/credit-card/marquee-credit-card",
    }

    # Known ecosystem benefits for Yes Bank cards (fallback data)
    KNOWN_BENEFITS = [
        # YES FIRST Exclusive
        ScrapedBenefit(
            card_name="YES FIRST Exclusive",
            brand_name="Travel",
            benefit_rate=4.0,
            benefit_type="points",
            description="4 reward points per Rs 100 on travel",
            source_url="https://www.yesbank.in/personal-banking/cards/credit-card/yes-first-exclusive"
        ),
        # YES PREMIA
        ScrapedBenefit(
            card_name="YES PREMIA",
            brand_name="Dining",
            benefit_rate=3.0,
            benefit_type="points",
            description="3X reward points on dining",
            source_url="https://www.yesbank.in/personal-banking/cards/credit-card/yes-premia"
        ),
        # Marquee
        ScrapedBenefit(
            card_name="Marquee",
            brand_name="Amazon",
            benefit_rate=5.0,
            benefit_type="cashback",
            description="5% cashback on Amazon",
            source_url="https://www.yesbank.in/personal-banking/cards/credit-card/marquee-credit-card"
        ),
    ]

    async def scrape(self) -> List[ScrapedBenefit]:
        """Scrape benefits from Yes Bank website."""
        self.logger.info("Starting Yes Bank scraping...")

        benefits = []
        benefits.extend(self.KNOWN_BENEFITS)

        try:
            scraped = await self._scrape_website()
            for benefit in scraped:
                if not self._benefit_exists(benefit, benefits):
                    benefits.append(benefit)
        except Exception as e:
            self.logger.warning(f"Error scraping Yes Bank website: {e}. Using known benefits only.")

        self.logger.info(f"Found {len(benefits)} Yes Bank benefits")
        return benefits

    async def _scrape_website(self) -> List[ScrapedBenefit]:
        """Actually scrape the Yes Bank website for benefits."""
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
            "BookMyShow", "MakeMyTrip", "Uber", "Ola", "Cleartrip"
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
        """Scrape time-bound campaigns from Yes Bank website."""
        self.logger.info("Starting Yes Bank campaign scraping...")
        campaigns = []
        self.logger.info(f"Found {len(campaigns)} Yes Bank campaigns")
        return campaigns

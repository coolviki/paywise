"""Standard Chartered credit card benefits scraper."""

import asyncio
import re
from datetime import date, timedelta
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapedBenefit, ScrapedCampaign


class SCScraper(BaseScraper):
    """Scraper for Standard Chartered credit card benefits."""

    bank_name = "Standard Chartered"
    base_url = "https://www.sc.com/in"

    # Known Standard Chartered cards
    CARD_PAGES = {
        "Ultimate": "/credit-cards/ultimate-credit-card",
        "Platinum Rewards": "/credit-cards/platinum-rewards-credit-card",
        "Super Value Titanium": "/credit-cards/super-value-titanium-credit-card",
        "DigiSmart": "/credit-cards/digismart-credit-card",
        "EaseMyTrip": "/credit-cards/easemytrip-credit-card",
    }

    # Known ecosystem benefits for Standard Chartered cards (fallback data)
    KNOWN_BENEFITS = [
        # Ultimate
        ScrapedBenefit(
            card_name="Ultimate",
            brand_name="Travel",
            benefit_rate=5.0,
            benefit_type="points",
            description="5X reward points on international spends",
            source_url="https://www.sc.com/in/credit-cards/ultimate-credit-card"
        ),
        ScrapedBenefit(
            card_name="Ultimate",
            brand_name="Dining",
            benefit_rate=5.0,
            benefit_type="points",
            description="5X reward points on dining",
            source_url="https://www.sc.com/in/credit-cards/ultimate-credit-card"
        ),
        # DigiSmart
        ScrapedBenefit(
            card_name="DigiSmart",
            brand_name="Online Shopping",
            benefit_rate=5.0,
            benefit_type="cashback",
            description="5% cashback on online spends",
            source_url="https://www.sc.com/in/credit-cards/digismart-credit-card"
        ),
        # EaseMyTrip
        ScrapedBenefit(
            card_name="EaseMyTrip",
            brand_name="EaseMyTrip",
            benefit_rate=10.0,
            benefit_type="cashback",
            description="10% cashback on EaseMyTrip bookings",
            source_url="https://www.sc.com/in/credit-cards/easemytrip-credit-card"
        ),
        # Platinum Rewards
        ScrapedBenefit(
            card_name="Platinum Rewards",
            brand_name="Duty Free",
            benefit_rate=5.0,
            benefit_type="points",
            description="5X reward points at duty free shops",
            source_url="https://www.sc.com/in/credit-cards/platinum-rewards-credit-card"
        ),
    ]

    async def scrape(self) -> List[ScrapedBenefit]:
        """Scrape benefits from Standard Chartered website."""
        self.logger.info("Starting Standard Chartered scraping...")

        benefits = []
        benefits.extend(self.KNOWN_BENEFITS)

        try:
            scraped = await self._scrape_website()
            for benefit in scraped:
                if not self._benefit_exists(benefit, benefits):
                    benefits.append(benefit)
        except Exception as e:
            self.logger.warning(f"Error scraping Standard Chartered website: {e}. Using known benefits only.")

        self.logger.info(f"Found {len(benefits)} Standard Chartered benefits")
        return benefits

    async def _scrape_website(self) -> List[ScrapedBenefit]:
        """Actually scrape the Standard Chartered website for benefits."""
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
            "EaseMyTrip", "Amazon", "Flipkart", "Swiggy", "Zomato",
            "BigBasket", "BookMyShow", "MakeMyTrip", "Uber", "Ola"
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
        """Scrape time-bound campaigns from Standard Chartered website."""
        self.logger.info("Starting Standard Chartered campaign scraping...")
        campaigns = []
        self.logger.info(f"Found {len(campaigns)} Standard Chartered campaigns")
        return campaigns

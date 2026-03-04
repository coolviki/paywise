"""HSBC credit card benefits scraper."""

import asyncio
import re
from datetime import date, timedelta
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapedBenefit, ScrapedCampaign


class HSBCScraper(BaseScraper):
    """Scraper for HSBC credit card benefits."""

    bank_name = "HSBC"
    base_url = "https://www.hsbc.co.in"

    # Known HSBC cards
    CARD_PAGES = {
        "Smart Value": "/credit-cards/smart-value-credit-card",
        "Visa Platinum": "/credit-cards/visa-platinum-credit-card",
        "Cashback": "/credit-cards/cashback-credit-card",
        "Premier": "/credit-cards/premier-credit-card",
        "Live+": "/credit-cards/live-plus-credit-card",
        "TravelOne": "/credit-cards/travelone-credit-card",
    }

    # Known ecosystem benefits for HSBC cards (fallback data)
    KNOWN_BENEFITS = [
        # Cashback Card
        ScrapedBenefit(
            card_name="Cashback",
            brand_name="Online Shopping",
            benefit_rate=2.5,
            benefit_type="cashback",
            description="2.5% cashback on online spends",
            source_url="https://www.hsbc.co.in/credit-cards/cashback-credit-card"
        ),
        # Smart Value
        ScrapedBenefit(
            card_name="Smart Value",
            brand_name="Grocery",
            benefit_rate=10.0,
            benefit_type="points",
            description="10X reward points on grocery spends",
            source_url="https://www.hsbc.co.in/credit-cards/smart-value-credit-card"
        ),
        ScrapedBenefit(
            card_name="Smart Value",
            brand_name="Fuel",
            benefit_rate=10.0,
            benefit_type="points",
            description="10X reward points on fuel",
            source_url="https://www.hsbc.co.in/credit-cards/smart-value-credit-card"
        ),
        # TravelOne
        ScrapedBenefit(
            card_name="TravelOne",
            brand_name="Travel",
            benefit_rate=6.0,
            benefit_type="miles",
            description="6 airmiles per Rs 150 on travel spends",
            source_url="https://www.hsbc.co.in/credit-cards/travelone-credit-card"
        ),
        # Live+
        ScrapedBenefit(
            card_name="Live+",
            brand_name="Entertainment",
            benefit_rate=4.0,
            benefit_type="points",
            description="4X reward points on entertainment",
            source_url="https://www.hsbc.co.in/credit-cards/live-plus-credit-card"
        ),
        # Premier
        ScrapedBenefit(
            card_name="Premier",
            brand_name="International",
            benefit_rate=3.0,
            benefit_type="points",
            description="3X reward points on international spends",
            source_url="https://www.hsbc.co.in/credit-cards/premier-credit-card"
        ),
    ]

    async def scrape(self) -> List[ScrapedBenefit]:
        """Scrape benefits from HSBC website."""
        self.logger.info("Starting HSBC scraping...")

        benefits = []
        benefits.extend(self.KNOWN_BENEFITS)

        try:
            scraped = await self._scrape_website()
            for benefit in scraped:
                if not self._benefit_exists(benefit, benefits):
                    benefits.append(benefit)
        except Exception as e:
            self.logger.warning(f"Error scraping HSBC website: {e}. Using known benefits only.")

        self.logger.info(f"Found {len(benefits)} HSBC benefits")
        return benefits

    async def _scrape_website(self) -> List[ScrapedBenefit]:
        """Actually scrape the HSBC website for benefits."""
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
        """Scrape time-bound campaigns from HSBC website."""
        self.logger.info("Starting HSBC campaign scraping...")
        campaigns = []
        self.logger.info(f"Found {len(campaigns)} HSBC campaigns")
        return campaigns

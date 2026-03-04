"""RBL Bank credit card benefits scraper."""

import asyncio
import re
from datetime import date, timedelta
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapedBenefit, ScrapedCampaign


class RBLScraper(BaseScraper):
    """Scraper for RBL Bank credit card benefits."""

    bank_name = "RBL Bank"
    base_url = "https://www.rblbank.com"

    # Known RBL cards
    CARD_PAGES = {
        "World Safari": "/credit-cards/world-safari-credit-card",
        "Platinum Maxima": "/credit-cards/platinum-maxima-credit-card",
        "Platinum Delight": "/credit-cards/platinum-delight-credit-card",
        "ShopRite": "/credit-cards/shoprite-credit-card",
        "Popcorn": "/credit-cards/popcorn-credit-card",
        "Play": "/credit-cards/play-credit-card",
        "Bankbazaar Savings": "/credit-cards/bankbazaar-savings-credit-card",
        "Zomato Edition": "/credit-cards/zomato-edition-credit-card",
        "Icon": "/credit-cards/icon-credit-card",
    }

    # Known ecosystem benefits for RBL cards (fallback data)
    KNOWN_BENEFITS = [
        # Zomato Edition
        ScrapedBenefit(
            card_name="Zomato Edition",
            brand_name="Zomato",
            benefit_rate=10.0,
            benefit_type="cashback",
            description="10% cashback on Zomato orders",
            source_url="https://www.rblbank.com/credit-cards/zomato-edition-credit-card"
        ),
        # ShopRite
        ScrapedBenefit(
            card_name="ShopRite",
            brand_name="Online Shopping",
            benefit_rate=5.0,
            benefit_type="cashback",
            description="5% cashback on online shopping",
            source_url="https://www.rblbank.com/credit-cards/shoprite-credit-card"
        ),
        # Popcorn
        ScrapedBenefit(
            card_name="Popcorn",
            brand_name="BookMyShow",
            benefit_rate=10.0,
            benefit_type="cashback",
            description="Buy 1 Get 1 on BookMyShow",
            source_url="https://www.rblbank.com/credit-cards/popcorn-credit-card"
        ),
        ScrapedBenefit(
            card_name="Popcorn",
            brand_name="PVR",
            benefit_rate=10.0,
            benefit_type="cashback",
            description="Buy 1 Get 1 on PVR movies",
            source_url="https://www.rblbank.com/credit-cards/popcorn-credit-card"
        ),
        # World Safari
        ScrapedBenefit(
            card_name="World Safari",
            brand_name="Travel",
            benefit_rate=4.0,
            benefit_type="points",
            description="4% value back on travel bookings",
            source_url="https://www.rblbank.com/credit-cards/world-safari-credit-card"
        ),
    ]

    async def scrape(self) -> List[ScrapedBenefit]:
        """Scrape benefits from RBL Bank website."""
        self.logger.info("Starting RBL Bank scraping...")

        benefits = []
        benefits.extend(self.KNOWN_BENEFITS)

        try:
            scraped = await self._scrape_website()
            for benefit in scraped:
                if not self._benefit_exists(benefit, benefits):
                    benefits.append(benefit)
        except Exception as e:
            self.logger.warning(f"Error scraping RBL website: {e}. Using known benefits only.")

        self.logger.info(f"Found {len(benefits)} RBL benefits")
        return benefits

    async def _scrape_website(self) -> List[ScrapedBenefit]:
        """Actually scrape the RBL website for benefits."""
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
            "Zomato", "BookMyShow", "PVR", "INOX", "Amazon",
            "Flipkart", "Swiggy", "BigBasket", "Uber", "Ola"
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
        """Scrape time-bound campaigns from RBL Bank website."""
        self.logger.info("Starting RBL Bank campaign scraping...")
        campaigns = []
        self.logger.info(f"Found {len(campaigns)} RBL campaigns")
        return campaigns

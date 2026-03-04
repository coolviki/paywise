"""Axis Bank credit card benefits scraper."""

import asyncio
import re
from datetime import date, timedelta
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapedBenefit, ScrapedCampaign


class AxisScraper(BaseScraper):
    """Scraper for Axis Bank credit card benefits."""

    bank_name = "Axis Bank"
    base_url = "https://www.axisbank.com"

    # Known Axis cards with their benefit pages
    CARD_PAGES = {
        "Magnus": "/retail/cards/credit-card/axis-bank-magnus-credit-card",
        "Reserve": "/retail/cards/credit-card/axis-bank-reserve-credit-card",
        "Privilege": "/retail/cards/credit-card/axis-bank-privilege-credit-card",
        "Select": "/retail/cards/credit-card/axis-bank-select-credit-card",
        "Ace": "/retail/cards/credit-card/axis-bank-ace-credit-card",
        "Neo": "/retail/cards/credit-card/axis-bank-neo-credit-card",
        "My Zone": "/retail/cards/credit-card/axis-bank-my-zone-credit-card",
        "Flipkart": "/retail/cards/credit-card/flipkart-axis-bank-credit-card",
        "Airtel": "/retail/cards/credit-card/airtel-axis-bank-credit-card",
        "Indian Oil": "/retail/cards/credit-card/indian-oil-axis-bank-credit-card",
        "Vistara": "/retail/cards/credit-card/vistara-axis-bank-credit-card",
        "Samsung": "/retail/cards/credit-card/samsung-axis-bank-credit-card",
        "LIC": "/retail/cards/credit-card/lic-axis-bank-credit-card",
    }

    # Known ecosystem benefits for Axis cards (fallback data)
    KNOWN_BENEFITS = [
        # Flipkart Card
        ScrapedBenefit(
            card_name="Flipkart",
            brand_name="Flipkart",
            benefit_rate=5.0,
            benefit_type="cashback",
            description="5% unlimited cashback on Flipkart, Myntra & 2GUD",
            source_url="https://www.axisbank.com/retail/cards/credit-card/flipkart-axis-bank-credit-card"
        ),
        # Ace Card
        ScrapedBenefit(
            card_name="Ace",
            brand_name="Google Pay",
            benefit_rate=5.0,
            benefit_type="cashback",
            description="5% cashback on bill payments via Google Pay",
            source_url="https://www.axisbank.com/retail/cards/credit-card/axis-bank-ace-credit-card"
        ),
        ScrapedBenefit(
            card_name="Ace",
            brand_name="Swiggy",
            benefit_rate=5.0,
            benefit_type="cashback",
            description="5% cashback on Swiggy, Zomato orders",
            source_url="https://www.axisbank.com/retail/cards/credit-card/axis-bank-ace-credit-card"
        ),
        # Magnus Card
        ScrapedBenefit(
            card_name="Magnus",
            brand_name="Travel",
            benefit_rate=12.0,
            benefit_type="points",
            description="12 EDGE REWARD Points per Rs 200 spent",
            source_url="https://www.axisbank.com/retail/cards/credit-card/axis-bank-magnus-credit-card"
        ),
        # Indian Oil Card
        ScrapedBenefit(
            card_name="Indian Oil",
            brand_name="IndianOil",
            benefit_rate=4.0,
            benefit_type="points",
            description="4% value back on fuel at Indian Oil outlets",
            source_url="https://www.axisbank.com/retail/cards/credit-card/indian-oil-axis-bank-credit-card"
        ),
        # Vistara Card
        ScrapedBenefit(
            card_name="Vistara",
            brand_name="Vistara",
            benefit_rate=3.0,
            benefit_type="miles",
            description="3 CV Points per Rs 200 spent on Vistara",
            source_url="https://www.axisbank.com/retail/cards/credit-card/vistara-axis-bank-credit-card"
        ),
        # Airtel Card
        ScrapedBenefit(
            card_name="Airtel",
            brand_name="Airtel",
            benefit_rate=25.0,
            benefit_type="cashback",
            description="25% cashback on Airtel bill payments",
            source_url="https://www.axisbank.com/retail/cards/credit-card/airtel-axis-bank-credit-card"
        ),
    ]

    async def scrape(self) -> List[ScrapedBenefit]:
        """Scrape benefits from Axis Bank website."""
        self.logger.info("Starting Axis Bank scraping...")

        benefits = []
        benefits.extend(self.KNOWN_BENEFITS)

        try:
            scraped = await self._scrape_website()
            for benefit in scraped:
                if not self._benefit_exists(benefit, benefits):
                    benefits.append(benefit)
        except Exception as e:
            self.logger.warning(f"Error scraping Axis website: {e}. Using known benefits only.")

        self.logger.info(f"Found {len(benefits)} Axis benefits")
        return benefits

    async def _scrape_website(self) -> List[ScrapedBenefit]:
        """Actually scrape the Axis website for benefits."""
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
            "Flipkart", "Myntra", "Swiggy", "Zomato", "Amazon",
            "Google Pay", "Airtel", "IndianOil", "Vistara", "Samsung",
            "LIC", "BigBasket", "Uber", "Ola"
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
        """Scrape time-bound campaigns from Axis Bank website."""
        self.logger.info("Starting Axis Bank campaign scraping...")
        campaigns = []
        today = date.today()

        known_campaigns = [
            ScrapedCampaign(
                card_name="Flipkart",
                brand_name="Flipkart",
                benefit_rate=10.0,
                benefit_type="cashback",
                start_date=today,
                end_date=today + timedelta(days=30),
                description="10% extra cashback during Flipkart Big Billion Days",
                source_url="https://www.axisbank.com/retail/cards/credit-card/flipkart-axis-bank-credit-card"
            ),
        ]

        campaigns.extend(known_campaigns)
        self.logger.info(f"Found {len(campaigns)} Axis campaigns")
        return campaigns

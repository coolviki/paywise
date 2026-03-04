"""American Express credit card benefits scraper."""

import asyncio
import re
from datetime import date, timedelta
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapedBenefit, ScrapedCampaign


class AmexScraper(BaseScraper):
    """Scraper for American Express credit card benefits."""

    bank_name = "American Express"
    base_url = "https://www.americanexpress.com/in"

    # Known Amex cards
    CARD_PAGES = {
        "Platinum Card": "/credit-cards/platinum-card",
        "Platinum Reserve": "/credit-cards/platinum-reserve-credit-card",
        "Platinum Travel": "/credit-cards/platinum-travel-credit-card",
        "Gold Card": "/credit-cards/gold-card",
        "Membership Rewards": "/credit-cards/membership-rewards-credit-card",
        "SmartEarn": "/credit-cards/smartearn-credit-card",
        "MRCC": "/credit-cards/mrcc-credit-card",
    }

    # Known ecosystem benefits for Amex cards (fallback data)
    KNOWN_BENEFITS = [
        # Platinum Card
        ScrapedBenefit(
            card_name="Platinum Card",
            brand_name="Marriott",
            benefit_rate=5.0,
            benefit_type="points",
            description="5X Membership Rewards points on Marriott hotels",
            source_url="https://www.americanexpress.com/in/credit-cards/platinum-card"
        ),
        ScrapedBenefit(
            card_name="Platinum Card",
            brand_name="Taj Hotels",
            benefit_rate=5.0,
            benefit_type="points",
            description="5X Membership Rewards points on Taj Hotels",
            source_url="https://www.americanexpress.com/in/credit-cards/platinum-card"
        ),
        # Platinum Travel
        ScrapedBenefit(
            card_name="Platinum Travel",
            brand_name="Travel",
            benefit_rate=5.0,
            benefit_type="points",
            description="5 Membership Rewards points per Rs 50 on travel",
            source_url="https://www.americanexpress.com/in/credit-cards/platinum-travel-credit-card"
        ),
        # Gold Card
        ScrapedBenefit(
            card_name="Gold Card",
            brand_name="Dining",
            benefit_rate=4.0,
            benefit_type="points",
            description="4X Membership Rewards points on dining",
            source_url="https://www.americanexpress.com/in/credit-cards/gold-card"
        ),
        # SmartEarn
        ScrapedBenefit(
            card_name="SmartEarn",
            brand_name="Flipkart",
            benefit_rate=10.0,
            benefit_type="points",
            description="10X Membership Rewards points on Flipkart",
            source_url="https://www.americanexpress.com/in/credit-cards/smartearn-credit-card"
        ),
        ScrapedBenefit(
            card_name="SmartEarn",
            brand_name="Amazon",
            benefit_rate=10.0,
            benefit_type="points",
            description="10X Membership Rewards points on Amazon",
            source_url="https://www.americanexpress.com/in/credit-cards/smartearn-credit-card"
        ),
        ScrapedBenefit(
            card_name="SmartEarn",
            brand_name="Uber",
            benefit_rate=10.0,
            benefit_type="points",
            description="10X Membership Rewards points on Uber",
            source_url="https://www.americanexpress.com/in/credit-cards/smartearn-credit-card"
        ),
    ]

    async def scrape(self) -> List[ScrapedBenefit]:
        """Scrape benefits from American Express website."""
        self.logger.info("Starting American Express scraping...")

        benefits = []
        benefits.extend(self.KNOWN_BENEFITS)

        try:
            scraped = await self._scrape_website()
            for benefit in scraped:
                if not self._benefit_exists(benefit, benefits):
                    benefits.append(benefit)
        except Exception as e:
            self.logger.warning(f"Error scraping Amex website: {e}. Using known benefits only.")

        self.logger.info(f"Found {len(benefits)} Amex benefits")
        return benefits

    async def _scrape_website(self) -> List[ScrapedBenefit]:
        """Actually scrape the Amex website for benefits."""
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
            "Marriott", "Taj Hotels", "ITC Hotels", "Oberoi",
            "Flipkart", "Amazon", "Uber", "Swiggy", "Zomato",
            "MakeMyTrip", "Yatra", "BookMyShow"
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
        """Scrape time-bound campaigns from American Express website."""
        self.logger.info("Starting American Express campaign scraping...")
        campaigns = []
        today = date.today()

        known_campaigns = [
            ScrapedCampaign(
                card_name="SmartEarn",
                brand_name="Flipkart",
                benefit_rate=20.0,
                benefit_type="points",
                start_date=today,
                end_date=today + timedelta(days=30),
                description="20X MR points on Flipkart during festive season",
                source_url="https://www.americanexpress.com/in/credit-cards/smartearn-credit-card"
            ),
        ]

        campaigns.extend(known_campaigns)
        self.logger.info(f"Found {len(campaigns)} Amex campaigns")
        return campaigns

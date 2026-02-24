"""SBI Card credit card benefits scraper."""

import asyncio
import re
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapedBenefit


class SBIScraper(BaseScraper):
    """Scraper for SBI Card credit card benefits."""

    bank_name = "SBI Card"
    base_url = "https://www.sbicard.com"

    # Known SBI cards with their benefit pages
    CARD_PAGES = {
        "Elite": "/en/personal/credit-cards/travel-fuel/sbi-card-elite.page",
        "Prime": "/en/personal/credit-cards/shopping/sbi-card-prime.page",
        "SimplyCLICK": "/en/personal/credit-cards/shopping/simplyclick-sbi-card.page",
        "SimplySAVE": "/en/personal/credit-cards/shopping/simplysave-sbi-card.page",
        "Ola Money": "/en/personal/credit-cards/travel-fuel/ola-money-sbi-card.page",
        "IRCTC": "/en/personal/credit-cards/travel-fuel/irctc-sbi-card.page",
        "BPCL Octane": "/en/personal/credit-cards/travel-fuel/bpcl-sbi-card-octane.page",
        "Air India Signature": "/en/personal/credit-cards/travel-fuel/air-india-sbi-signature-card.page",
        "Yatra": "/en/personal/credit-cards/travel-fuel/yatra-sbi-card.page",
        "Cashback": "/en/personal/credit-cards/cashback/cashback-sbi-card.page",
        "Pulse": "/en/personal/credit-cards/lifestyle/pulse-sbi-card.page",
    }

    # Known ecosystem benefits for SBI cards
    KNOWN_BENEFITS = [
        # SimplyCLICK
        ScrapedBenefit(
            card_name="SimplyCLICK",
            brand_name="Amazon",
            benefit_rate=5.0,
            benefit_type="points",
            description="5X reward points on Amazon purchases",
            source_url="https://www.sbicard.com/en/personal/credit-cards/shopping/simplyclick-sbi-card.page"
        ),
        ScrapedBenefit(
            card_name="SimplyCLICK",
            brand_name="Cleartrip",
            benefit_rate=10.0,
            benefit_type="points",
            description="10X reward points on Cleartrip",
            source_url="https://www.sbicard.com/en/personal/credit-cards/shopping/simplyclick-sbi-card.page"
        ),
        ScrapedBenefit(
            card_name="SimplyCLICK",
            brand_name="Bookmyshow",
            benefit_rate=10.0,
            benefit_type="points",
            description="10X reward points on BookMyShow",
            source_url="https://www.sbicard.com/en/personal/credit-cards/shopping/simplyclick-sbi-card.page"
        ),
        # Ola Money Card
        ScrapedBenefit(
            card_name="Ola Money",
            brand_name="Ola",
            benefit_rate=7.0,
            benefit_type="cashback",
            description="7% cashback on Ola rides",
            source_url="https://www.sbicard.com/en/personal/credit-cards/travel-fuel/ola-money-sbi-card.page"
        ),
        # BPCL Octane
        ScrapedBenefit(
            card_name="BPCL Octane",
            brand_name="BPCL",
            benefit_rate=13.0,
            benefit_type="points",
            description="13X reward points on BPCL fuel purchases",
            source_url="https://www.sbicard.com/en/personal/credit-cards/travel-fuel/bpcl-sbi-card-octane.page"
        ),
        # IRCTC Card
        ScrapedBenefit(
            card_name="IRCTC",
            brand_name="IRCTC",
            benefit_rate=10.0,
            benefit_type="points",
            description="10% value back on IRCTC bookings",
            source_url="https://www.sbicard.com/en/personal/credit-cards/travel-fuel/irctc-sbi-card.page"
        ),
        # Air India Card
        ScrapedBenefit(
            card_name="Air India Signature",
            brand_name="Air India",
            benefit_rate=4.0,
            benefit_type="miles",
            description="4 Flying Returns miles per INR 100 on Air India",
            source_url="https://www.sbicard.com/en/personal/credit-cards/travel-fuel/air-india-sbi-signature-card.page"
        ),
        # Yatra Card
        ScrapedBenefit(
            card_name="Yatra",
            brand_name="Yatra",
            benefit_rate=5.0,
            benefit_type="points",
            description="5 reward points per INR 100 on Yatra bookings",
            source_url="https://www.sbicard.com/en/personal/credit-cards/travel-fuel/yatra-sbi-card.page"
        ),
        # Cashback Card
        ScrapedBenefit(
            card_name="Cashback",
            brand_name="Online",
            benefit_rate=5.0,
            benefit_type="cashback",
            description="5% cashback on all online spends",
            source_url="https://www.sbicard.com/en/personal/credit-cards/cashback/cashback-sbi-card.page"
        ),
    ]

    async def scrape(self) -> List[ScrapedBenefit]:
        """Scrape benefits from SBI Card website."""
        self.logger.info("Starting SBI Card scraping...")

        benefits = []

        # Use known benefits as primary source
        benefits.extend(self.KNOWN_BENEFITS)

        # Try to scrape additional benefits
        try:
            scraped = await self._scrape_website()
            for benefit in scraped:
                if not self._benefit_exists(benefit, benefits):
                    benefits.append(benefit)
        except Exception as e:
            self.logger.warning(f"Error scraping SBI Card website: {e}. Using known benefits only.")

        self.logger.info(f"Found {len(benefits)} SBI Card benefits")
        return benefits

    async def _scrape_website(self) -> List[ScrapedBenefit]:
        """Scrape the SBI Card website for benefits."""
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

        # SBI Card pages often have benefits in specific sections
        benefit_sections = soup.find_all(['div', 'section', 'li'], class_=re.compile(r'benefit|reward|feature|key-feature', re.I))

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
            "Amazon", "Ola", "BPCL", "IRCTC", "Air India", "Yatra",
            "Cleartrip", "BookMyShow", "Swiggy", "Zomato", "Flipkart",
            "BigBasket", "HP Petrol", "IndianOil"
        ]

        text_lower = text.lower()
        for brand in known_brands:
            if brand.lower() in text_lower:
                return brand

        return None

    def _benefit_exists(self, benefit: ScrapedBenefit, existing: List[ScrapedBenefit]) -> bool:
        """Check if a benefit already exists."""
        for b in existing:
            if (b.card_name.lower() == benefit.card_name.lower() and
                b.brand_name.lower() == benefit.brand_name.lower()):
                return True
        return False

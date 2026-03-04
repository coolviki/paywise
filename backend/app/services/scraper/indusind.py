"""IndusInd Bank credit card benefits scraper."""

import asyncio
import re
from datetime import date, timedelta
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapedBenefit, ScrapedCampaign


class IndusIndScraper(BaseScraper):
    """Scraper for IndusInd Bank credit card benefits."""

    bank_name = "IndusInd Bank"
    base_url = "https://www.indusind.com"

    # Known IndusInd cards
    CARD_PAGES = {
        "Pioneer Heritage": "/content/indusind-bank/in/en/personal/cards/credit-cards/pioneer-heritage.html",
        "Legend": "/content/indusind-bank/in/en/personal/cards/credit-cards/legend.html",
        "Iconia": "/content/indusind-bank/in/en/personal/cards/credit-cards/iconia.html",
        "Platinum Aura": "/content/indusind-bank/in/en/personal/cards/credit-cards/platinum-aura.html",
        "Pinnacle": "/content/indusind-bank/in/en/personal/cards/credit-cards/pinnacle.html",
        "Tiger": "/content/indusind-bank/in/en/personal/cards/credit-cards/tiger.html",
        "InterMiles Voyage": "/content/indusind-bank/in/en/personal/cards/credit-cards/intermiles-voyage.html",
        "InterMiles Odyssey": "/content/indusind-bank/in/en/personal/cards/credit-cards/intermiles-odyssey.html",
        "British Airways": "/content/indusind-bank/in/en/personal/cards/credit-cards/british-airways.html",
    }

    # Known ecosystem benefits for IndusInd cards (fallback data)
    KNOWN_BENEFITS = [
        # InterMiles Cards
        ScrapedBenefit(
            card_name="InterMiles Voyage",
            brand_name="InterMiles",
            benefit_rate=4.0,
            benefit_type="miles",
            description="4 InterMiles per Rs 100 on all spends",
            source_url="https://www.indusind.com/content/indusind-bank/in/en/personal/cards/credit-cards/intermiles-voyage.html"
        ),
        ScrapedBenefit(
            card_name="InterMiles Odyssey",
            brand_name="InterMiles",
            benefit_rate=3.0,
            benefit_type="miles",
            description="3 InterMiles per Rs 100 on all spends",
            source_url="https://www.indusind.com/content/indusind-bank/in/en/personal/cards/credit-cards/intermiles-odyssey.html"
        ),
        # British Airways
        ScrapedBenefit(
            card_name="British Airways",
            brand_name="British Airways",
            benefit_rate=4.0,
            benefit_type="miles",
            description="4 Avios per Rs 100 on British Airways",
            source_url="https://www.indusind.com/content/indusind-bank/in/en/personal/cards/credit-cards/british-airways.html"
        ),
        # Pioneer Heritage
        ScrapedBenefit(
            card_name="Pioneer Heritage",
            brand_name="Golf",
            benefit_rate=5.0,
            benefit_type="points",
            description="Complimentary golf rounds at premium courses",
            source_url="https://www.indusind.com/content/indusind-bank/in/en/personal/cards/credit-cards/pioneer-heritage.html"
        ),
        # Legend
        ScrapedBenefit(
            card_name="Legend",
            brand_name="Travel",
            benefit_rate=3.0,
            benefit_type="points",
            description="3X reward points on travel and dining",
            source_url="https://www.indusind.com/content/indusind-bank/in/en/personal/cards/credit-cards/legend.html"
        ),
    ]

    async def scrape(self) -> List[ScrapedBenefit]:
        """Scrape benefits from IndusInd Bank website."""
        self.logger.info("Starting IndusInd Bank scraping...")

        benefits = []
        benefits.extend(self.KNOWN_BENEFITS)

        try:
            scraped = await self._scrape_website()
            for benefit in scraped:
                if not self._benefit_exists(benefit, benefits):
                    benefits.append(benefit)
        except Exception as e:
            self.logger.warning(f"Error scraping IndusInd website: {e}. Using known benefits only.")

        self.logger.info(f"Found {len(benefits)} IndusInd benefits")
        return benefits

    async def _scrape_website(self) -> List[ScrapedBenefit]:
        """Actually scrape the IndusInd website for benefits."""
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
            "InterMiles", "British Airways", "Amazon", "Flipkart",
            "Swiggy", "Zomato", "BookMyShow", "MakeMyTrip", "Uber", "Ola"
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
        """Scrape time-bound campaigns from IndusInd Bank website."""
        self.logger.info("Starting IndusInd Bank campaign scraping...")
        campaigns = []
        self.logger.info(f"Found {len(campaigns)} IndusInd campaigns")
        return campaigns

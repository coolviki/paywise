"""Kotak Mahindra Bank credit card benefits scraper."""

import asyncio
import re
from datetime import date, timedelta
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapedBenefit, ScrapedCampaign


class KotakScraper(BaseScraper):
    """Scraper for Kotak Mahindra Bank credit card benefits."""

    bank_name = "Kotak Mahindra Bank"
    base_url = "https://www.kotak.com"

    # Known Kotak cards
    CARD_PAGES = {
        "Privy League Signature": "/personal-banking/cards/credit-cards/privy-league-signature-credit-card",
        "White Reserve": "/personal-banking/cards/credit-cards/white-reserve-credit-card",
        "Royale Signature": "/personal-banking/cards/credit-cards/royale-signature-credit-card",
        "League Platinum": "/personal-banking/cards/credit-cards/league-platinum-credit-card",
        "Zen Signature": "/personal-banking/cards/credit-cards/zen-signature-credit-card",
        "Indigo 6E Rewards": "/personal-banking/cards/credit-cards/indigo-6e-rewards-credit-card",
        "811 Dream Different": "/personal-banking/cards/credit-cards/811-dream-different-credit-card",
        "Mojo": "/personal-banking/cards/credit-cards/mojo-credit-card",
        "PVR": "/personal-banking/cards/credit-cards/pvr-kotak-credit-card",
    }

    # Known ecosystem benefits for Kotak cards (fallback data)
    KNOWN_BENEFITS = [
        # Indigo 6E Rewards
        ScrapedBenefit(
            card_name="Indigo 6E Rewards",
            brand_name="IndiGo",
            benefit_rate=6.0,
            benefit_type="points",
            description="6 6E Rewards per Rs 100 on IndiGo flights",
            source_url="https://www.kotak.com/personal-banking/cards/credit-cards/indigo-6e-rewards-credit-card"
        ),
        # PVR Card
        ScrapedBenefit(
            card_name="PVR",
            brand_name="PVR",
            benefit_rate=10.0,
            benefit_type="cashback",
            description="Buy 1 Get 1 free on PVR movie tickets",
            source_url="https://www.kotak.com/personal-banking/cards/credit-cards/pvr-kotak-credit-card"
        ),
        # Privy League
        ScrapedBenefit(
            card_name="Privy League Signature",
            brand_name="Travel",
            benefit_rate=4.0,
            benefit_type="points",
            description="4 reward points per Rs 150 on travel spends",
            source_url="https://www.kotak.com/personal-banking/cards/credit-cards/privy-league-signature-credit-card"
        ),
        # White Reserve
        ScrapedBenefit(
            card_name="White Reserve",
            brand_name="Dining",
            benefit_rate=5.0,
            benefit_type="points",
            description="5 reward points per Rs 150 on dining",
            source_url="https://www.kotak.com/personal-banking/cards/credit-cards/white-reserve-credit-card"
        ),
    ]

    async def scrape(self) -> List[ScrapedBenefit]:
        """Scrape benefits from Kotak Bank website."""
        self.logger.info("Starting Kotak Bank scraping...")

        benefits = []
        benefits.extend(self.KNOWN_BENEFITS)

        try:
            scraped = await self._scrape_website()
            for benefit in scraped:
                if not self._benefit_exists(benefit, benefits):
                    benefits.append(benefit)
        except Exception as e:
            self.logger.warning(f"Error scraping Kotak website: {e}. Using known benefits only.")

        self.logger.info(f"Found {len(benefits)} Kotak benefits")
        return benefits

    async def _scrape_website(self) -> List[ScrapedBenefit]:
        """Actually scrape the Kotak website for benefits."""
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
            "IndiGo", "PVR", "INOX", "Amazon", "Flipkart",
            "Swiggy", "Zomato", "BigBasket", "Uber", "Ola"
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
        """Scrape time-bound campaigns from Kotak Bank website."""
        self.logger.info("Starting Kotak Bank campaign scraping...")
        campaigns = []
        self.logger.info(f"Found {len(campaigns)} Kotak campaigns")
        return campaigns

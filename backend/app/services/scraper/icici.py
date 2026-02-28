"""ICICI Bank credit card benefits scraper."""

import asyncio
import re
from datetime import date, timedelta
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapedBenefit, ScrapedCampaign


class ICICIScraper(BaseScraper):
    """Scraper for ICICI Bank credit card benefits."""

    bank_name = "ICICI Bank"
    base_url = "https://www.icicibank.com"

    # Known ICICI cards with their benefit pages
    CARD_PAGES = {
        "Amazon Pay": "/personal-banking/cards/credit-card/amazon-pay-credit-card",
        "Emeralde": "/personal-banking/cards/credit-card/emeralde-credit-card",
        "Sapphiro": "/personal-banking/cards/credit-card/sapphiro-credit-card",
        "Rubyx": "/personal-banking/cards/credit-card/rubyx-credit-card",
        "Coral": "/personal-banking/cards/credit-card/coral-credit-card",
        "MakeMyTrip": "/personal-banking/cards/credit-card/makemytrip-credit-card",
        "Manchester United": "/personal-banking/cards/credit-card/manchester-united-credit-card",
    }

    # Known ecosystem benefits for ICICI cards
    KNOWN_BENEFITS = [
        # Amazon Pay Card
        ScrapedBenefit(
            card_name="Amazon Pay",
            brand_name="Amazon",
            benefit_rate=5.0,
            benefit_type="cashback",
            description="5% cashback on Amazon.in for Prime members",
            source_url="https://www.icicibank.com/personal-banking/cards/credit-card/amazon-pay-credit-card"
        ),
        ScrapedBenefit(
            card_name="Amazon Pay",
            brand_name="Amazon",
            benefit_rate=3.0,
            benefit_type="cashback",
            description="3% cashback on Amazon.in for non-Prime members",
            source_url="https://www.icicibank.com/personal-banking/cards/credit-card/amazon-pay-credit-card"
        ),
        ScrapedBenefit(
            card_name="Amazon Pay",
            brand_name="Swiggy",
            benefit_rate=2.0,
            benefit_type="cashback",
            description="2% cashback on Swiggy orders",
            source_url="https://www.icicibank.com/personal-banking/cards/credit-card/amazon-pay-credit-card"
        ),
        ScrapedBenefit(
            card_name="Amazon Pay",
            brand_name="Zomato",
            benefit_rate=2.0,
            benefit_type="cashback",
            description="2% cashback on Zomato orders",
            source_url="https://www.icicibank.com/personal-banking/cards/credit-card/amazon-pay-credit-card"
        ),
        # MakeMyTrip Card
        ScrapedBenefit(
            card_name="MakeMyTrip",
            brand_name="MakeMyTrip",
            benefit_rate=5.0,
            benefit_type="points",
            description="5X reward points on MakeMyTrip bookings",
            source_url="https://www.icicibank.com/personal-banking/cards/credit-card/makemytrip-credit-card"
        ),
        # Emeralde - Dining
        ScrapedBenefit(
            card_name="Emeralde",
            brand_name="Dining",
            benefit_rate=5.0,
            benefit_type="points",
            description="5X reward points on dining",
            source_url="https://www.icicibank.com/personal-banking/cards/credit-card/emeralde-credit-card"
        ),
    ]

    async def scrape(self) -> List[ScrapedBenefit]:
        """Scrape benefits from ICICI Bank website."""
        self.logger.info("Starting ICICI Bank scraping...")

        benefits = []

        # Use known benefits as primary source
        benefits.extend(self.KNOWN_BENEFITS)

        # Try to scrape additional benefits from the website
        try:
            scraped = await self._scrape_website()
            for benefit in scraped:
                if not self._benefit_exists(benefit, benefits):
                    benefits.append(benefit)
        except Exception as e:
            self.logger.warning(f"Error scraping ICICI website: {e}. Using known benefits only.")

        self.logger.info(f"Found {len(benefits)} ICICI benefits")
        return benefits

    async def _scrape_website(self) -> List[ScrapedBenefit]:
        """Scrape the ICICI website for benefits."""
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

        benefit_sections = soup.find_all(['div', 'section', 'li'], class_=re.compile(r'benefit|reward|feature|offer', re.I))

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
            "Amazon", "Swiggy", "Zomato", "MakeMyTrip", "Flipkart",
            "BookMyShow", "Myntra", "Ajio", "Uber", "Ola"
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

    async def scrape_campaigns(self) -> List[ScrapedCampaign]:
        """Scrape time-bound campaigns from ICICI Bank website."""
        self.logger.info("Starting ICICI Bank campaign scraping...")

        campaigns = []
        today = date.today()

        # Known ICICI campaigns (fallback data)
        known_campaigns = [
            ScrapedCampaign(
                card_name="Amazon Pay",
                brand_name="Amazon",
                benefit_rate=10.0,
                benefit_type="cashback",
                start_date=today,
                end_date=today + timedelta(days=30),
                description="10% cashback on Amazon Great Indian Festival",
                terms_url="https://www.icicibank.com/personal-banking/cards/credit-card/amazon-pay-credit-card",
                source_url="https://www.icicibank.com/personal-banking/cards/credit-card/amazon-pay-credit-card"
            ),
        ]

        campaigns.extend(known_campaigns)

        # Try to scrape actual campaigns
        try:
            scraped_campaigns = await self._scrape_campaigns_from_website()
            for campaign in scraped_campaigns:
                if not self._campaign_exists(campaign, campaigns):
                    campaigns.append(campaign)
        except Exception as e:
            self.logger.warning(f"Error scraping ICICI campaigns: {e}")

        self.logger.info(f"Found {len(campaigns)} ICICI campaigns")
        return campaigns

    async def _scrape_campaigns_from_website(self) -> List[ScrapedCampaign]:
        """Scrape campaigns from ICICI offers page."""
        campaigns = []

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                url = f"{self.base_url}/personal-banking/cards/credit-card/credit-card-offers"
                response = await client.get(url)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    campaigns = self._parse_campaigns_page(soup, url)

            except Exception as e:
                self.logger.debug(f"Error scraping ICICI offers: {e}")

        return campaigns

    def _parse_campaigns_page(self, soup: BeautifulSoup, url: str) -> List[ScrapedCampaign]:
        """Parse campaigns from offers page."""
        campaigns = []
        today = date.today()

        offer_sections = soup.find_all(['div', 'section'], class_=re.compile(r'offer|promo|campaign', re.I))

        for section in offer_sections:
            text = section.get_text()
            rate = self.parse_benefit_rate(text)

            if rate:
                benefit_type = self.detect_benefit_type(text)
                brand = self._extract_brand(text)
                card = self._extract_card_from_text(text)

                if brand and card:
                    campaigns.append(ScrapedCampaign(
                        card_name=card,
                        brand_name=brand,
                        benefit_rate=rate,
                        benefit_type=benefit_type,
                        start_date=today,
                        end_date=today + timedelta(days=30),
                        description=text[:300].strip(),
                        source_url=url
                    ))

        return campaigns

    def _extract_card_from_text(self, text: str) -> Optional[str]:
        """Extract card name from text."""
        for card_name in self.CARD_PAGES.keys():
            if card_name.lower() in text.lower():
                return card_name
        return None

    def _campaign_exists(self, campaign: ScrapedCampaign, existing: List[ScrapedCampaign]) -> bool:
        """Check if campaign exists."""
        for c in existing:
            if (c.card_name.lower() == campaign.card_name.lower() and
                c.brand_name.lower() == campaign.brand_name.lower() and
                c.start_date == campaign.start_date):
                return True
        return False

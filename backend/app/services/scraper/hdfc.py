"""HDFC Bank credit card benefits scraper."""

import asyncio
import re
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup

from .base import BaseScraper, ScrapedBenefit


class HDFCScraper(BaseScraper):
    """Scraper for HDFC Bank credit card benefits."""

    bank_name = "HDFC Bank"
    base_url = "https://www.hdfcbank.com"

    # Known HDFC cards with their benefit pages
    CARD_PAGES = {
        "Infinia": "/personal/pay/cards/credit-cards/infinia-credit-card",
        "Diners Club Black": "/personal/pay/cards/credit-cards/diners-club-black",
        "Diners Club Privilege": "/personal/pay/cards/credit-cards/diners-club-privilege",
        "Regalia Gold": "/personal/pay/cards/credit-cards/regalia-gold-credit-card",
        "Regalia": "/personal/pay/cards/credit-cards/regalia-credit-card",
        "Millennia": "/personal/pay/cards/credit-cards/millennia-credit-card",
        "MoneyBack+": "/personal/pay/cards/credit-cards/moneyback-plus-credit-card",
        "Tata Neu Plus": "/personal/pay/cards/credit-cards/tata-neu-plus-hdfc-bank-credit-card",
        "Tata Neu Infinity": "/personal/pay/cards/credit-cards/tata-neu-infinity-hdfc-bank-credit-card",
        "Marriott Bonvoy": "/personal/pay/cards/credit-cards/marriott-bonvoy-hdfc-bank-credit-card",
        "Swiggy": "/personal/pay/cards/credit-cards/swiggy-hdfc-bank-credit-card",
        "IndianOil": "/personal/pay/cards/credit-cards/indianoil-hdfc-bank-credit-card",
    }

    # Known ecosystem benefits for HDFC cards (fallback data)
    KNOWN_BENEFITS = [
        # Tata Neu Cards
        ScrapedBenefit(
            card_name="Tata Neu Plus",
            brand_name="Tata Group",
            benefit_rate=5.0,
            benefit_type="neucoins",
            description="5% NeuCoins on Tata Neu app purchases",
            source_url="https://www.hdfcbank.com/personal/pay/cards/credit-cards/tata-neu-plus-hdfc-bank-credit-card"
        ),
        ScrapedBenefit(
            card_name="Tata Neu Infinity",
            brand_name="Tata Group",
            benefit_rate=10.0,
            benefit_type="neucoins",
            description="10% NeuCoins on Tata Neu app purchases",
            source_url="https://www.hdfcbank.com/personal/pay/cards/credit-cards/tata-neu-infinity-hdfc-bank-credit-card"
        ),
        # Marriott Card
        ScrapedBenefit(
            card_name="Marriott Bonvoy",
            brand_name="Marriott",
            benefit_rate=8.0,
            benefit_type="points",
            description="8 Marriott Bonvoy points per INR 150 spent at Marriott properties",
            source_url="https://www.hdfcbank.com/personal/pay/cards/credit-cards/marriott-bonvoy-hdfc-bank-credit-card"
        ),
        # Swiggy Card
        ScrapedBenefit(
            card_name="Swiggy",
            brand_name="Swiggy",
            benefit_rate=10.0,
            benefit_type="cashback",
            description="10% cashback on Swiggy orders",
            source_url="https://www.hdfcbank.com/personal/pay/cards/credit-cards/swiggy-hdfc-bank-credit-card"
        ),
        # IndianOil Card
        ScrapedBenefit(
            card_name="IndianOil",
            brand_name="IndianOil",
            benefit_rate=5.0,
            benefit_type="points",
            description="5% value back on fuel purchases at IndianOil outlets",
            source_url="https://www.hdfcbank.com/personal/pay/cards/credit-cards/indianoil-hdfc-bank-credit-card"
        ),
        # Infinia - SmartBuy
        ScrapedBenefit(
            card_name="Infinia",
            brand_name="SmartBuy",
            benefit_rate=10.0,
            benefit_type="points",
            description="10X reward points on SmartBuy portal",
            source_url="https://www.hdfcbank.com/personal/pay/cards/credit-cards/infinia-credit-card"
        ),
        # Diners Club Black - SmartBuy
        ScrapedBenefit(
            card_name="Diners Club Black",
            brand_name="SmartBuy",
            benefit_rate=10.0,
            benefit_type="points",
            description="10X reward points on SmartBuy portal",
            source_url="https://www.hdfcbank.com/personal/pay/cards/credit-cards/diners-club-black"
        ),
    ]

    async def scrape(self) -> List[ScrapedBenefit]:
        """Scrape benefits from HDFC Bank website."""
        self.logger.info("Starting HDFC Bank scraping...")

        benefits = []

        # Use known benefits as primary source
        # In production, this would actually scrape the website
        benefits.extend(self.KNOWN_BENEFITS)

        # Try to scrape additional benefits from the website
        try:
            scraped = await self._scrape_website()
            # Merge scraped benefits with known benefits
            for benefit in scraped:
                if not self._benefit_exists(benefit, benefits):
                    benefits.append(benefit)
        except Exception as e:
            self.logger.warning(f"Error scraping HDFC website: {e}. Using known benefits only.")

        self.logger.info(f"Found {len(benefits)} HDFC benefits")
        return benefits

    async def _scrape_website(self) -> List[ScrapedBenefit]:
        """Actually scrape the HDFC website for benefits."""
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

                    # Be respectful of the server
                    await asyncio.sleep(1)

                except Exception as e:
                    self.logger.debug(f"Error scraping {card_name}: {e}")
                    continue

        return benefits

    def _parse_card_page(self, soup: BeautifulSoup, card_name: str, url: str) -> List[ScrapedBenefit]:
        """Parse a card page for benefits."""
        benefits = []

        # Look for benefit sections
        # This is a simplified parser - real implementation would be more robust
        benefit_sections = soup.find_all(['div', 'section'], class_=re.compile(r'benefit|reward|feature', re.I))

        for section in benefit_sections:
            text = section.get_text()

            # Look for percentage patterns
            rate = self.parse_benefit_rate(text)
            if rate:
                benefit_type = self.detect_benefit_type(text)

                # Try to identify the brand
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
            "Swiggy", "Zomato", "Amazon", "Flipkart", "BigBasket",
            "Tata Neu", "Marriott", "SmartBuy", "IndianOil", "BPCL",
            "HP Petrol", "Croma", "Westside", "Tanishq"
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

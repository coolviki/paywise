from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScrapedBenefit:
    """Represents a benefit scraped from a bank website."""
    card_name: str
    brand_name: str
    benefit_rate: float
    benefit_type: str  # cashback, points, miles, etc.
    description: Optional[str] = None
    source_url: Optional[str] = None


@dataclass
class ScrapedCampaign:
    """Represents a time-bound promotional campaign scraped from a bank website."""
    card_name: str
    brand_name: str
    benefit_rate: float
    benefit_type: str  # cashback, points, discount, etc.
    start_date: date
    end_date: date
    description: Optional[str] = None
    terms_url: Optional[str] = None
    source_url: Optional[str] = None


class BaseScraper(ABC):
    """Base class for bank website scrapers."""

    bank_name: str = "Unknown"
    base_url: str = ""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def scrape(self) -> List[ScrapedBenefit]:
        """
        Scrape benefits from the bank website.
        Returns a list of ScrapedBenefit objects.
        """
        pass

    async def scrape_campaigns(self) -> List[ScrapedCampaign]:
        """
        Scrape time-bound promotional campaigns from the bank website.
        Returns a list of ScrapedCampaign objects.
        Override in subclasses to implement campaign scraping.
        """
        return []

    def normalize_card_name(self, name: str) -> str:
        """
        Normalize card name for matching.
        Removes common prefixes/suffixes to identify duplicate cards.
        E.g., "ICICI Coral Credit Card" and "ICICI Coral" become "Coral"
        """
        import re

        name = name.strip()

        # Remove bank name prefixes
        bank_prefixes = [
            "HDFC Bank", "HDFC", "ICICI Bank", "ICICI",
            "SBI Card", "SBI", "Axis Bank", "Axis",
            "Kotak Mahindra", "Kotak", "RBL Bank", "RBL",
            "IndusInd Bank", "IndusInd", "Yes Bank", "Yes",
            "IDFC First", "IDFC", "American Express", "Amex"
        ]
        for prefix in bank_prefixes:
            if name.upper().startswith(prefix.upper()):
                name = name[len(prefix):].strip()

        # Remove common suffixes
        suffixes_to_remove = [
            "Credit Card", "Debit Card", "Card",
            "Visa", "Mastercard", "RuPay", "Rupay"
        ]
        for suffix in suffixes_to_remove:
            if name.upper().endswith(suffix.upper()):
                name = name[:-len(suffix)].strip()

        # Clean up any leftover whitespace or hyphens at edges
        name = re.sub(r'^[\s\-]+|[\s\-]+$', '', name)

        return name

    def get_canonical_card_name(self, name: str) -> str:
        """
        Get canonical card name for deduplication.
        Returns a standardized form that can be used for comparison.
        """
        normalized = self.normalize_card_name(name).lower()
        # Replace multiple spaces/hyphens with single space
        import re
        normalized = re.sub(r'[\s\-_]+', ' ', normalized)
        return normalized.strip()

    def normalize_brand_name(self, name: str) -> str:
        """Normalize brand name for matching."""
        return name.strip().lower()

    def parse_benefit_rate(self, text: str) -> Optional[float]:
        """Extract benefit rate from text like '5% cashback' or '10X points'."""
        import re

        # Try to find percentage
        match = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
        if match:
            return float(match.group(1))

        # Try to find multiplier (e.g., 10X = 10%)
        match = re.search(r'(\d+(?:\.\d+)?)\s*[xX]', text)
        if match:
            return float(match.group(1))

        return None

    def detect_benefit_type(self, text: str) -> str:
        """Detect the type of benefit from text."""
        text_lower = text.lower()

        if 'cashback' in text_lower or 'cash back' in text_lower:
            return 'cashback'
        elif 'point' in text_lower or 'reward' in text_lower:
            return 'points'
        elif 'mile' in text_lower:
            return 'miles'
        elif 'neucoin' in text_lower:
            return 'neucoins'
        elif 'discount' in text_lower:
            return 'discount'

        return 'cashback'  # Default

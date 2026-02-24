from abc import ABC, abstractmethod
from dataclasses import dataclass
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

    def normalize_card_name(self, name: str) -> str:
        """Normalize card name for matching."""
        # Remove common prefixes/suffixes
        name = name.strip()
        # Remove bank name prefix if present
        for prefix in ["HDFC Bank", "HDFC", "ICICI Bank", "ICICI", "SBI Card", "SBI"]:
            if name.upper().startswith(prefix.upper()):
                name = name[len(prefix):].strip()
        return name

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

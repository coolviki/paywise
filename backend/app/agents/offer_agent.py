from typing import Optional, List, Dict, Any
import json
from .base_agent import BaseAgent


class OfferAgent(BaseAgent):
    """Agent for extracting and analyzing offers from bank pages."""

    SYSTEM_PROMPT = """You are an expert at extracting credit card offer information from bank websites.
Extract all relevant offers and return them in a structured JSON format.
Be precise with numbers, dates, and terms."""

    async def extract_offers(
        self,
        bank_name: str,
        page_content: str,
    ) -> List[Dict[str, Any]]:
        """Extract offers from bank page content."""
        prompt = f"""Extract credit card offers from this {bank_name} page content:

{page_content[:8000]}  # Truncate to fit context

Return a JSON array of offers with this structure:
{{
  "offers": [
    {{
      "card_name": "string",
      "merchant_name": "string or null",
      "category": "string or null",
      "discount_type": "percentage|flat|cashback|points",
      "discount_value": number,
      "min_transaction": number or null,
      "max_discount": number or null,
      "valid_from": "YYYY-MM-DD or null",
      "valid_until": "YYYY-MM-DD or null",
      "terms": "string"
    }}
  ]
}}

Only return valid JSON, no other text."""

        response = await self.call_llm(
            prompt,
            system_prompt=self.SYSTEM_PROMPT,
            max_tokens=4096,
        )

        if not response:
            return []

        try:
            # Try to parse the JSON response
            data = json.loads(response)
            return data.get("offers", [])
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            try:
                start = response.find("{")
                end = response.rfind("}") + 1
                if start >= 0 and end > start:
                    data = json.loads(response[start:end])
                    return data.get("offers", [])
            except Exception:
                pass

        return []

    async def categorize_merchant(self, merchant_name: str) -> Optional[str]:
        """Categorize a merchant using LLM."""
        prompt = f"""What category does "{merchant_name}" belong to?

Choose from: Food & Dining, Grocery, Shopping, Travel, Entertainment, Fuel, Healthcare, Utilities, Education, Other

Return only the category name, nothing else."""

        response = await self.call_llm(prompt, max_tokens=50)

        if response:
            return response.strip()

        return None

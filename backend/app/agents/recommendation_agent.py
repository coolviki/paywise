from typing import Optional, List, Dict, Any
import json
from .base_agent import BaseAgent
from ..models.card import PaymentMethod


class RecommendationAgent(BaseAgent):
    """Agent for generating payment recommendations using LLM."""

    SYSTEM_PROMPT = """PayWise: India credit card expert. Recommend the card that gives the highest real value to the user.
IMPORTANT: If a card has an ecosystem_benefit_rate for this merchant, that rate overrides its base_reward_rate — always prefer ecosystem benefits over generic rates.
JSON only, be brief."""

    # Category mapping for better context
    CATEGORY_HINTS = {
        "restaurant": "dining",
        "cafe": "dining",
        "bar": "dining",
        "food": "dining",
        "bakery": "dining",
        "gas_station": "fuel",
        "fuel": "fuel",
        "petrol": "fuel",
        "grocery": "grocery",
        "supermarket": "grocery",
        "store": "shopping",
        "mall": "shopping",
        "shopping": "shopping",
        "clothing": "shopping",
        "electronics": "shopping",
        "airport": "travel",
        "hotel": "travel",
        "travel": "travel",
        "airline": "travel",
    }

    @staticmethod
    def get_category_type(place_category: Optional[str]) -> str:
        """Map Google Places category to reward category."""
        if not place_category:
            return "general"
        cat_lower = place_category.lower()
        for keyword, category_type in RecommendationAgent.CATEGORY_HINTS.items():
            if keyword in cat_lower:
                return category_type
        return "general"

    @staticmethod
    async def get_recommendation(
        place_name: str,
        place_category: Optional[str],
        payment_methods: List[PaymentMethod],
        transaction_amount: Optional[float] = None,
        ecosystem_benefits: Optional[Dict[str, dict]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get LLM-based recommendation for the best card to use."""
        agent = RecommendationAgent()

        if not agent.client:
            return None

        ecosystem_benefits = ecosystem_benefits or {}

        # Build card list for the prompt, injecting ecosystem benefits where present
        cards_info = []
        for pm in payment_methods:
            if pm.card:
                card_id_str = str(pm.card_id)
                card_info: Dict[str, Any] = {
                    "id": card_id_str,
                    "name": pm.card.name,
                    "bank": pm.card.bank.name if pm.card.bank else "Unknown",
                    "type": pm.card.card_type,
                    "reward_type": pm.card.reward_type,
                    "base_reward_rate": float(pm.card.base_reward_rate) if pm.card.base_reward_rate else None,
                }
                # Inject ecosystem benefit when this card has one for the merchant's brand
                benefit = ecosystem_benefits.get(card_id_str)
                if benefit:
                    card_info["ecosystem_benefit_rate"] = benefit["benefit_rate"]
                    card_info["ecosystem_benefit_type"] = benefit["benefit_type"]
                    card_info["ecosystem_benefit_note"] = benefit["description"]
                cards_info.append(card_info)

        if not cards_info:
            return None

        amount_str = f"Rs.{transaction_amount:.0f}" if transaction_amount else "a typical purchase"
        category_type = RecommendationAgent.get_category_type(place_category)

        # Add an explicit ecosystem context line when relevant
        ecosystem_note = ""
        if ecosystem_benefits:
            sample = next(iter(ecosystem_benefits.values()))
            ecosystem_note = f"\nNote: {place_name} is a {sample['brand_name']} property. Cards with ecosystem_benefit_rate earn that rate here instead of their base rate."

        prompt = f"""{category_type.upper()}: {place_name}, {amount_str}{ecosystem_note}
Cards:{json.dumps(cards_info)}
Reply with ONLY this JSON (no offers array, keep reason under 10 words):
{{"best_card":{{"card_id":"id","estimated_savings":"Rs.X","reason":"short {category_type} reason"}},"insight":"tip"}}"""

        try:
            response = await agent.call_llm(prompt, system_prompt=RecommendationAgent.SYSTEM_PROMPT)

            if not response:
                print("LLM returned empty response")
                return None

            # Try to parse JSON from response
            # Handle markdown code blocks if present
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            # Try to fix truncated JSON by adding closing braces
            try:
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                # Try to fix truncated JSON
                fixed = response
                # Count open/close braces
                open_braces = fixed.count('{') - fixed.count('}')
                open_brackets = fixed.count('[') - fixed.count(']')

                # Add missing closing brackets/braces
                fixed += ']' * open_brackets
                fixed += '}' * open_braces

                # Remove trailing comma before closing brace
                fixed = fixed.replace(',]', ']').replace(',}', '}')

                try:
                    result = json.loads(fixed)
                    print(f"Fixed truncated JSON successfully")
                    return result
                except json.JSONDecodeError as e:
                    print(f"Failed to parse LLM response as JSON: {e}")
                    print(f"Raw response: {response[:200]}...")
                    return None

        except Exception as e:
            print(f"LLM recommendation failed: {e}")
            return None

    @staticmethod
    async def generate_insight(
        place_name: str,
        best_card_name: str,
        best_card_bank: str,
        savings: str,
    ) -> Optional[str]:
        """Generate a brief AI insight (fallback method)."""
        agent = RecommendationAgent()

        if not agent.client:
            return f"Use {best_card_name} from {best_card_bank} at {place_name} to save {savings}."

        prompt = f"""Generate a brief, helpful 1-sentence tip for using {best_card_name} ({best_card_bank}) at {place_name} with estimated savings of {savings}.
Be conversational and mention any relevant tips like using mobile wallets, checking for additional coupons, or timing purchases."""

        response = await agent.call_llm(prompt, system_prompt=RecommendationAgent.SYSTEM_PROMPT, max_tokens=100)
        return response.strip() if response else None

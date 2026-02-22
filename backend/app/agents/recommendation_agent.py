from typing import Optional, List, Dict, Any
import json
from .base_agent import BaseAgent
from ..models.card import PaymentMethod


class RecommendationAgent(BaseAgent):
    """Agent for generating payment recommendations using LLM."""

    SYSTEM_PROMPT = """You are PayWise. Help users pick the best credit card for purchases in India. Be very concise. Return valid JSON only."""

    @staticmethod
    async def get_recommendation(
        place_name: str,
        place_category: Optional[str],
        payment_methods: List[PaymentMethod],
        transaction_amount: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get LLM-based recommendation for the best card to use."""
        agent = RecommendationAgent()

        if not agent.client:
            return None

        # Build card list for the prompt
        cards_info = []
        for pm in payment_methods:
            if pm.card:
                card_info = {
                    "id": str(pm.card_id),
                    "name": pm.card.name,
                    "bank": pm.card.bank.name if pm.card.bank else "Unknown",
                    "type": pm.card.card_type,
                    "reward_type": pm.card.reward_type,
                    "base_reward_rate": float(pm.card.base_reward_rate) if pm.card.base_reward_rate else None,
                }
                cards_info.append(card_info)

        if not cards_info:
            return None

        amount_str = f"Rs.{transaction_amount:.0f}" if transaction_amount else "a typical purchase"

        prompt = f"""Best card for {place_name} ({place_category or 'retail'}), {amount_str}?
Cards: {json.dumps(cards_info)}
JSON response (keep reason under 20 words):
{{"best_card":{{"card_id":"id","estimated_savings":"Rs.X","reason":"brief why","offers":[]}},"alternatives":[],"insight":"short tip"}}"""

        try:
            response = await agent.call_llm(prompt, system_prompt=RecommendationAgent.SYSTEM_PROMPT)

            if not response:
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

            result = json.loads(response.strip())
            return result

        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response as JSON: {e}")
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

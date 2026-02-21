from typing import Optional, List, Dict, Any
import json
from .base_agent import BaseAgent
from ..models.card import PaymentMethod


class RecommendationAgent(BaseAgent):
    """Agent for generating payment recommendations using LLM."""

    SYSTEM_PROMPT = """You are PayWise, an AI assistant that helps users in India choose the best payment method for their purchases.

You have knowledge of current credit card offers, cashback deals, and reward programs from major Indian banks including:
- HDFC Bank (Regalia, Diners Club, Infinia, etc.)
- ICICI Bank (Amazon Pay, Coral, Sapphiro, etc.)
- SBI Cards (SimplyCLICK, Prime, Elite, etc.)
- Axis Bank (Flipkart, Magnus, Vistara, etc.)
- Kotak Bank, Yes Bank, IndusInd Bank, IDFC First Bank, American Express, etc.

When recommending a card, consider:
1. Current offers and promotions at the merchant
2. Category-specific rewards (dining, groceries, fuel, travel, etc.)
3. Bank partnerships with the merchant
4. Cashback rates and reward point values
5. Milestone benefits and accelerated rewards

Always respond in the exact JSON format requested."""

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

        prompt = f"""Analyze the best payment card to use at "{place_name}" ({place_category or 'retail'}) for {amount_str}.

User's available cards:
{json.dumps(cards_info, indent=2)}

Respond with a JSON object in this exact format:
{{
    "best_card": {{
        "card_id": "<id of the best card>",
        "estimated_savings": "<e.g., 'Rs.150' or '5% cashback'>",
        "reason": "<brief reason why this card is best>",
        "offers": ["<list of current offers/deals applicable>"]
    }},
    "alternatives": [
        {{
            "card_id": "<id>",
            "estimated_savings": "<savings>",
            "reason": "<reason>",
            "offers": []
        }}
    ],
    "insight": "<1-2 sentence personalized tip for maximizing savings>"
}}

Consider current bank offers, category rewards, and partnerships. Provide realistic savings estimates based on typical offers in India."""

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

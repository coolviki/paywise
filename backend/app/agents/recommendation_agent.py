from typing import Optional, List
from .base_agent import BaseAgent
from ..models.merchant import Merchant
from ..schemas.recommendation import CardRecommendation


class RecommendationAgent(BaseAgent):
    """Agent for generating payment recommendations and insights."""

    SYSTEM_PROMPT = """You are PayWise, an AI assistant that helps users choose the best payment method
for their purchases in India. You provide concise, helpful insights about credit card rewards and offers.
Keep your responses brief (1-2 sentences) and focus on the key benefit for the user."""

    @staticmethod
    async def generate_insight(
        merchant: Merchant,
        best_option: CardRecommendation,
        alternatives: List[CardRecommendation],
    ) -> Optional[str]:
        """Generate an AI insight about the recommendation."""
        agent = RecommendationAgent()

        prompt = f"""Generate a brief, helpful insight for this payment recommendation:

Merchant: {merchant.name}
Category: {merchant.category.name if merchant.category else 'General'}

Best Option: {best_option.card_name} from {best_option.bank_name}
- Estimated savings: {best_option.estimated_savings}
- Reason: {best_option.reason}

Alternatives:
"""
        for alt in alternatives:
            prompt += f"- {alt.card_name}: {alt.estimated_savings} ({alt.reason})\n"

        prompt += """
Provide a 1-2 sentence insight explaining why the recommended card is the best choice
and any tips for maximizing savings. Be conversational and helpful."""

        response = await agent.call_llm(prompt, system_prompt=RecommendationAgent.SYSTEM_PROMPT)

        if response:
            return response.strip()

        # Fallback insight
        return f"{best_option.card_name} offers the best value at {merchant.name} with {best_option.reason}."

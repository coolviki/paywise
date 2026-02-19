from typing import Optional
import anthropic
from ..core.config import settings


class BaseAgent:
    """Base class for LLM agents."""

    def __init__(self):
        self.client = None
        if settings.anthropic_api_key:
            self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.llm_model

    async def call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
    ) -> Optional[str]:
        """Call the LLM with the given prompt."""
        if not self.client:
            return None

        messages = [{"role": "user", "content": prompt}]

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt or "",
                messages=messages,
            )

            if response.content:
                return response.content[0].text

            return None

        except Exception as e:
            print(f"LLM call failed: {e}")
            return None

from typing import Optional
import google.generativeai as genai
from ..core.config import settings


class BaseAgent:
    """Base class for LLM agents using Google Gemini."""

    def __init__(self):
        self.client = None
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            self.client = genai.GenerativeModel(settings.llm_model)
        self.model = settings.llm_model

    async def call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
    ) -> Optional[str]:
        """Call the Gemini LLM with the given prompt."""
        if not self.client:
            return None

        try:
            # Combine system prompt and user prompt for Gemini
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            response = self.client.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.7,
                )
            )

            if response.text:
                return response.text

            return None

        except Exception as e:
            print(f"LLM call failed: {e}")
            return None

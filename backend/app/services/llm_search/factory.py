"""
Factory for creating LLM search providers based on configuration.
"""

from typing import Optional
from enum import Enum

from .base import LLMSearchProvider
from .perplexity import PerplexityProvider
from .tavily import TavilyProvider


class LLMSearchProviderType(str, Enum):
    PERPLEXITY = "perplexity"
    TAVILY = "tavily"


# Singleton instance
_provider_instance: Optional[LLMSearchProvider] = None


def get_llm_search_provider(
    provider_type: Optional[str] = None,
    perplexity_api_key: Optional[str] = None,
    tavily_api_key: Optional[str] = None,
    gemini_api_key: Optional[str] = None,
) -> Optional[LLMSearchProvider]:
    """
    Get or create an LLM search provider instance.

    Args:
        provider_type: "perplexity" or "tavily" (auto-detected if not specified)
        perplexity_api_key: Perplexity API key
        tavily_api_key: Tavily API key
        gemini_api_key: Gemini API key (required for Tavily)

    Returns:
        LLMSearchProvider instance or None if no valid configuration
    """
    global _provider_instance

    # Return cached instance if available
    if _provider_instance is not None:
        return _provider_instance

    # Load from environment if keys not provided
    if not any([perplexity_api_key, tavily_api_key]):
        from ...core.config import settings
        perplexity_api_key = getattr(settings, "perplexity_api_key", None)
        tavily_api_key = getattr(settings, "tavily_api_key", None)
        gemini_api_key = gemini_api_key or getattr(settings, "gemini_api_key", None)

    # Auto-detect provider type based on available keys
    if provider_type is None:
        if perplexity_api_key:
            provider_type = LLMSearchProviderType.PERPLEXITY
        elif tavily_api_key and gemini_api_key:
            provider_type = LLMSearchProviderType.TAVILY
        else:
            return None

    # Create provider
    if provider_type == LLMSearchProviderType.PERPLEXITY or provider_type == "perplexity":
        if not perplexity_api_key:
            raise ValueError("Perplexity API key required for Perplexity provider")
        _provider_instance = PerplexityProvider(api_key=perplexity_api_key)

    elif provider_type == LLMSearchProviderType.TAVILY or provider_type == "tavily":
        if not tavily_api_key or not gemini_api_key:
            raise ValueError("Both Tavily and Gemini API keys required for Tavily provider")
        _provider_instance = TavilyProvider(
            tavily_api_key=tavily_api_key,
            gemini_api_key=gemini_api_key,
        )

    else:
        raise ValueError(f"Unknown provider type: {provider_type}")

    return _provider_instance


def reset_provider():
    """Reset the cached provider instance (useful for testing)."""
    global _provider_instance
    _provider_instance = None

"""
Provider-agnostic LLM search service for fetching restaurant offers.
Supports multiple providers: Perplexity, Tavily, OpenAI, etc.
"""

from .base import LLMSearchProvider, RestaurantOffer
from .factory import get_llm_search_provider

__all__ = ["LLMSearchProvider", "RestaurantOffer", "get_llm_search_provider"]

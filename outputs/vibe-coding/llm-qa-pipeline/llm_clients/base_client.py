"""Base LLM client with token tracking."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from core.cache_manager import CacheManager
from core.token_tracker import track_tokens


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients with token tracking."""

    def __init__(self, api_name: str):
        self.api_name = api_name
        self.cache = CacheManager()

    @abstractmethod
    def generate_content(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate content using the LLM.

        Args:
            prompt: The prompt to send to the LLM
            **kwargs: Additional arguments specific to the API

        Returns:
            A dictionary containing:
            - 'response': The generated content
            - 'input_tokens': Number of input tokens
            - 'output_tokens': Number of output tokens
            - 'cache_hit': Whether this was a cache hit
            - 'status': 'success' or 'failed'
        """
        pass

    def _prepare_response(
        self,
        response: Any,
        input_tokens: int,
        output_tokens: int,
        cache_hit: bool = False,
        status: str = "success",
    ) -> Dict[str, Any]:
        """
        Prepare a standardized response.

        Args:
            response: The actual response from the API
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cache_hit: Whether this was a cache hit
            status: Response status

        Returns:
            Standardized response dictionary
        """
        return {
            "response": response,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_hit": cache_hit,
            "status": status,
        }

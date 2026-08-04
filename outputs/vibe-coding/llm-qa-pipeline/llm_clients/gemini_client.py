"""Gemini API client with token tracking and caching."""

from typing import Dict, Any, Optional
from google import genai
from llm_clients.base_client import BaseLLMClient
from core.token_tracker import track_tokens
from utils.config import Config


class GeminiClient(BaseLLMClient):
    """Gemini API client with built-in token tracking and caching."""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__("gemini")
        self.api_key = api_key or Config.GEMINI_API_KEY
        self.client = genai.Client(api_key=self.api_key)
        self.model = Config.GEMINI_MODEL

    @track_tokens(api="gemini", model="gemini-2.0-flash")
    def generate_content(
        self,
        prompt: str,
        model: Optional[str] = None,
        use_cache: bool = True,
        tc_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate content using Gemini API with caching.

        Args:
            prompt: The prompt to send
            model: Model name (default: gemini-2.0-flash)
            use_cache: Whether to use caching (default: True)
            tc_id: Optional test case ID for tracking

        Returns:
            Standardized response with token counts
        """
        model = model or self.model

        # Try to get from cache
        if use_cache:
            prompt_hash = self.cache.hash_prompt(prompt)
            cached_result = self.cache.get_eval_result(prompt_hash)

            if cached_result:
                return self._prepare_response(
                    response=cached_result.get("response"),
                    input_tokens=cached_result.get("input_tokens", 0),
                    output_tokens=cached_result.get("output_tokens", 0),
                    cache_hit=True,
                    status="success",
                ) | {"tc_id": tc_id}

        try:
            # Call Gemini API
            response = self.client.models.generate_content(
                model=model,
                contents=prompt,
            )

            # Extract token counts
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count

            response_text = response.text

            # Save to cache if enabled
            if use_cache:
                prompt_hash = self.cache.hash_prompt(prompt)
                self.cache.save_eval_result(
                    prompt_hash,
                    {
                        "response": response_text,
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                    },
                )

            return self._prepare_response(
                response=response_text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_hit=False,
                status="success",
            ) | {"tc_id": tc_id}

        except Exception as e:
            return {
                "response": None,
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_hit": False,
                "status": "failed",
                "error": str(e),
                "tc_id": tc_id,
            }

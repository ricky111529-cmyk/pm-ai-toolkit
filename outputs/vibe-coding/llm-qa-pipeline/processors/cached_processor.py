"""Processor that prioritizes cache usage."""

from typing import Dict, Any

from processors.base_processor import BaseProcessor


class CachedProcessor(BaseProcessor):
    """
    Processor that checks cache first, then runs evaluation if needed.

    This is ideal for 'summary' requests where we want to reuse
    previous results when available.
    """

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process request with cache priority.

        Args:
            request: Request with 'tc_id' and 'payload'

        Returns:
            Cached or newly computed result
        """
        tc_id = request.get("tc_id")
        payload = request.get("payload", {})

        # Check cache
        cached_result = self.cache.get_tc_result(tc_id)
        if cached_result:
            return {
                "tc_id": tc_id,
                "result": cached_result,
                "cache_hit": True,
                "source": "cache",
            }

        # No cache, run evaluation (this would be implemented in a subclass
        # that knows how to evaluate, but for now we return a placeholder)
        return {
            "tc_id": tc_id,
            "result": None,
            "cache_hit": False,
            "source": "evaluation",
            "message": "Evaluation not implemented in CachedProcessor",
        }

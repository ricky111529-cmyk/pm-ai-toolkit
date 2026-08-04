"""Processor that always runs fresh evaluations."""

from typing import Dict, Any

from processors.base_processor import BaseProcessor


class RealTimeProcessor(BaseProcessor):
    """
    Processor that always runs fresh evaluation, ignoring cache.

    This is ideal for 'analysis' requests where we need current,
    uncached results.
    """

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process request with fresh evaluation (no cache).

        Args:
            request: Request with 'tc_id' and 'payload'

        Returns:
            Fresh evaluation result
        """
        tc_id = request.get("tc_id")
        payload = request.get("payload", {})

        # Always run evaluation (this would be implemented in a subclass
        # that knows how to evaluate, but for now we return a placeholder)
        return {
            "tc_id": tc_id,
            "result": None,
            "cache_hit": False,
            "source": "real_time_evaluation",
            "message": "Evaluation not implemented in RealTimeProcessor",
        }

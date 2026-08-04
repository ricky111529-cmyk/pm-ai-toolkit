"""Processor for summary-only evaluations."""

from typing import Dict, Any

from processors.base_processor import BaseProcessor


class SummaryProcessor(BaseProcessor):
    """
    Processor for 'summary' requests that only evaluate key aspects.

    This processor can run fewer evaluations than a full analysis
    to reduce token usage while still providing useful insights.
    """

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process request with limited evaluation scope.

        Args:
            request: Request with 'tc_id' and 'payload'

        Returns:
            Summary evaluation result
        """
        tc_id = request.get("tc_id")
        payload = request.get("payload", {})

        # Run limited evaluation (only key aspects)
        return {
            "tc_id": tc_id,
            "result": None,
            "evaluation_scope": "summary",
            "source": "summary_evaluation",
            "message": "Summary evaluation not implemented in SummaryProcessor",
        }

"""Logging and token tracking utilities."""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from utils.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class TokenLogger:
    """Log and track token usage across API calls."""

    def __init__(self):
        self.config = Config
        self.metrics_file = self.config.get_metrics_file()
        self.logger = logging.getLogger("TokenTracker")

    def log_token_usage(
        self,
        api: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        tc_id: Optional[str] = None,
        processor_type: str = "unknown",
        cache_hit: bool = False,
        latency_ms: int = 0,
        status: str = "success",
    ) -> None:
        """
        Log a token usage event.

        Args:
            api: API name (e.g., 'gemini', 'aip')
            model: Model name (e.g., 'gemini-2.0-flash')
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            tc_id: Test case ID (optional)
            processor_type: Processor type (cached, real_time, etc.)
            cache_hit: Whether this was a cache hit
            latency_ms: Response latency in milliseconds
            status: Status (success, failed, etc.)
        """
        total_tokens = input_tokens + output_tokens

        # Calculate cost (Gemini pricing as of 2026)
        cost = self._calculate_cost(api, model, input_tokens, output_tokens)

        # Create log entry
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "api": api,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "cost_usd": round(cost, 6),
            "tc_id": tc_id,
            "processor_type": processor_type,
            "cache_hit": cache_hit,
            "latency_ms": latency_ms,
            "status": status,
        }

        # Append to metrics file
        self._append_to_metrics(entry)

        # Log to console
        self.logger.info(
            f"[{api}] {model} | input:{input_tokens} output:{output_tokens} "
            f"total:{total_tokens} cost:${cost:.6f} cache_hit:{cache_hit}"
        )

    def _calculate_cost(self, api: str, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate API cost based on token counts."""
        # Gemini 2.0 Flash pricing (as of 2026)
        if api == "gemini" and "2.0-flash" in model:
            # Input: $0.075 per 1M tokens
            # Output: $0.30 per 1M tokens
            input_cost = (input_tokens / 1_000_000) * 0.075
            output_cost = (output_tokens / 1_000_000) * 0.30
            return input_cost + output_cost
        return 0.0

    def _append_to_metrics(self, entry: Dict[str, Any]) -> None:
        """Append a token usage entry to the metrics file."""
        try:
            # Read existing metrics
            if self.metrics_file.exists():
                with open(self.metrics_file, "r") as f:
                    metrics = json.load(f)
            else:
                metrics = {"entries": []}

            # Append new entry
            if "entries" not in metrics:
                metrics["entries"] = []
            metrics["entries"].append(entry)

            # Write back
            with open(self.metrics_file, "w") as f:
                json.dump(metrics, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to write metrics: {e}")

    def get_daily_summary(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get a summary of token usage for a specific day."""
        if date is None:
            date = datetime.utcnow().date().isoformat()

        if not self.metrics_file.exists():
            return {"date": date, "apis": {}, "summary": {}}

        with open(self.metrics_file, "r") as f:
            metrics = json.load(f)

        entries = metrics.get("entries", [])

        # Filter by date
        daily_entries = [
            e for e in entries
            if e["timestamp"].startswith(date)
        ]

        # Aggregate by API
        summary = {"date": date, "apis": {}, "summary": {}}

        total_tokens = 0
        total_cost = 0
        total_calls = 0
        cache_hits = 0

        for entry in daily_entries:
            api = entry["api"]

            if api not in summary["apis"]:
                summary["apis"][api] = {
                    "total_tokens": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_cost_usd": 0.0,
                    "call_count": 0,
                    "cache_hits": 0,
                    "cache_hit_rate": 0.0,
                }

            api_summary = summary["apis"][api]
            api_summary["total_tokens"] += entry["total_tokens"]
            api_summary["input_tokens"] += entry["input_tokens"]
            api_summary["output_tokens"] += entry["output_tokens"]
            api_summary["total_cost_usd"] += entry["cost_usd"]
            api_summary["call_count"] += 1

            if entry["cache_hit"]:
                api_summary["cache_hits"] += 1
                cache_hits += 1

            total_tokens += entry["total_tokens"]
            total_cost += entry["cost_usd"]
            total_calls += 1

        # Calculate cache hit rates
        for api_data in summary["apis"].values():
            if api_data["call_count"] > 0:
                api_data["cache_hit_rate"] = round(
                    api_data["cache_hits"] / api_data["call_count"], 3
                )

        # Overall summary
        summary["summary"] = {
            "total_tokens_all_apis": total_tokens,
            "total_cost_usd": round(total_cost, 6),
            "total_calls": total_calls,
            "cache_hit_rate": round(cache_hits / total_calls, 3) if total_calls > 0 else 0.0,
        }

        return summary

    def print_summary(self, date: Optional[str] = None) -> None:
        """Print a formatted summary of token usage."""
        summary = self.get_daily_summary(date)

        date_str = summary["date"]
        print(f"\n{'Token Usage Summary':<50} ({date_str})")
        print("=" * 70)

        for api, data in summary["apis"].items():
            print(f"\n{api.upper()}")
            print("-" * 70)
            print(f"  Total Tokens:      {data['total_tokens']:>15,}")
            print(f"  Input Tokens:      {data['input_tokens']:>15,}")
            print(f"  Output Tokens:     {data['output_tokens']:>15,}")
            print(f"  Total Cost:        ${data['total_cost_usd']:>14.6f}")
            print(f"  Call Count:        {data['call_count']:>15}")
            print(f"  Cache Hit Rate:    {data['cache_hit_rate']*100:>14.1f}%")

        print("\n" + "=" * 70)
        print(f"{'OVERALL SUMMARY':<50}")
        print("-" * 70)
        overall = summary["summary"]
        print(f"  Total Tokens:      {overall['total_tokens_all_apis']:>15,}")
        print(f"  Total Cost:        ${overall['total_cost_usd']:>14.6f}")
        print(f"  Total Calls:       {overall['total_calls']:>15}")
        print(f"  Cache Hit Rate:    {overall['cache_hit_rate']*100:>14.1f}%")
        print("=" * 70)

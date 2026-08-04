"""Token tracking decorator and utilities."""

import time
import functools
from typing import Callable, Optional, Any
from utils.logger import TokenLogger

# Global token logger instance
_token_logger = TokenLogger()


def track_tokens(
    api: str,
    model: str,
    processor_type: str = "unknown"
) -> Callable:
    """
    Decorator to track token usage for API calls.

    Args:
        api: API name (e.g., 'gemini', 'aip')
        model: Model name (e.g., 'gemini-2.0-flash')
        processor_type: Type of processor (cached, real_time, etc.)

    Example:
        @track_tokens(api='gemini', model='gemini-2.0-flash')
        def evaluate_storyline(payload):
            response = gemini_client.generate_content(...)
            return {'input_tokens': 1200, 'output_tokens': 450, ...}
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()

            # Call the original function
            result = func(*args, **kwargs)

            # Extract token counts from result
            input_tokens = result.get("input_tokens", 0) if isinstance(result, dict) else 0
            output_tokens = result.get("output_tokens", 0) if isinstance(result, dict) else 0
            tc_id = result.get("tc_id") if isinstance(result, dict) else None
            cache_hit = result.get("cache_hit", False) if isinstance(result, dict) else False
            status = result.get("status", "success") if isinstance(result, dict) else "success"

            # Calculate latency
            latency_ms = int((time.time() - start_time) * 1000)

            # Log the token usage
            _token_logger.log_token_usage(
                api=api,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                tc_id=tc_id,
                processor_type=processor_type,
                cache_hit=cache_hit,
                latency_ms=latency_ms,
                status=status,
            )

            return result

        return wrapper
    return decorator


def get_token_logger() -> TokenLogger:
    """Get the global token logger instance."""
    return _token_logger

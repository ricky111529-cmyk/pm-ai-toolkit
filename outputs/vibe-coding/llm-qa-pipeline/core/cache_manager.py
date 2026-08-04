"""Cache management for prompts and evaluation results."""

import hashlib
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any

from utils.config import Config


class CacheManager:
    """Manage caching of prompts and results to reduce API calls."""

    def __init__(self):
        self.config = Config
        self.config.ensure_directories()
        self.prompts_cache_dir = self.config.get_cache_prompts_dir()
        self.results_cache_dir = self.config.get_cache_results_dir()
        self.cache_enabled = self.config.CACHE_ENABLED
        self.cache_expiry_hours = self.config.CACHE_EXPIRY_HOURS

    def hash_prompt(self, content: str) -> str:
        """Generate a hash for a prompt."""
        return hashlib.sha256(content.encode()).hexdigest()

    def get_eval_result(self, prompt_hash: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached evaluation result by prompt hash.

        Args:
            prompt_hash: SHA256 hash of the prompt

        Returns:
            Cached result if found and not expired, None otherwise
        """
        if not self.cache_enabled:
            return None

        cache_file = self.prompts_cache_dir / f"{prompt_hash}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r") as f:
                cached_data = json.load(f)

            # Check if cache has expired
            cached_time = cached_data.get("cached_at", 0)
            current_time = time.time()
            expiry_seconds = self.cache_expiry_hours * 3600

            if current_time - cached_time > expiry_seconds:
                # Cache expired, delete it
                cache_file.unlink()
                return None

            return cached_data.get("result")
        except Exception as e:
            print(f"Error reading cache: {e}")
            return None

    def save_eval_result(self, prompt_hash: str, result: Dict[str, Any]) -> None:
        """
        Save an evaluation result to cache.

        Args:
            prompt_hash: SHA256 hash of the prompt
            result: The evaluation result to cache
        """
        if not self.cache_enabled:
            return

        cache_file = self.prompts_cache_dir / f"{prompt_hash}.json"

        try:
            cached_data = {
                "cached_at": time.time(),
                "result": result,
            }
            with open(cache_file, "w") as f:
                json.dump(cached_data, f, indent=2)
        except Exception as e:
            print(f"Error saving cache: {e}")

    def get_tc_result(self, tc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached TC result by TC ID.

        Args:
            tc_id: Test case ID (e.g., 'TC-001')

        Returns:
            Cached result if found and not expired, None otherwise
        """
        if not self.cache_enabled:
            return None

        cache_file = self.results_cache_dir / f"{tc_id}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r") as f:
                cached_data = json.load(f)

            # Check if cache has expired
            cached_time = cached_data.get("cached_at", 0)
            current_time = time.time()
            expiry_seconds = self.cache_expiry_hours * 3600

            if current_time - cached_time > expiry_seconds:
                # Cache expired, delete it
                cache_file.unlink()
                return None

            return cached_data.get("result")
        except Exception as e:
            print(f"Error reading TC cache: {e}")
            return None

    def save_tc_result(self, tc_id: str, result: Dict[str, Any]) -> None:
        """
        Save a TC evaluation result to cache.

        Args:
            tc_id: Test case ID (e.g., 'TC-001')
            result: The evaluation result to cache
        """
        if not self.cache_enabled:
            return

        cache_file = self.results_cache_dir / f"{tc_id}.json"

        try:
            cached_data = {
                "cached_at": time.time(),
                "result": result,
            }
            with open(cache_file, "w") as f:
                json.dump(cached_data, f, indent=2)
        except Exception as e:
            print(f"Error saving TC cache: {e}")

    def clear_cache(self) -> None:
        """Clear all cached data."""
        try:
            # Clear prompt cache
            for cache_file in self.prompts_cache_dir.glob("*.json"):
                cache_file.unlink()

            # Clear TC results cache
            for cache_file in self.results_cache_dir.glob("*.json"):
                cache_file.unlink()

            print("Cache cleared successfully")
        except Exception as e:
            print(f"Error clearing cache: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the cache."""
        prompt_cache_count = len(list(self.prompts_cache_dir.glob("*.json")))
        results_cache_count = len(list(self.results_cache_dir.glob("*.json")))

        return {
            "prompt_cache_entries": prompt_cache_count,
            "results_cache_entries": results_cache_count,
            "total_cache_entries": prompt_cache_count + results_cache_count,
            "cache_enabled": self.cache_enabled,
            "cache_expiry_hours": self.cache_expiry_hours,
        }

    def cleanup_expired_cache(self) -> None:
        """Remove expired cache entries."""
        current_time = time.time()
        expiry_seconds = self.cache_expiry_hours * 3600

        removed_count = 0

        # Cleanup prompt cache
        for cache_file in self.prompts_cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r") as f:
                    cached_data = json.load(f)

                cached_time = cached_data.get("cached_at", 0)
                if current_time - cached_time > expiry_seconds:
                    cache_file.unlink()
                    removed_count += 1
            except Exception:
                pass

        # Cleanup TC results cache
        for cache_file in self.results_cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r") as f:
                    cached_data = json.load(f)

                cached_time = cached_data.get("cached_at", 0)
                if current_time - cached_time > expiry_seconds:
                    cache_file.unlink()
                    removed_count += 1
            except Exception:
                pass

        print(f"Removed {removed_count} expired cache entries")

"""Configuration management for the token optimization system."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Central configuration class."""

    # Project paths
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    CACHE_DIR = DATA_DIR / "cache"
    METRICS_DIR = DATA_DIR / "metrics"
    PROMPTS_DIR = PROJECT_ROOT / "prompts"

    # Gemini API
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = "gemini-2.0-flash"

    # AIP API
    AIP_API_URL = os.getenv(
        "AIP_API_URL",
        "https://<YOUR_API_HOST>/<YOUR_CHAT_ENDPOINT>"
    )
    AIP_API_DOMAIN = os.getenv("AIP_API_DOMAIN", "staging")
    AIP_API_LANGUAGE = os.getenv("AIP_API_LANGUAGE", "ja")
    AIP_API_COOKIE_NAME = os.getenv("AIP_API_COOKIE_NAME", "<AUTH_COOKIE_NAME>")
    AIP_API_COOKIE_VALUE = os.getenv("AIP_API_COOKIE_VALUE", "")

    # OpenAI API (for future use)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    # Cache Settings
    CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_EXPIRY_HOURS = int(os.getenv("CACHE_EXPIRY_HOURS", "168"))  # 7 days

    # Token Tracking
    TOKEN_TRACKING_ENABLED = os.getenv("TOKEN_TRACKING_ENABLED", "true").lower() == "true"

    @classmethod
    def ensure_directories(cls) -> None:
        """Create necessary directories if they don't exist."""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        (cls.CACHE_DIR / "prompts").mkdir(parents=True, exist_ok=True)
        (cls.CACHE_DIR / "results").mkdir(parents=True, exist_ok=True)
        cls.METRICS_DIR.mkdir(parents=True, exist_ok=True)
        cls.PROMPTS_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_cache_prompts_dir(cls) -> Path:
        """Get the cache prompts directory."""
        return cls.CACHE_DIR / "prompts"

    @classmethod
    def get_cache_results_dir(cls) -> Path:
        """Get the cache results directory."""
        return cls.CACHE_DIR / "results"

    @classmethod
    def get_metrics_file(cls) -> Path:
        """Get the metrics JSON file path."""
        return cls.METRICS_DIR / "token_usage.json"

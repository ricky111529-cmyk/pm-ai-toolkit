"""Base processor for request handling."""

from abc import ABC, abstractmethod
from typing import Dict, Any

from core.cache_manager import CacheManager


class BaseProcessor(ABC):
    """Abstract base processor."""

    def __init__(self):
        self.cache = CacheManager()

    @abstractmethod
    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request.

        Args:
            request: Request dictionary

        Returns:
            Processing result
        """
        pass

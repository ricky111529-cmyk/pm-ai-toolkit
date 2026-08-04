"""Request router for intelligent request handling."""

from typing import Dict, Type, Optional, Any
from abc import ABC, abstractmethod


class Processor(ABC):
    """Abstract processor interface."""

    @abstractmethod
    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request and return a result."""
        pass


class RequestRouter:
    """
    Route requests to appropriate processors based on request type.

    Types:
    - 'cached_result': Return cached result if available
    - 'summary': Use cache when possible, run evaluation if needed
    - 'analysis': Always run fresh evaluation, ignore cache
    """

    def __init__(self):
        self.routes: Dict[str, Type[Processor]] = {}

    def register(self, request_type: str, processor_class: Type[Processor]) -> None:
        """
        Register a processor for a request type.

        Args:
            request_type: Type of request (e.g., 'cached_result', 'summary', 'analysis')
            processor_class: Processor class to handle this type
        """
        self.routes[request_type] = processor_class

    def route(self, request: Dict[str, Any]) -> Type[Processor]:
        """
        Get the processor for a request.

        Args:
            request: Request dictionary with 'type' field

        Returns:
            Processor class for this request type

        Raises:
            ValueError: If request type is not registered
        """
        request_type = request.get("type", "analysis")

        if request_type not in self.routes:
            # Default to analysis processor
            if "analysis" in self.routes:
                return self.routes["analysis"]
            raise ValueError(f"No processor registered for request type: {request_type}")

        return self.routes[request_type]

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request by routing it to the appropriate processor.

        Args:
            request: Request dictionary

        Returns:
            Processing result
        """
        processor_class = self.route(request)
        processor = processor_class()
        return processor.process(request)

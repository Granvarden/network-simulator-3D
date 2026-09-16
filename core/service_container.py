"""Service container / dependency locator."""

from typing import Any, Dict, Type, TypeVar

T = TypeVar("T")


class ServiceContainer:
    """Lightweight dependency injection container."""

    def __init__(self):
        self._services: Dict[str, Any] = {}

    def register(self, key: str, instance: Any) -> None:
        """Register a service by name."""
        self._services[key] = instance

    def get(self, key: str) -> Any:
        """Retrieve a service by name."""
        if key not in self._services:
            raise KeyError(f"Service '{key}' is not registered in container.")
        return self._services[key]

    def has(self, key: str) -> bool:
        return key in self._services

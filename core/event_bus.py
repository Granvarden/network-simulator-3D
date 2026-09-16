"""Event bus for decoupled communication between modules."""

from collections import defaultdict
from typing import Any, Callable, Dict, List


class EventBus:
    """Decoupled Publish/Subscribe event system."""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[..., None]]] = defaultdict(list)

    def subscribe(self, event_type: str, callback: Callable[..., None]) -> None:
        """Subscribe a callback to a given event type."""
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable[..., None]) -> None:
        """Unsubscribe a callback from an event type."""
        if event_type in self._subscribers and callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)

    def publish(self, event_type: str, **kwargs: Any) -> None:
        """Publish an event with keyword arguments to all subscribers."""
        for callback in list(self._subscribers.get(event_type, [])):
            try:
                callback(**kwargs)
            except Exception as e:
                print(f"[EventBus Error] in {event_type} handler: {e}")

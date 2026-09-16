"""Base class for world interactables."""

from abc import ABC, abstractmethod
from typing import Optional, Tuple


class Interactable(ABC):
    """Objects in the 3D world that the player can look at and interact with."""

    def __init__(self, name: str, position: Tuple[float, float, float]):
        self.name: str = name
        self.position: Tuple[float, float, float] = position
        self.is_interactable: bool = True

    @abstractmethod
    def get_interaction_hint(self) -> str:
        """Text displayed on HUD when looking at this interactable."""
        pass

    @abstractmethod
    def get_bounding_box(self) -> Tuple[float, float, float, float, float, float]:
        """Returns (min_x, min_y, min_z, max_x, max_y, max_z)."""
        pass

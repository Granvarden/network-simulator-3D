"""Base 3D Device visual model."""

from abc import ABC, abstractmethod
from typing import Any, Tuple
from OpenGL.GL import *
from rendering.primitives import draw_box, draw_wire_box


class DeviceModel(ABC):
    """Abstract visual model decoupled from device logic."""

    @abstractmethod
    def render(self, device: Any, cx: float, cy: float, cz: float) -> None:
        """Render the 3D model centered at (cx, cy, cz)."""
        pass

"""Base 3D Device visual model."""

from abc import ABC, abstractmethod
from typing import Any, Tuple
from OpenGL.GL import *
from rendering.primitives import draw_box, draw_wire_box


class DeviceModel(ABC):
    """Abstract visual model decoupled from device logic."""

    @staticmethod
    def get_port_led_colors(port: Any) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        """
        Calculate (link_led_color, activity_led_color) for any network port:
        - Operational (Connected + Admin UP on both sides): (Vibrant Green, Glowing Green)
        - Connected but Inactive/Disabled (Cable present, but Admin DOWN or remote DOWN): (Solid Amber, OFF)
        - Disconnected (No cable): (Dark OFF, Dark OFF)
        """
        off_col = (0.12, 0.14, 0.17)
        green_lnk = (0.12, 0.98, 0.28)
        green_act = (0.22, 1.00, 0.40)
        amber_col = (0.98, 0.62, 0.08)

        if not port:
            return off_col, off_col

        if port.connected_port is not None:
            if port.is_operational:
                return green_lnk, green_act
            else:
                return amber_col, off_col
        else:
            return off_col, off_col

    @abstractmethod
    def render(self, device: Any, cx: float, cy: float, cz: float) -> None:
        """Render the 3D model centered at (cx, cy, cz)."""
        pass

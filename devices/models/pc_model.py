"""3D visual model for a PC Workstation."""

from typing import Any
from OpenGL.GL import *
from rendering.primitives import draw_box
from config.graphics_config import GraphicsConfig
from .device_model import DeviceModel


class PCModel(DeviceModel):
    """Renders a PC / Rackmount Workstation."""

    def render(self, device: Any, cx: float, cy: float, cz: float) -> None:
        width = 0.44
        height = 0.086
        depth = 0.50

        # PC Chassis (Matte Dark Gray)
        draw_box(cx, cy, cz, width, height, depth, GraphicsConfig.COLOR_PC_CHASSIS)

        # Rack ears/brackets
        ear_color = (0.25, 0.27, 0.30)
        draw_box(cx - (width / 2.0 + 0.02), cy, cz + depth / 2.0 - 0.015, 0.04, height, 0.03, ear_color)
        draw_box(cx + (width / 2.0 + 0.02), cy, cz + depth / 2.0 - 0.015, 0.04, height, 0.03, ear_color)

        # Front Faceplate
        face_z = cz + depth / 2.0 + 0.002
        draw_box(cx, cy, face_z, width - 0.02, height - 0.006, 0.003, (0.16, 0.18, 0.20))

        # Power Button & LED
        pwr_led = GraphicsConfig.COLOR_LED_GREEN if device.power_state else GraphicsConfig.COLOR_LED_OFF
        draw_box(cx - 0.16, cy + 0.015, face_z + 0.004, 0.014, 0.014, 0.003, (0.35, 0.38, 0.42))
        draw_box(cx - 0.16, cy + 0.015, face_z + 0.006, 0.006, 0.006, 0.002, pwr_led)

        # Drive Bay Slots
        draw_box(cx - 0.02, cy, face_z + 0.003, 0.18, 0.030, 0.002, (0.10, 0.11, 0.13))

        # Ethernet eth0 port (placed on front/side for easy player connection in simulator)
        eth0 = device.get_port("eth0")
        draw_box(cx + 0.14, cy - 0.01, face_z + 0.004, 0.022, 0.018, 0.005, GraphicsConfig.COLOR_PORT_METAL)
        draw_box(cx + 0.14, cy - 0.01, face_z + 0.007, 0.016, 0.012, 0.002, (0.05, 0.05, 0.05))

        led_c = GraphicsConfig.COLOR_LED_GREEN if (eth0 and eth0.is_operational) else GraphicsConfig.COLOR_LED_OFF
        draw_box(cx + 0.14, cy + 0.008, face_z + 0.004, 0.004, 0.004, 0.002, led_c)

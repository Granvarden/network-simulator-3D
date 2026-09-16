"""3D visual model for a 2U Router."""

from typing import Any
from OpenGL.GL import *
from rendering.primitives import draw_box, draw_cylinder
from config.graphics_config import GraphicsConfig
from .device_model import DeviceModel


class RouterModel(DeviceModel):
    """Renders a realistic industrial 2U Router."""

    def render(self, device: Any, cx: float, cy: float, cz: float) -> None:
        width = 0.48
        height = 0.086
        depth = 0.55

        # Main Chassis (Industrial Cisco Slate)
        draw_box(cx, cy, cz, width, height, depth, GraphicsConfig.COLOR_ROUTER_CHASSIS)

        # Rack Ears (Left & Right 19" mounting brackets)
        ear_color = (0.28, 0.30, 0.33)
        draw_box(cx - (width / 2.0 + 0.02), cy, cz + depth / 2.0 - 0.015, 0.04, height, 0.03, ear_color)
        draw_box(cx + (width / 2.0 + 0.02), cy, cz + depth / 2.0 - 0.015, 0.04, height, 0.03, ear_color)

        # Front Faceplate Inset
        face_z = cz + depth / 2.0 + 0.002
        draw_box(cx, cy, face_z, width - 0.04, height - 0.01, 0.004, (0.12, 0.15, 0.18))

        # Power LED
        power_led_color = GraphicsConfig.COLOR_LED_GREEN if device.power_state else GraphicsConfig.COLOR_LED_OFF
        draw_box(cx - 0.20, cy + 0.02, face_z + 0.003, 0.006, 0.006, 0.003, power_led_color)

        # Render Ports on Faceplate
        g0 = device.get_port("Gi0/0")
        if g0:
            # Metal port housing
            draw_box(cx - 0.15, cy, face_z + 0.004, 0.022, 0.018, 0.006, GraphicsConfig.COLOR_PORT_METAL)
            # Port cavity
            draw_box(cx - 0.15, cy, face_z + 0.007, 0.016, 0.012, 0.002, (0.05, 0.05, 0.05))
            # Link LED
            led_color = GraphicsConfig.COLOR_LED_GREEN if g0.is_operational else GraphicsConfig.COLOR_LED_OFF
            draw_box(cx - 0.15, cy + 0.015, face_z + 0.004, 0.004, 0.004, 0.002, led_color)

        g1 = device.get_port("Gi0/1")
        if g1:
            draw_box(cx - 0.10, cy, face_z + 0.004, 0.022, 0.018, 0.006, GraphicsConfig.COLOR_PORT_METAL)
            draw_box(cx - 0.10, cy, face_z + 0.007, 0.016, 0.012, 0.002, (0.05, 0.05, 0.05))
            led_color = GraphicsConfig.COLOR_LED_GREEN if g1.is_operational else GraphicsConfig.COLOR_LED_OFF
            draw_box(cx - 0.10, cy + 0.015, face_z + 0.004, 0.004, 0.004, 0.002, led_color)

        # Console Port (RJ45 with sky blue label)
        draw_box(cx + 0.15, cy, face_z + 0.004, 0.022, 0.018, 0.006, (0.2, 0.5, 0.8))
        draw_box(cx + 0.15, cy, face_z + 0.007, 0.016, 0.012, 0.002, (0.05, 0.05, 0.05))

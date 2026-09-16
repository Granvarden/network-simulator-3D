"""3D visual model for a 1U 24-Port Switch."""

from typing import Any
from OpenGL.GL import *
from rendering.primitives import draw_box
from config.graphics_config import GraphicsConfig
from .device_model import DeviceModel


class SwitchModel(DeviceModel):
    """Renders an industrial 1U 24-Port Gigabit Switch."""

    def render(self, device: Any, cx: float, cy: float, cz: float) -> None:
        width = 0.48
        height = 0.042
        depth = 0.38

        # Main Chassis
        draw_box(cx, cy, cz, width, height, depth, GraphicsConfig.COLOR_SWITCH_CHASSIS)

        # Rack Ears
        ear_color = (0.28, 0.30, 0.33)
        draw_box(cx - (width / 2.0 + 0.015), cy, cz + depth / 2.0 - 0.015, 0.03, height, 0.03, ear_color)
        draw_box(cx + (width / 2.0 + 0.015), cy, cz + depth / 2.0 - 0.015, 0.03, height, 0.03, ear_color)

        # Front Faceplate
        face_z = cz + depth / 2.0 + 0.002
        draw_box(cx, cy, face_z, width - 0.02, height - 0.006, 0.003, (0.08, 0.10, 0.14))

        # Status LEDs on left
        draw_box(cx - 0.21, cy + 0.008, face_z + 0.003, 0.004, 0.004, 0.002, GraphicsConfig.COLOR_LED_GREEN)
        draw_box(cx - 0.21, cy - 0.008, face_z + 0.003, 0.004, 0.004, 0.002, GraphicsConfig.COLOR_LED_GREEN)

        # Render 24 RJ45 Ports (2 rows of 12)
        start_x = cx - 0.16
        spacing_x = 0.028

        for i in range(1, 25):
            port = device.get_port(f"Gi0/{i}")
            col = (i - 1) % 12
            row = (i - 1) // 12
            px = start_x + col * spacing_x
            py = cy - 0.008 if row == 0 else cy + 0.008

            # Port housing
            draw_box(px, py, face_z + 0.003, 0.020, 0.012, 0.004, GraphicsConfig.COLOR_PORT_METAL)
            # RJ45 cavity
            draw_box(px, py, face_z + 0.005, 0.015, 0.008, 0.002, (0.02, 0.02, 0.02))

            # Small Port Link LED
            if port and port.is_operational:
                led_c = GraphicsConfig.COLOR_LED_GREEN
            else:
                led_c = GraphicsConfig.COLOR_LED_OFF
            led_y = py + 0.008 if row == 1 else py - 0.008
            draw_box(px, led_y, face_z + 0.003, 0.003, 0.003, 0.002, led_c)

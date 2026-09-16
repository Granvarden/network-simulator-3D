"""High-detail 3D visual model for a 2U Enterprise Cisco-style Modular Router."""

from typing import Any
from OpenGL.GL import *
from rendering.primitives import draw_box
from config.graphics_config import GraphicsConfig
from .device_model import DeviceModel


class RouterModel(DeviceModel):
    """Renders a high-detail 2U Enterprise Router with mounting ears, ventilation, OLED, and RJ45 ports."""

    def render(self, device: Any, cx: float, cy: float, cz: float) -> None:
        # Standard 19" Rackmount 2U Dimensions (Matches Switch and PC depth)
        width = 0.44
        height = 0.086
        depth = 0.50

        # 1. Main Heavy-Duty Steel Chassis (Dark Cisco Slate Blue)
        draw_box(cx, cy, cz, width, height, depth, GraphicsConfig.COLOR_ROUTER_CHASSIS)

        # 2. Left & Right 19" Rack Mounting Ears (Mounted flush at front)
        ear_color = (0.26, 0.28, 0.32)
        ear_d = 0.025
        ear_w = 0.02
        ear_z = cz + depth / 2.0 - ear_d / 2.0
        draw_box(cx - 0.23, cy, ear_z, ear_w, height, ear_d, ear_color)
        draw_box(cx + 0.23, cy, ear_z, ear_w, height, ear_d, ear_color)

        # Chrome Mounting Bolts / Screw Holes on Ears (4 screws per side)
        screw_color = (0.75, 0.78, 0.82)
        for side in (-0.235, 0.235):
            for sy_off in (-0.030, -0.010, 0.010, 0.030):
                draw_box(cx + side, cy + sy_off, cz + depth / 2.0 + 0.001, 0.006, 0.006, 0.002, screw_color)

        # Industrial Metal Pull Handles on Left and Right Ears
        handle_color = (0.65, 0.68, 0.72)
        draw_box(cx - 0.236, cy, cz + depth / 2.0 + 0.015, 0.006, 0.046, 0.018, handle_color)
        draw_box(cx + 0.236, cy, cz + depth / 2.0 + 0.015, 0.006, 0.046, 0.018, handle_color)

        # 3. Front Industrial Faceplate Inset
        face_z = cz + depth / 2.0
        draw_box(cx, cy, face_z + 0.001, width - 0.008, height - 0.004, 0.003, (0.12, 0.15, 0.19))

        # Cisco-style Cyan/Teal Brand Stripe across top front edge
        draw_box(cx, cy + height / 2.0 - 0.005, face_z + 0.002, width - 0.012, 0.006, 0.002, (0.06, 0.52, 0.74))

        # 4. Left Air Intake Ventilation Grille (6 vertical dark slats)
        for s in range(6):
            slat_x = cx - 0.185 + s * 0.016
            draw_box(slat_x, cy, face_z + 0.002, 0.008, height - 0.024, 0.002, (0.05, 0.07, 0.09))

        # 5. Center OLED Management Screen & Telemetry
        screen_cx = cx - 0.05
        screen_cy = cy + 0.014
        # Black bezel
        draw_box(screen_cx, screen_cy, face_z + 0.002, 0.060, 0.028, 0.002, (0.03, 0.04, 0.06))
        # Screen surface
        scr_color = (0.12, 0.68, 0.82) if device.power_state else (0.05, 0.12, 0.16)
        draw_box(screen_cx, screen_cy, face_z + 0.003, 0.052, 0.020, 0.001, scr_color)
        if device.power_state:
            # Simulated telemetry graph line on screen
            draw_box(screen_cx, screen_cy, face_z + 0.004, 0.040, 0.003, 0.001, (0.90, 0.98, 1.0))

        # Diagnostic Status LED Cluster (PWR, SYS, ACT) below screen
        pwr_col = GraphicsConfig.COLOR_LED_GREEN if device.power_state else GraphicsConfig.COLOR_LED_OFF
        sys_col = GraphicsConfig.COLOR_LED_GREEN if device.power_state else GraphicsConfig.COLOR_LED_OFF
        act_col = (0.20, 0.92, 0.35) if device.power_state else GraphicsConfig.COLOR_LED_OFF
        draw_box(cx - 0.066, cy - 0.015, face_z + 0.002, 0.005, 0.005, 0.002, pwr_col)
        draw_box(cx - 0.050, cy - 0.015, face_z + 0.002, 0.005, 0.005, 0.002, sys_col)
        draw_box(cx - 0.034, cy - 0.015, face_z + 0.002, 0.005, 0.005, 0.002, act_col)

        # 6. Right Equipment Module Plate (4x Gigabit Ethernet + 1x Console)
        port_base_z = face_z + 0.002
        draw_box(cx + 0.095, cy - 0.015, port_base_z, 0.190, 0.034, 0.003, (0.20, 0.23, 0.28))

        # 4 Gigabit Ethernet RJ45 Ports (Gi0/0 - Gi0/3)
        router_ports = [
            ("Gi0/0", 0.020),
            ("Gi0/1", 0.055),
            ("Gi0/2", 0.090),
            ("Gi0/3", 0.125),
        ]
        for p_name, lx in router_ports:
            port = device.get_port(p_name)
            px = cx + lx
            py = cy - 0.015
            pz = face_z + 0.002

            # Metal shield collar
            draw_box(px, py, pz, 0.022, 0.016, 0.006, GraphicsConfig.COLOR_PORT_METAL)
            # Socket cavity
            draw_box(px, py, pz + 0.002, 0.016, 0.011, 0.003, (0.02, 0.03, 0.04))
            # Gold contact pins inside socket
            draw_box(px, py + 0.002, pz + 0.003, 0.010, 0.002, 0.001, (0.92, 0.75, 0.20))
            # Link LED
            led_c = GraphicsConfig.COLOR_LED_GREEN if (port and port.is_operational) else GraphicsConfig.COLOR_LED_OFF
            draw_box(px, py + 0.012, pz, 0.004, 0.003, 0.002, led_c)

        # Console Port (Local Pos: 0.165, -0.015, 0.252)
        pcon_x = cx + 0.165
        pcon_y = cy - 0.015
        pcon_z = face_z + 0.002
        # Cisco Sky Blue RJ45 Collar
        draw_box(pcon_x, pcon_y, pcon_z, 0.022, 0.016, 0.006, (0.15, 0.55, 0.85))
        draw_box(pcon_x, pcon_y, pcon_z + 0.002, 0.016, 0.011, 0.003, (0.02, 0.03, 0.04))
        # "CONSOLE" Blue Label Tab above port
        draw_box(pcon_x, pcon_y + 0.012, pcon_z, 0.018, 0.004, 0.002, (0.85, 0.92, 1.0))

        # USB / AUX Diagnostic port
        draw_box(cx + 0.192, cy - 0.015, pcon_z, 0.010, 0.007, 0.004, (0.16, 0.18, 0.22))

        # Power Rocker Switch (Far right upper corner)
        pwr_sw_c = (0.85, 0.22, 0.22) if device.power_state else (0.35, 0.12, 0.12)
        draw_box(cx + 0.19, cy + 0.018, face_z + 0.002, 0.014, 0.012, 0.004, pwr_sw_c)

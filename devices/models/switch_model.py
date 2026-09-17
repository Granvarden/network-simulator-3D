"""High-detail 3D visual model for a 1U 24-Port Enterprise Gigabit Switch."""

from typing import Any
from OpenGL.GL import *
from rendering.primitives import draw_box
from config.graphics_config import GraphicsConfig
from .device_model import DeviceModel


class SwitchModel(DeviceModel):
    """Renders a high-detail 1U 24-Port Gigabit Switch with dual-row RJ45 matrix, SFP cages, and status LEDs."""

    def render(self, device: Any, cx: float, cy: float, cz: float) -> None:
        # Standard 19" Rackmount 1U Dimensions (Standardized 0.50m depth matching Router and PC)
        width = 0.44
        height = 0.043
        depth = 0.50

        # 1. Main Steel Chassis (Dark Enterprise Charcoal)
        draw_box(cx, cy, cz, width, height, depth, GraphicsConfig.COLOR_SWITCH_CHASSIS)

        # 2. Left & Right 19" Rack Mounting Ears
        ear_color = (0.25, 0.27, 0.30)
        ear_d = 0.025
        ear_w = 0.02
        ear_z = cz + depth / 2.0 - ear_d / 2.0
        draw_box(cx - 0.23, cy, ear_z, ear_w, height, ear_d, ear_color)
        draw_box(cx + 0.23, cy, ear_z, ear_w, height, ear_d, ear_color)

        # Chrome Mounting Bolts / Screw Holes on Ears (2 per side for 1U)
        screw_color = (0.75, 0.78, 0.82)
        for side in (-0.235, 0.235):
            for sy_off in (-0.012, 0.012):
                draw_box(cx + side, cy + sy_off, cz + depth / 2.0 + 0.001, 0.006, 0.006, 0.002, screw_color)

        # 3. Front Faceplate
        face_z = cz + depth / 2.0
        draw_box(cx, cy, face_z + 0.00075, width - 0.008, height - 0.004, 0.0015, (0.10, 0.12, 0.16))

        # Top Accent Bezel Stripe
        draw_box(cx, cy + height / 2.0 - 0.003, face_z + 0.0017, width - 0.012, 0.003, 0.0006, (0.35, 0.40, 0.46))

        # 4. Left System Status Panel & Mode Pushbutton
        draw_box(cx - 0.190, cy, face_z + 0.0030, 0.008, 0.008, 0.0025, (0.35, 0.38, 0.42))  # Mode button
        # 4 Micro Diagnostic LEDs (SYST, STAT, SPEED, DUPLEX)
        sys_led_col = GraphicsConfig.COLOR_LED_GREEN if device.power_state else GraphicsConfig.COLOR_LED_OFF
        for idx in range(4):
            lx = cx - 0.175 + idx * 0.009
            draw_box(lx, cy, face_z + 0.0020, 0.004, 0.004, 0.0012, sys_led_col)

        # 5. Dual-Row 24-Port RJ45 Matrix Block
        # Backing metal shield cage (cleanly proud of front faceplate)
        start_x = -0.13
        spacing_x = 0.024
        cage_center_x = cx + start_x + 5.5 * spacing_x
        cage_w = 12 * spacing_x + 0.008
        draw_box(cage_center_x, cy, face_z + 0.0018, cage_w, 0.034, 0.0016, (0.22, 0.25, 0.29))

        port_pz = face_z + 0.002

        import time
        current_time = time.time()

        for i in range(1, 25):
            port = device.get_port(f"Gi0/{i}")
            col = (i - 1) % 12
            row = (i - 1) // 12

            px = cx + start_x + col * spacing_x
            py = cy - 0.008 if row == 0 else cy + 0.008

            # Precision Metallic Port Shield Collar (Exact match: 0.020m x 0.012m)
            draw_box(px, py, port_pz, 0.020, 0.012, 0.005, GraphicsConfig.COLOR_PORT_METAL)

            # RJ45 Socket Cavity
            draw_box(px, py, port_pz + 0.002, 0.015, 0.008, 0.002, (0.02, 0.02, 0.03))

            # Gold Contact Pins simulation
            pin_y_off = 0.002 if row == 0 else -0.002
            draw_box(px, py + pin_y_off, port_pz + 0.0032, 0.009, 0.002, 0.0008, (0.92, 0.75, 0.20))

            # Dual Micro Status LED Indicators (Left: Link Status, Right: Activity / Speed)
            if port is not None:
                link_col, act_col = port.get_led_colors(device.power_state, current_time)
            else:
                link_col, act_col = GraphicsConfig.COLOR_LED_OFF, GraphicsConfig.COLOR_LED_OFF

            led_y = py - 0.0085 if row == 0 else py + 0.0085

            # Contrast Bezel Housing
            draw_box(px, led_y, port_pz + 0.0012, 0.012, 0.0035, 0.0014, GraphicsConfig.COLOR_LED_BEZEL)

            # Left Micro LED (Link Status)
            draw_box(px - 0.0032, led_y, port_pz + 0.0022, 0.0035, 0.0022, 0.0008, link_col)

            # Right Micro LED (Activity Status)
            draw_box(px + 0.0032, led_y, port_pz + 0.0022, 0.0035, 0.0022, 0.0008, act_col)

        # 6. SFP+ 10G Dual Uplink Cages on Far Right
        sfp_z = face_z + 0.002
        for sfp_idx, sx_off in enumerate((0.165, 0.188)):
            sfp_x = cx + sx_off
            # SFP outer metallic cage
            draw_box(sfp_x, cy, sfp_z, 0.018, 0.016, 0.006, (0.60, 0.62, 0.66))
            # SFP optical cavity / dust cap
            draw_box(sfp_x, cy, sfp_z + 0.002, 0.013, 0.011, 0.003, (0.08, 0.10, 0.14))
            # SFP activity LED (stepped proud of faceplate)
            sfp_c = GraphicsConfig.COLOR_LED_GREEN if device.power_state else GraphicsConfig.COLOR_LED_OFF
            draw_box(sfp_x, cy + 0.010, face_z + 0.0022, 0.003, 0.003, 0.0014, sfp_c)


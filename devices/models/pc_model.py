"""High-detail 3D visual model for a 2U Enterprise Rackmount Server / Workstation PC."""

from typing import Any
from OpenGL.GL import *
from rendering.primitives import draw_box
from config.graphics_config import GraphicsConfig
from .device_model import DeviceModel


class PCModel(DeviceModel):
    """Renders a high-detail 2U Enterprise Rackmount Server with drive array, service tag, and front eth0."""

    def render(self, device: Any, cx: float, cy: float, cz: float) -> None:
        # Standard 19" Rackmount 2U Dimensions (Standardized 0.50m depth matching Router and Switch)
        width = 0.44
        height = 0.086
        depth = 0.50

        # 1. Main Heavy-Duty Steel Server Chassis (Matte Dark Industrial Steel)
        draw_box(cx, cy, cz, width, height, depth, GraphicsConfig.COLOR_PC_CHASSIS)

        # 2. Left & Right 19" Server Rack Mounting Ears with Release Latches
        ear_color = (0.24, 0.26, 0.29)
        ear_d = 0.025
        ear_w = 0.02
        ear_z = cz + depth / 2.0 - ear_d / 2.0
        draw_box(cx - 0.23, cy, ear_z, ear_w, height, ear_d, ear_color)
        draw_box(cx + 0.23, cy, ear_z, ear_w, height, ear_d, ear_color)

        # Chrome Mounting Screws (4 per ear)
        screw_color = (0.75, 0.78, 0.82)
        for side in (-0.235, 0.235):
            for sy_off in (-0.030, -0.010, 0.010, 0.030):
                draw_box(cx + side, cy + sy_off, cz + depth / 2.0 + 0.001, 0.006, 0.006, 0.002, screw_color)

        # Quick-Release Server Latch Handles
        latch_color = (0.60, 0.63, 0.68)
        draw_box(cx - 0.236, cy, cz + depth / 2.0 + 0.012, 0.006, 0.048, 0.014, latch_color)
        draw_box(cx + 0.236, cy, cz + depth / 2.0 + 0.012, 0.006, 0.048, 0.014, latch_color)

        # 3. Front Perforated Server Faceplate Bezel
        face_z = cz + depth / 2.0
        draw_box(cx, cy, face_z + 0.00075, width - 0.008, height - 0.004, 0.0015, (0.13, 0.14, 0.17))

        # Top Silver Bezel Line
        draw_box(cx, cy + height / 2.0 - 0.004, face_z + 0.0018, width - 0.012, 0.004, 0.0006, (0.42, 0.46, 0.52))

        # 4. Front Hot-Swap Drive Array (8x 2.5" SAS/SATA Drive Sleds: 4 cols x 2 rows)
        caddy_w = 0.045
        caddy_h = 0.032
        drive_start_x = cx - 0.175
        drive_sp_x = 0.048
        drive_led_col = (0.15, 0.85, 0.35) if device.power_state else GraphicsConfig.COLOR_LED_OFF

        for col in range(4):
            dx = drive_start_x + col * drive_sp_x
            for row in range(2):
                dy = cy - 0.018 if row == 0 else cy + 0.018
                # Drive sled body (cleanly stepped proud of faceplate)
                draw_box(dx, dy, face_z + 0.0020, caddy_w, caddy_h, 0.0016, (0.08, 0.09, 0.11))
                # Metal release latch bar
                draw_box(dx, dy, face_z + 0.0035, caddy_w - 0.006, 0.008, 0.0012, (0.35, 0.38, 0.43))
                # Drive activity LED
                draw_box(dx + caddy_w / 2.0 - 0.006, dy + caddy_h / 2.0 - 0.006, face_z + 0.0035, 0.003, 0.003, 0.0010, drive_led_col)

        # 5. Right Control & Diagnostics Panel
        # Dell-style Pull-Out Asset Service Tag Tray (Blue Accent)
        draw_box(cx + 0.055, cy + 0.022, face_z + 0.0025, 0.028, 0.014, 0.0020, (0.10, 0.42, 0.82))

        # Power Button with Illuminated LED ring
        pwr_led = GraphicsConfig.COLOR_LED_GREEN if device.power_state else GraphicsConfig.COLOR_LED_OFF
        draw_box(cx + 0.170, cy + 0.020, face_z + 0.0025, 0.015, 0.015, 0.0020, (0.32, 0.35, 0.40))
        draw_box(cx + 0.170, cy + 0.020, face_z + 0.0038, 0.007, 0.007, 0.0010, pwr_led)

        # Server Health Heartbeat LED & System ID Button
        health_col = (0.2, 0.7, 1.0) if device.power_state else GraphicsConfig.COLOR_LED_OFF
        draw_box(cx + 0.145, cy + 0.020, face_z + 0.0025, 0.005, 0.005, 0.0016, health_col)
        draw_box(cx + 0.130, cy + 0.020, face_z + 0.0025, 0.006, 0.006, 0.0016, (0.25, 0.28, 0.32))

        # 6. Front Maintenance Ethernet Port (eth0) (Local Pos: 0.12, -0.015, 0.252)
        import time
        current_time = time.time()
        eth0 = device.get_port("eth0")
        eth_x = cx + 0.12
        eth_y = cy - 0.015
        eth_z = face_z + 0.002

        # Metal Port Shield Collar (local_slot_pos[2] = 0.252)
        draw_box(eth_x, eth_y, eth_z, 0.022, 0.016, 0.006, GraphicsConfig.COLOR_PORT_METAL)

        # Socket Cavity
        draw_box(eth_x, eth_y, eth_z + 0.002, 0.016, 0.011, 0.003, (0.02, 0.03, 0.04))

        # Gold Contact Pins
        draw_box(eth_x, eth_y + 0.002, eth_z + 0.0032, 0.010, 0.002, 0.0008, (0.92, 0.75, 0.20))

        # Dual Link & Speed/Activity LEDs above eth0
        if eth0 is not None:
            link_col, act_col = eth0.get_led_colors(device.power_state, current_time)
        else:
            link_col, act_col = GraphicsConfig.COLOR_LED_OFF, GraphicsConfig.COLOR_LED_OFF

        # Contrast Bezel Housing
        draw_box(eth_x, eth_y + 0.012, face_z + 0.0030, 0.014, 0.0045, 0.0014, GraphicsConfig.COLOR_LED_BEZEL)

        # Left Micro LED (Link Status)
        draw_box(eth_x - 0.0035, eth_y + 0.012, face_z + 0.0040, 0.004, 0.003, 0.0008, link_col)

        # Right Micro LED (Activity Status)
        draw_box(eth_x + 0.0035, eth_y + 0.012, face_z + 0.0040, 0.004, 0.003, 0.0008, act_col)

        # "eth0 / LOM" White Label Plate (cleanly proud of faceplate bezel)
        draw_box(eth_x, eth_y - 0.012, face_z + 0.0022, 0.018, 0.003, 0.0012, (0.85, 0.88, 0.92))

        # 2x Front USB 3.0 Diagnostic Ports
        usb_z = face_z + 0.0025
        draw_box(cx + 0.165, eth_y, usb_z, 0.012, 0.007, 0.003, (0.12, 0.40, 0.78))
        draw_box(cx + 0.182, eth_y, usb_z, 0.012, 0.007, 0.003, (0.12, 0.40, 0.78))

"""Server Rack implementation (Standard 42U enclosure)."""

from typing import Any, Dict, List, Optional, Tuple
from OpenGL.GL import *
from rendering.primitives import draw_box, draw_wire_box, draw_line_3d
from config.game_config import GameConfig
from config.graphics_config import GraphicsConfig
from devices.device import Device
from devices.models.router_model import RouterModel
from devices.models.switch_model import SwitchModel
from devices.models.pc_model import PCModel
from .interactable import Interactable


class Rack(Interactable):
    """Standard 42U Data Center Server Rack with slot occupancy tracking."""

    def __init__(self, rack_id: str, position: Tuple[float, float, float], rotation: float = 0.0):
        super().__init__(name=rack_id, position=position)
        self.rack_id: str = rack_id
        self.rotation: float = rotation
        self.height_units: int = GameConfig.RACK_U_COUNT  # 42U
        self.u_height_m: float = GameConfig.RACK_U_HEIGHT_METERS  # ~0.04445m
        self.width_m: float = GameConfig.RACK_WIDTH_METERS        # 0.60m
        self.depth_m: float = GameConfig.RACK_DEPTH_METERS        # 0.90m
        self.total_height_m: float = 42 * self.u_height_m + 0.15 # ~2.01m
        self.base_y: float = position[1]

        # Installed devices
        self.devices: List[Device] = []
        # Map: U_number (1..42) -> Device
        self.occupied_units: Dict[int, Device] = {}

        # Door state
        self.door_open: bool = True  # Default open for easy access

        # Visual model instances
        self._router_model = RouterModel()
        self._switch_model = SwitchModel()
        self._pc_model = PCModel()

    def get_interaction_hint(self) -> str:
        dev_count = len(self.devices)
        return f"[E] {self.rack_id} (42U) | {dev_count} Devices Installed"

    def get_bounding_box(self) -> Tuple[float, float, float, float, float, float]:
        hw = self.width_m / 2.0
        hd = self.depth_m / 2.0
        min_x = self.position[0] - hw
        max_x = self.position[0] + hw
        min_y = self.position[1]
        max_y = self.position[1] + self.total_height_m
        min_z = self.position[2] - hd
        max_z = self.position[2] + hd
        return (min_x, min_y, min_z, max_x, max_y, max_z)

    def toggle_door(self) -> None:
        self.door_open = not self.door_open

    def get_u_from_world_y(self, y: float) -> int:
        """Convert a 3D world Y coordinate to the corresponding U unit (1-42)."""
        rel_y = y - (self.base_y + 0.08)
        u_idx = int(rel_y / self.u_height_m) + 1
        return max(1, min(self.height_units, u_idx))

    def get_world_y_for_u(self, u: int) -> float:
        """Get the base world Y position for a given U unit."""
        return self.base_y + 0.08 + (u - 1) * self.u_height_m

    def can_install(self, device: Device, start_u: int) -> Tuple[bool, str]:
        """Check whether a device can be installed at the specified U position."""
        if start_u < 1:
            return False, f"Invalid U position {start_u} (must be between 1 and {self.height_units})"

        end_u = start_u + device.u_height - 1
        if end_u > self.height_units:
            return False, f"Device ({device.u_height}U) exceeds rack height ({end_u} > {self.height_units}U)"

        # Check for collision with existing devices
        for u in range(start_u, end_u + 1):
            if u in self.occupied_units:
                occ_dev = self.occupied_units[u]
                return False, f"Position U{u} is already occupied by '{occ_dev.hostname}'"

        return True, "OK"

    def install_device(self, device: Device, start_u: int) -> Tuple[bool, str]:
        """Install a device at start_u. Returns (success, message)."""
        can_inst, msg = self.can_install(device, start_u)
        if not can_inst:
            return False, msg

        device.rack_id = self.rack_id
        device.start_u = start_u
        end_u = start_u + device.u_height - 1

        # Calculate exact 3D center position (chassis depth 0.50m mounted to front rail at cz + 0.40m)
        center_y = self.get_world_y_for_u(start_u) + (device.u_height * self.u_height_m) / 2.0
        device.position = (self.position[0], center_y, self.position[2] + 0.15)

        # Register occupied slots
        for u in range(start_u, end_u + 1):
            self.occupied_units[u] = device

        if device not in self.devices:
            self.devices.append(device)

        return True, f"Installed {device.hostname} at {self.rack_id} U{start_u}-U{end_u}"

    def remove_device(self, device: Device) -> Tuple[bool, str]:
        """Remove device from rack and disconnect any plugged cables."""
        if device not in self.devices:
            return False, f"Device '{device.hostname}' is not installed in {self.rack_id}"

        # Disconnect cables safely
        device.disconnect_all_cables()

        # Free occupied units
        for u, dev in list(self.occupied_units.items()):
            if dev == device:
                del self.occupied_units[u]

        self.devices.remove(device)
        device.rack_id = None
        device.start_u = None
        return True, f"Removed '{device.hostname}' from {self.rack_id}"

    def get_device_at_u(self, u: int) -> Optional[Device]:
        return self.occupied_units.get(u)

    def render(self) -> None:
        """Render a highly detailed 42U datacenter server rack enclosure."""
        cx, cy, cz = self.position
        hw = self.width_m / 2.0      # 0.30m half-width
        hd = self.depth_m / 2.0      # 0.45m half-depth
        th = self.total_height_m     # ~2.01m total height

        rail_y_base = cy + 0.08
        rail_h = 42 * self.u_height_m

        # ================================================================
        # 1. STRUCTURAL FRAME: 4 Corner Posts (Thick Extruded Steel)
        # ================================================================
        post_w = 0.045
        post_d = 0.045
        post_color = (0.11, 0.12, 0.14)  # Near-black steel
        mid_y = cy + th / 2.0

        # Front-Left, Front-Right posts (flush with front face)
        draw_box(cx - hw + post_w / 2, mid_y, cz + hd - post_d / 2, post_w, th, post_d, post_color)
        draw_box(cx + hw - post_w / 2, mid_y, cz + hd - post_d / 2, post_w, th, post_d, post_color)
        # Rear-Left, Rear-Right posts
        draw_box(cx - hw + post_w / 2, mid_y, cz - hd + post_d / 2, post_w, th, post_d, post_color)
        draw_box(cx + hw - post_w / 2, mid_y, cz - hd + post_d / 2, post_w, th, post_d, post_color)

        # ================================================================
        # 2. TOP & BOTTOM PLATES / CABLE TRAY LIDS
        # ================================================================
        plate_color = (0.12, 0.13, 0.15)
        draw_box(cx, cy + 0.03, cz, self.width_m, 0.06, self.depth_m, plate_color)       # Bottom plate
        draw_box(cx, cy + th - 0.03, cz, self.width_m, 0.06, self.depth_m, plate_color)  # Top plate/lid

        # Top cable entry brush strip (dark foam strip)
        draw_box(cx, cy + th - 0.005, cz + hd * 0.4, self.width_m - 0.06, 0.010, hd * 0.18, (0.08, 0.08, 0.09))

        # ================================================================
        # 3. SIDE PANELS: Perforated Vented Steel Panels
        # ================================================================
        # Outer panel skin (mid-dark charcoal)
        side_panel_color = (0.15, 0.16, 0.18)
        panel_inner_color = (0.13, 0.14, 0.16)
        draw_box(cx - hw + 0.008, mid_y, cz, 0.016, th - 0.10, self.depth_m - 0.09, side_panel_color)
        draw_box(cx + hw - 0.008, mid_y, cz, 0.016, th - 0.10, self.depth_m - 0.09, side_panel_color)

        # Horizontal stiffener ribs on side panels (every ~20cm)
        rib_color = (0.10, 0.11, 0.13)
        for rib_i in range(1, 10):
            rib_y = cy + 0.08 + (rib_i / 10.0) * (th - 0.10)
            draw_box(cx - hw + 0.004, rib_y, cz, 0.006, 0.015, self.depth_m - 0.12, rib_color)
            draw_box(cx + hw - 0.004, rib_y, cz, 0.006, 0.015, self.depth_m - 0.12, rib_color)

        # Perforation slot rows (visual slits evenly spaced — dark cutout rows)
        perf_color = (0.06, 0.07, 0.08)
        for slot_i in range(8):
            slot_y = cy + 0.25 + slot_i * 0.22
            draw_box(cx - hw + 0.014, slot_y, cz, 0.002, 0.018, self.depth_m * 0.55, perf_color)
            draw_box(cx + hw - 0.014, slot_y, cz, 0.002, 0.018, self.depth_m * 0.55, perf_color)

        # ================================================================
        # 4. REAR PANEL: Cable Management Backplane
        # ================================================================
        rear_panel_color = (0.13, 0.14, 0.16)
        draw_box(cx, mid_y, cz - hd + 0.010, self.width_m - 0.08, th - 0.10, 0.020, rear_panel_color)

        # Rear PDU (vertical power strip bar, right side)
        pdu_color = (0.09, 0.10, 0.12)
        draw_box(cx + hw - 0.065, mid_y, cz - hd + 0.022, 0.060, th * 0.70, 0.040, pdu_color)
        # PDU outlets (small gray bumps)
        for pdu_i in range(10):
            outlet_y = cy + 0.18 + pdu_i * 0.14
            draw_box(cx + hw - 0.065, outlet_y, cz - hd + 0.044, 0.030, 0.018, 0.008, (0.25, 0.26, 0.28))

        # ================================================================
        # 5. FRONT MOUNTING RAILS (19" Standard — Brushed Silver)
        # ================================================================
        rail_color = (0.28, 0.30, 0.33)  # Brushed stainless steel
        rail_w = 0.022
        rail_x_offset = 0.229  # Standard 19" rack rail spacing (half = 9.5in = ~0.241m - post)
        rail_z = cz + hd - 0.060  # Set slightly back from front face

        draw_box(cx - rail_x_offset, rail_y_base + rail_h / 2, rail_z, rail_w, rail_h, 0.018, rail_color)
        draw_box(cx + rail_x_offset, rail_y_base + rail_h / 2, rail_z, rail_w, rail_h, 0.018, rail_color)

        # Rail U-slot screw holes (small notch markings every 1U)
        screw_color = (0.18, 0.20, 0.22)
        for u in range(1, 43, 3):  # Every 3U for performance
            uy = rail_y_base + (u - 0.5) * self.u_height_m
            draw_box(cx - rail_x_offset, uy, rail_z + 0.009, 0.006, 0.008, 0.002, screw_color)
            draw_box(cx + rail_x_offset, uy, rail_z + 0.009, 0.006, 0.008, 0.002, screw_color)

        # ================================================================
        # 6. U-SLOT NUMBER MARKINGS STRIP (Left panel, front)
        # ================================================================
        # Thin number label strip (anodized aluminum, light)
        label_strip_color = (0.35, 0.37, 0.40)
        draw_box(cx - hw + 0.024, rail_y_base + rail_h / 2, cz + hd - 0.032, 0.018, rail_h, 0.012, label_strip_color)

        # Every 5U: bright tick mark
        tick_color = (0.55, 0.58, 0.62)
        for u5 in range(5, 43, 5):
            ty = rail_y_base + (u5 - 0.5) * self.u_height_m
            draw_box(cx - hw + 0.024, ty, cz + hd - 0.028, 0.018, 0.004, 0.006, tick_color)
            # Every 10U: wider bright accent tick
            if u5 % 10 == 0:
                draw_box(cx - hw + 0.024, ty, cz + hd - 0.028, 0.018, 0.006, 0.008, (0.72, 0.75, 0.80))

        # ================================================================
        # 7. FRONT DOOR: Perforated Mesh Panel
        # ================================================================
        door_face_color = (0.14, 0.155, 0.175)

        # Main door face panel (slightly inset from front posts)
        draw_box(cx, mid_y, cz + hd - 0.010, self.width_m - 0.09, th - 0.13, 0.014, door_face_color)

        # Door mesh perforation rows (dark slots across full width)
        mesh_color = (0.09, 0.10, 0.11)
        for mesh_row in range(18):
            row_y = cy + 0.12 + mesh_row * 0.10
            draw_box(cx, row_y, cz + hd - 0.004, self.width_m * 0.80, 0.022, 0.004, mesh_color)

        # Door hinge strip (left vertical bar)
        hinge_color = (0.10, 0.11, 0.12)
        draw_box(cx - hw + 0.055, mid_y, cz + hd - 0.003, 0.012, th - 0.12, 0.018, hinge_color)

        # Door handle latch (front center-right)
        handle_bar_color = (0.28, 0.30, 0.34)
        handle_x = cx + hw - 0.080
        draw_box(handle_x, cy + th * 0.52, cz + hd + 0.002, 0.018, 0.060, 0.022, handle_bar_color)
        # Handle grip knob (bright chrome)
        draw_box(handle_x, cy + th * 0.52, cz + hd + 0.013, 0.012, 0.012, 0.010, (0.65, 0.68, 0.72))

        # Door lock cylinder (small)
        draw_box(handle_x, cy + th * 0.52 - 0.050, cz + hd + 0.012, 0.010, 0.010, 0.012, (0.22, 0.24, 0.26))

        # ================================================================
        # 8. CABLE MANAGEMENT ARM BARS (Front horizontal brush bars at rack base)
        # ================================================================
        cmb_color = (0.12, 0.13, 0.15)
        cmb_z = cz + hd - 0.024
        for cmb_i in [0.12, 0.22]:
            draw_box(cx, cy + cmb_i, cmb_z, self.width_m - 0.09, 0.020, 0.030, cmb_color)

        # ================================================================
        # 9. FRONT SYSTEM STATUS LED STRIP (Top of rack, front face)
        # ================================================================
        # Status bar panel (thin strip below top plate)
        status_bar_y = cy + th - 0.075
        draw_box(cx, status_bar_y, cz + hd - 0.007, self.width_m - 0.09, 0.025, 0.010, (0.10, 0.11, 0.13))

        # Power LED (green)
        draw_box(cx - hw + 0.085, status_bar_y, cz + hd + 0.001, 0.010, 0.010, 0.004,
                 GraphicsConfig.COLOR_LED_GREEN if len(self.devices) > 0 else GraphicsConfig.COLOR_LED_OFF)
        # Activity LED (amber/orange)
        draw_box(cx - hw + 0.110, status_bar_y, cz + hd + 0.001, 0.010, 0.010, 0.004,
                 GraphicsConfig.COLOR_LED_AMBER if len(self.devices) > 0 else GraphicsConfig.COLOR_LED_OFF)
        # Fault LED (red when no devices)
        draw_box(cx - hw + 0.135, status_bar_y, cz + hd + 0.001, 0.010, 0.010, 0.004,
                 (0.85, 0.12, 0.10) if len(self.devices) == 0 else GraphicsConfig.COLOR_LED_OFF)

        # ================================================================
        # 10. RACK IDENTITY BADGE PLATE (Top-Front colored label)
        # ================================================================
        if "A" in self.rack_id:
            sign_color = (0.15, 0.40, 0.80)
            sign_accent = (0.25, 0.55, 0.95)
        elif "B" in self.rack_id:
            sign_color = (0.10, 0.55, 0.35)
            sign_accent = (0.18, 0.75, 0.48)
        else:
            sign_color = (0.72, 0.35, 0.08)
            sign_accent = (0.90, 0.50, 0.12)

        badge_y = cy + th - 0.042
        # Badge background plate
        draw_box(cx, badge_y, cz + hd + 0.006, 0.24, 0.038, 0.008, sign_color)
        # Badge accent left stripe
        draw_box(cx - 0.104, badge_y, cz + hd + 0.009, 0.022, 0.028, 0.004, sign_accent)

        # ================================================================
        # 11. RENDER INSTALLED DEVICES
        # ================================================================
        for device in self.devices:
            if device.start_u is None or not device.position:
                continue
            dev_cx, dev_cy, dev_cz = device.position

            if device.device_type == "Router":
                self._router_model.render(device, dev_cx, dev_cy, dev_cz)
            elif device.device_type == "Switch":
                self._switch_model.render(device, dev_cx, dev_cy, dev_cz)
            elif device.device_type == "PC":
                self._pc_model.render(device, dev_cx, dev_cy, dev_cz)

        # ================================================================
        # 12. RACK WIREFRAME OUTLINE (Top-level structural emphasis)
        # ================================================================
        draw_wire_box(cx, mid_y, cz, self.width_m + 0.002, th + 0.002, self.depth_m + 0.002,
                      (0.08, 0.09, 0.10), line_width=0.8)


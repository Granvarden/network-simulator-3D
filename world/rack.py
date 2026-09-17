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

        # Display list cache for static rack frame enclosure
        self._frame_display_list: Optional[int] = None

    def __del__(self):
        if self._frame_display_list is not None:
            try:
                glDeleteLists(self._frame_display_list, 1)
            except Exception:
                pass

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

    def _draw_enclosure_frame(self, cx: float, cy: float, cz: float, hw: float, hd: float, th: float) -> None:
        """Draw static 42U rack enclosure frame, casters, rails, PDUs, door, and signage."""
        # 1. 4 Corner Vertical Posts (Solid dark steel, elevated +3mm above floor plane to eliminate Z-fighting)
        post_size = 0.04
        post_color = GraphicsConfig.COLOR_RACK_FRAME
        post_h = th - 0.003
        post_cy = cy + 0.003 + post_h / 2.0
        draw_box(cx - hw + 0.02, post_cy, cz - hd + 0.02, post_size, post_h, post_size, post_color)
        draw_box(cx + hw - 0.02, post_cy, cz - hd + 0.02, post_size, post_h, post_size, post_color)
        draw_box(cx - hw + 0.02, post_cy, cz + hd - 0.02, post_size, post_h, post_size, post_color)
        draw_box(cx + hw - 0.02, post_cy, cz + hd - 0.02, post_size, post_h, post_size, post_color)

        # 2. Leveling Feet & Heavy-Duty Dual Caster Wheels (Bottom faces >= cy + 0.003 to clear floor & grid)
        for cx_off in (-hw + 0.038, hw - 0.038):
            for cz_off in (-hd + 0.038, hd - 0.038):
                # Caster bracket housing
                draw_box(cx + cx_off, cy + 0.016, cz + cz_off, 0.032, 0.024, 0.032, (0.24, 0.26, 0.28))
                # Dark polyurethane wheel
                draw_box(cx + cx_off, cy + 0.008, cz + cz_off, 0.018, 0.010, 0.026, (0.07, 0.07, 0.08))
                # Adjacent steel leveling foot screw
                draw_box(cx + cx_off * 0.75, cy + 0.007, cz + cz_off, 0.014, 0.008, 0.014, (0.65, 0.68, 0.72))

        # 3. Top & Bottom Enclosure Plates
        plate_color = (0.12, 0.13, 0.15)
        draw_box(cx, cy + 0.0315, cz, self.width_m - 0.002, 0.057, self.depth_m - 0.002, plate_color)
        draw_box(cx, cy + th - 0.03, cz, self.width_m - 0.002, 0.06, self.depth_m - 0.002, plate_color)

        # 4. Top Roof Details: Cable Brush Entry Strips & Exhaust Fan Grilles
        # Rear-top cable entry brush strip
        draw_box(cx, cy + th + 0.002, cz - 0.22, 0.32, 0.003, 0.09, (0.45, 0.48, 0.52))
        draw_box(cx, cy + th + 0.004, cz - 0.22, 0.28, 0.002, 0.06, (0.06, 0.06, 0.07))
        # Front-top cable entry brush strip
        draw_box(cx, cy + th + 0.002, cz + 0.22, 0.32, 0.003, 0.09, (0.45, 0.48, 0.52))
        draw_box(cx, cy + th + 0.004, cz + 0.22, 0.28, 0.002, 0.06, (0.06, 0.06, 0.07))
        # Dual roof exhaust fans
        for fz in (cz - 0.06, cz + 0.06):
            draw_box(cx, cy + th + 0.002, fz, 0.13, 0.002, 0.11, (0.25, 0.28, 0.32))
            draw_box(cx, cy + th + 0.004, fz, 0.10, 0.002, 0.08, (0.05, 0.06, 0.07))

        # 5. Left & Right Perforated Side Panels with Quarter-Turn Latches
        panel_color = (0.16, 0.17, 0.19)
        draw_box(cx - hw + 0.005, cy + th / 2.0, cz, 0.01, th - 0.12, self.depth_m - 0.08, panel_color)
        draw_box(cx + hw - 0.005, cy + th / 2.0, cz, 0.01, th - 0.12, self.depth_m - 0.08, panel_color)
        # Recessed slam latches at mid-height on side panels
        draw_box(cx - hw - 0.001, cy + th / 2.0, cz, 0.003, 0.05, 0.035, (0.30, 0.33, 0.37))
        draw_box(cx + hw + 0.001, cy + th / 2.0, cz, 0.003, 0.05, 0.035, (0.30, 0.33, 0.37))
        # Rear corner grounding safety bonding strap
        draw_box(cx - hw + 0.015, cy + 0.06, cz - hd + 0.04, 0.008, 0.025, 0.008, (0.85, 0.75, 0.15))

        # 6. Dual 0U Vertical Power Distribution Units (PDUs) on Rear Posts
        # PDU-A (Primary Feed, Green load indicator) on Left-Rear Post
        pdu_a_x = cx - 0.22
        pdu_z = cz - hd + 0.065
        pdu_h = 1.65
        pdu_cy = cy + 0.20 + pdu_h / 2.0
        draw_box(pdu_a_x, pdu_cy, pdu_z, 0.045, pdu_h, 0.035, (0.12, 0.13, 0.16))
        # PDU-A LED telemetry load display
        draw_box(pdu_a_x, cy + 1.78, pdu_z + 0.019, 0.032, 0.040, 0.002, (0.10, 0.95, 0.35))
        # PDU-A outlet banks
        for b in range(6):
            draw_box(pdu_a_x, cy + 0.40 + b * 0.22, pdu_z + 0.0185, 0.028, 0.10, 0.002, (0.03, 0.03, 0.04))
            draw_box(pdu_a_x + 0.010, cy + 0.40 + b * 0.22 + 0.04, pdu_z + 0.0195, 0.004, 0.004, 0.001, (0.10, 0.90, 0.30))

        # PDU-B (Redundant Feed, Blue load indicator) on Right-Rear Post
        pdu_b_x = cx + 0.22
        draw_box(pdu_b_x, pdu_cy, pdu_z, 0.045, pdu_h, 0.035, (0.12, 0.13, 0.16))
        # PDU-B LED telemetry load display
        draw_box(pdu_b_x, cy + 1.78, pdu_z + 0.019, 0.032, 0.040, 0.002, (0.15, 0.65, 1.0))
        # PDU-B outlet banks
        for b in range(6):
            draw_box(pdu_b_x, cy + 0.40 + b * 0.22, pdu_z + 0.0185, 0.028, 0.10, 0.002, (0.03, 0.03, 0.04))
            draw_box(pdu_b_x - 0.010, cy + 0.40 + b * 0.22 + 0.04, pdu_z + 0.0195, 0.004, 0.004, 0.001, (0.15, 0.65, 1.0))

        # 7. 19" Mounting Rails (Vertical silver/gray rails resting flush behind device ear front face)
        rail_w = 0.02
        rail_x = 0.235
        rail_color = GraphicsConfig.COLOR_RACK_RAILS
        rail_y = cy + 0.08 + (42 * self.u_height_m) / 2.0
        rail_h = 42 * self.u_height_m
        draw_box(cx - rail_x, rail_y, cz + 0.385, rail_w, rail_h, 0.02, rail_color)
        draw_box(cx + rail_x, rail_y, cz + 0.385, rail_w, rail_h, 0.02, rail_color)

        # EIA-310-D Unit markings & contrast ticks on 19" rails (every 5U)
        for rx in (cx - rail_x, cx + rail_x):
            for unit in (5, 10, 15, 20, 25, 30, 35, 40):
                uy = cy + 0.08 + (unit - 0.5) * self.u_height_m
                draw_box(rx, uy, cz + 0.3955, 0.008, 0.004, 0.001, (0.85, 0.88, 0.92))
            for u in (2, 8, 12, 18, 22, 28, 32, 38):
                uy = cy + 0.08 + (u - 0.5) * self.u_height_m
                draw_box(rx, uy, cz + 0.3952, 0.005, 0.005, 0.0008, (0.06, 0.07, 0.08))

        # 8. Front Ventilated Door Frame & Industrial Swing Handle
        door_frame_col = (0.13, 0.14, 0.16)
        # Top header & bottom sill
        draw_box(cx, cy + th - 0.045, cz + hd + 0.006, self.width_m - 0.01, 0.030, 0.012, door_frame_col)
        draw_box(cx, cy + 0.045, cz + hd + 0.006, self.width_m - 0.01, 0.025, 0.012, door_frame_col)
        # Left & right upright stiles
        draw_box(cx - hw + 0.012, cy + th / 2.0, cz + hd + 0.006, 0.022, th - 0.09, 0.012, door_frame_col)
        draw_box(cx + hw - 0.012, cy + th / 2.0, cz + hd + 0.006, 0.022, th - 0.09, 0.012, door_frame_col)
        # Industrial swing-handle combination lock on right stile
        draw_box(cx + hw - 0.012, cy + 1.05, cz + hd + 0.015, 0.016, 0.12, 0.008, (0.28, 0.30, 0.34))
        draw_box(cx + hw - 0.012, cy + 1.03, cz + hd + 0.021, 0.008, 0.07, 0.006, (0.75, 0.78, 0.82))
        draw_box(cx + hw - 0.012, cy + 1.09, cz + hd + 0.020, 0.010, 0.022, 0.003, (0.10, 0.12, 0.15))

        # 10. Rack ID Sign at Top with Status Beacon
        sign_color = (0.2, 0.5, 0.9) if "A" in self.rack_id else ((0.2, 0.7, 0.5) if "B" in self.rack_id else (0.9, 0.5, 0.2))
        beacon_color = (0.25, 0.65, 1.0) if "A" in self.rack_id else ((0.25, 0.95, 0.45) if "B" in self.rack_id else (1.0, 0.65, 0.2))
        # Beveled sign plate backing frame
        draw_box(cx, cy + th - 0.04, cz + hd + 0.006, 0.32, 0.056, 0.008, (0.10, 0.11, 0.13))
        # High-contrast acrylic color placard
        draw_box(cx, cy + th - 0.04, cz + hd + 0.012, 0.28, 0.042, 0.004, sign_color)
        # Overhead status beacon light on top of rack
        draw_box(cx, cy + th + 0.006, cz + hd + 0.008, 0.035, 0.012, 0.035, (0.15, 0.17, 0.20))
        draw_box(cx, cy + th + 0.016, cz + hd + 0.008, 0.024, 0.010, 0.024, beacon_color)

    def render(self) -> None:
        """Render the 42U rack enclosure, mounting rails, PDUs, casters, door frame, and installed devices."""
        cx, cy, cz = self.position
        hw = self.width_m / 2.0
        hd = self.depth_m / 2.0
        th = self.total_height_m

        try:
            if self._frame_display_list is None:
                self._frame_display_list = glGenLists(1)
                glNewList(self._frame_display_list, GL_COMPILE)
                self._draw_enclosure_frame(cx, cy, cz, hw, hd, th)
                glEndList()
            glCallList(self._frame_display_list)
        except Exception:
            # Fallback for headless tests without active GL context
            self._draw_enclosure_frame(cx, cy, cz, hw, hd, th)

        # 9. Render Installed Devices
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

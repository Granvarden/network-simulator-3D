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

        # Calculate exact 3D center position
        center_y = self.get_world_y_for_u(start_u) + (device.u_height * self.u_height_m) / 2.0
        device.position = (self.position[0], center_y, self.position[2])

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
        """Render the 42U rack enclosure, mounting rails, and all installed devices."""
        cx, cy, cz = self.position
        hw = self.width_m / 2.0
        hd = self.depth_m / 2.0
        th = self.total_height_m

        # 4 Corner Vertical Posts (Solid dark steel)
        post_size = 0.04
        post_color = GraphicsConfig.COLOR_RACK_FRAME
        draw_box(cx - hw + 0.02, cy + th / 2.0, cz - hd + 0.02, post_size, th, post_size, post_color)
        draw_box(cx + hw - 0.02, cy + th / 2.0, cz - hd + 0.02, post_size, th, post_size, post_color)
        draw_box(cx - hw + 0.02, cy + th / 2.0, cz + hd - 0.02, post_size, th, post_size, post_color)
        draw_box(cx + hw - 0.02, cy + th / 2.0, cz + hd - 0.02, post_size, th, post_size, post_color)

        # Top & Bottom Plates
        plate_color = (0.12, 0.13, 0.15)
        draw_box(cx, cy + 0.03, cz, self.width_m, 0.06, self.depth_m, plate_color)
        draw_box(cx, cy + th - 0.03, cz, self.width_m, 0.06, self.depth_m, plate_color)

        # Left & Right Perforated Side Panels (Dark metal)
        panel_color = (0.16, 0.17, 0.19)
        draw_box(cx - hw + 0.005, cy + th / 2.0, cz, 0.01, th - 0.12, self.depth_m - 0.08, panel_color)
        draw_box(cx + hw - 0.005, cy + th / 2.0, cz, 0.01, th - 0.12, self.depth_m - 0.08, panel_color)

        # 19" Mounting Rails (Vertical silver/gray rails)
        rail_w = 0.02
        rail_x = 0.24  # 0.48m spacing between rails
        rail_color = GraphicsConfig.COLOR_RACK_RAILS
        rail_y = cy + 0.08 + (42 * self.u_height_m) / 2.0
        rail_h = 42 * self.u_height_m
        draw_box(cx - rail_x, rail_y, cz + 0.40, rail_w, rail_h, 0.02, rail_color)
        draw_box(cx + rail_x, rail_y, cz + 0.40, rail_w, rail_h, 0.02, rail_color)

        # Render Installed Devices
        for device in self.devices:
            if device.start_u is None:
                continue
            dev_cy = self.get_world_y_for_u(device.start_u) + (device.u_height * self.u_height_m) / 2.0
            dev_cz = cz + 0.12  # Mounted in front rail

            if device.device_type == "Router":
                self._router_model.render(device, cx, dev_cy, dev_cz)
            elif device.device_type == "Switch":
                self._switch_model.render(device, cx, dev_cy, dev_cz)
            elif device.device_type == "PC":
                self._pc_model.render(device, cx, dev_cy, dev_cz)

        # Rack ID Sign at Top
        sign_color = (0.2, 0.5, 0.9) if "A" in self.rack_id else ((0.2, 0.7, 0.5) if "B" in self.rack_id else (0.9, 0.5, 0.2))
        draw_box(cx, cy + th - 0.04, cz + hd + 0.005, 0.30, 0.05, 0.01, sign_color)

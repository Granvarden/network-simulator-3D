"""Data Center / Network Lab Room geometry, boundary walls, and detailed infrastructure."""

from typing import List, Optional, Tuple
from OpenGL.GL import *
from rendering.primitives import draw_box, draw_grid_plane
from config.game_config import GameConfig
from config.graphics_config import GraphicsConfig


class Room:
    """20m x 15m enterprise data center room environment with full infrastructure detailing."""

    def __init__(self):
        self.width: float = GameConfig.ROOM_WIDTH    # 20.0m (-10.0 to +10.0)
        self.depth: float = GameConfig.ROOM_DEPTH    # 15.0m (-7.5 to +7.5)
        self.height: float = GameConfig.ROOM_HEIGHT  # 4.0m (0.0 to 4.0)
        self._display_list: Optional[int] = None

    def __del__(self):
        if self._display_list is not None:
            try:
                glDeleteLists(self._display_list, 1)
            except Exception:
                pass

    def _draw_room_geometry(self, hw: float, hd: float) -> None:
        """Render all static room architectural meshes."""
        # 1. Raised Floor with 1m x 1m Server Room Grid Tiles
        draw_grid_plane(
            width=self.width,
            depth=self.depth,
            tile_size=1.0,
            y_pos=0.0,
            color_plane=GraphicsConfig.COLOR_FLOOR_TILE,
            color_grid=GraphicsConfig.COLOR_FLOOR_GRID
        )

        # 2. Base Boundary Walls & Baseboard Trims
        self._render_boundary_walls(hw, hd)

        # 3. Ceiling Slab, HVAC Ducts, Sprinklers & Troffer LED Lighting
        self._render_ceiling_and_hvac(hw, hd)

        # 4. West Wall: Main 480V PDU Electrical Substation & Climate Telemetry
        self._render_west_wall_power_station(hw, hd)

        # 5. East Wall: FM-200 Clean Agent Fire Suppression & Safety Equipment
        self._render_east_wall_fire_safety(hw, hd)

        # 6. North Wall: Backlit Datacenter Signage & Overhead Cable Dropouts
        self._render_north_wall_signage_and_dropouts(hw, hd)

        # 7. South Wall: Security Air-Lock Entrance Doors & Illuminated Exit Sign
        self._render_south_wall_security_entrance(hw, hd)

    def render(self) -> None:
        hw = self.width / 2.0
        hd = self.depth / 2.0

        try:
            if self._display_list is None:
                self._display_list = glGenLists(1)
                glNewList(self._display_list, GL_COMPILE)
                self._draw_room_geometry(hw, hd)
                glEndList()
            glCallList(self._display_list)
        except Exception:
            # Fallback for headless tests without active GL context
            self._draw_room_geometry(hw, hd)

    def _render_boundary_walls(self, hw: float, hd: float) -> None:
        wall_color = GraphicsConfig.COLOR_WALL
        trim_color = GraphicsConfig.COLOR_WALL_TRIM

        # North Wall (Z = -hd)
        draw_box(0.0, self.height / 2.0, -hd - 0.05, self.width, self.height, 0.1, wall_color)
        draw_box(0.0, 0.1015, -hd + 0.02, self.width, 0.197, 0.04, trim_color)

        # South Wall (Z = +hd)
        draw_box(0.0, self.height / 2.0, hd + 0.05, self.width, self.height, 0.1, wall_color)
        draw_box(0.0, 0.1015, hd - 0.02, self.width, 0.197, 0.04, trim_color)

        # West Wall (X = -hw)
        draw_box(-hw - 0.05, self.height / 2.0, 0.0, 0.1, self.height, self.depth, wall_color)
        draw_box(-hw + 0.02, 0.1015, 0.0, 0.04, 0.197, self.depth, trim_color)

        # East Wall (X = +hw)
        draw_box(hw + 0.05, self.height / 2.0, 0.0, 0.1, self.height, self.depth, wall_color)
        draw_box(hw - 0.02, 0.1015, 0.0, 0.04, 0.197, self.depth, trim_color)

    def _render_ceiling_and_hvac(self, hw: float, hd: float) -> None:
        # Ceiling Concrete Slab
        draw_box(0.0, self.height + 0.05, 0.0, self.width, 0.1, self.depth, GraphicsConfig.COLOR_CEILING)

        # Modern Recessed Troffer LED Lighting Fixtures
        for z_light in (-5.5, -2.0, 1.8, 5.5):
            for x_light in (-5.5, 0.0, 5.5):
                # Aluminum extruded bezel housing
                draw_box(x_light, self.height - 0.04, z_light, 2.5, 0.06, 0.50, (0.32, 0.35, 0.38))
                # Diffuser frame rim
                draw_box(x_light, self.height - 0.07, z_light, 2.3, 0.02, 0.42, (0.75, 0.78, 0.82))
                # Glowing opal LED diffuser panel
                draw_box(x_light, self.height - 0.082, z_light, 2.2, 0.015, 0.35, (0.95, 0.98, 1.0))

        # HVAC Supply Air Duct System (Spanning West to East at Y = 3.68, Z = 0.0)
        duct_color = (0.68, 0.71, 0.75)
        seam_color = (0.45, 0.48, 0.52)
        draw_box(0.0, 3.68, 0.0, self.width - 2.0, 0.32, 0.65, duct_color)
        # Duct galvanized seam joints
        for dx in (-6.0, -3.0, 0.0, 3.0, 6.0):
            draw_box(dx, 3.68, 0.0, 0.05, 0.33, 0.66, seam_color)
            # Steel threaded support rods to ceiling
            draw_box(dx, 3.90, -0.30, 0.016, 0.20, 0.016, (0.50, 0.52, 0.55))
            draw_box(dx, 3.90, 0.30, 0.016, 0.20, 0.016, (0.50, 0.52, 0.55))
        # Directional Air Diffuser Louvers blowing cool air
        for lx in (-5.5, -1.8, 1.8, 5.5):
            draw_box(lx, 3.51, 0.0, 0.60, 0.02, 0.50, (0.88, 0.90, 0.94))
            draw_box(lx, 3.495, 0.0, 0.50, 0.01, 0.40, (0.18, 0.20, 0.23))

        # Red Fire Sprinkler Pipe Distribution Network (At Y = 3.45, Z = -3.2)
        pipe_color = (0.80, 0.12, 0.12)
        draw_box(0.0, 3.45, -3.2, self.width - 2.0, 0.035, 0.035, pipe_color)
        # Brass pendent sprinkler heads
        for px in (-7.0, -3.5, 0.0, 3.5, 7.0):
            draw_box(px, 3.40, -3.2, 0.014, 0.065, 0.014, pipe_color)
            draw_box(px, 3.36, -3.2, 0.032, 0.014, 0.032, (0.88, 0.75, 0.22))

        # Ceiling Smoke / Thermal Optical Detectors
        for sx, sz in ((-3.5, -3.5), (3.5, -3.5), (0.0, 3.8), (-4.5, 3.8), (4.5, 3.8)):
            draw_box(sx, 3.96, sz, 0.16, 0.03, 0.16, (0.92, 0.93, 0.95))
            draw_box(sx, 3.94, sz, 0.016, 0.01, 0.016, (0.15, 0.98, 0.35))

        # High-Detail Overhead Cable Ladder Trays with Realistic Rungs & Looms
        tray_color = (0.85, 0.70, 0.15)
        for tray_z in (-6.65, 3.50):
            # Dual longitudinal stringer rails
            draw_box(0.0, 3.20, tray_z - 0.22, self.width - 2.0, 0.05, 0.03, tray_color)
            draw_box(0.0, 3.20, tray_z + 0.22, self.width - 2.0, 0.05, 0.03, tray_color)
            # Transverse ladder cross-rungs
            for rung_idx in range(-9, 10):
                draw_box(rung_idx * 0.90, 3.19, tray_z, 0.035, 0.02, 0.44, tray_color)

        # Cable Bundles resting inside trays
        # Ethernet Blue bundle (Tray 1)
        draw_box(0.0, 3.22, -6.74, self.width - 2.2, 0.04, 0.14, (0.12, 0.38, 0.88))
        # Power Feeder Black bundle (Tray 1)
        draw_box(0.0, 3.22, -6.56, self.width - 2.2, 0.045, 0.15, (0.10, 0.10, 0.12))
        # Multimode Aqua fiber trunk bundle (Tray 2)
        draw_box(0.0, 3.22, 3.50, self.width - 2.2, 0.035, 0.18, (0.10, 0.75, 0.82))

    def _render_west_wall_power_station(self, hw: float, hd: float) -> None:
        """Render electrical PDU substation, circuit breakers, and EPO station on West wall."""
        # 1. Primary 480V/208V PDU Electrical Switchboard Cabinet
        pdu1_x = -hw + 0.22  # X = -9.78
        draw_box(pdu1_x, 1.15, -3.5, 0.42, 2.25, 1.20, (0.18, 0.20, 0.23))
        # Bezel frame & safety orange warning stripe
        draw_box(pdu1_x + 0.211, 1.15, -3.5, 0.005, 2.23, 1.18, (0.12, 0.14, 0.16))
        draw_box(pdu1_x + 0.214, 1.15, -3.5, 0.005, 0.08, 1.14, (0.95, 0.48, 0.10))
        # Digital telemetry voltage/power meter display
        draw_box(pdu1_x + 0.215, 1.65, -3.5, 0.005, 0.14, 0.32, (0.05, 0.12, 0.18))
        draw_box(pdu1_x + 0.218, 1.65, -3.5, 0.005, 0.10, 0.28, (0.15, 0.85, 0.95))
        # Rows of Miniature Circuit Breakers
        for row_y in (0.85, 1.15):
            draw_box(pdu1_x + 0.215, row_y, -3.5, 0.005, 0.16, 0.80, (0.08, 0.09, 0.11))
            for bi in range(6):
                draw_box(pdu1_x + 0.219, row_y, -3.80 + bi * 0.12, 0.005, 0.04, 0.03, (0.18, 0.85, 0.30))
        # Heavy rotary emergency isolator switch
        draw_box(pdu1_x + 0.216, 1.95, -3.5, 0.006, 0.08, 0.08, (0.88, 0.15, 0.15))
        # High Voltage Warning Placard
        draw_box(pdu1_x + 0.216, 1.40, -3.5, 0.004, 0.12, 0.28, (0.95, 0.85, 0.10))

        # 2. Secondary UPS Battery Inverter Cabinet
        pdu2_x = -hw + 0.22  # X = -9.78
        draw_box(pdu2_x, 1.15, -2.0, 0.42, 2.25, 1.00, (0.18, 0.20, 0.23))
        # Battery Health Status LEDs
        for i in range(4):
            draw_box(pdu2_x + 0.215, 1.70 - i * 0.04, -2.0, 0.005, 0.02, 0.02, (0.20, 0.92, 0.35))
        # Cooling air louvers on lower cabinet
        draw_box(pdu2_x + 0.215, 0.60, -2.0, 0.005, 0.45, 0.80, (0.10, 0.11, 0.13))

        # 3. Heavy EMT Metal Conduit Pipes rising to ceiling tray
        for cz_pos in (-3.8, -3.5, -3.2, -2.0):
            draw_box(pdu1_x, 2.90, cz_pos, 0.05, 1.25, 0.05, (0.65, 0.68, 0.72))

        # 4. Emergency Power Off (EPO) Wall Station (Eye level, bright yellow/red)
        draw_box(-hw + 0.04, 1.50, -0.5, 0.05, 0.22, 0.18, (0.95, 0.85, 0.10))
        draw_box(-hw + 0.07, 1.50, -0.5, 0.03, 0.07, 0.07, (0.90, 0.12, 0.12))
        draw_box(-hw + 0.08, 1.50, -0.5, 0.015, 0.12, 0.11, (0.75, 0.85, 0.95))
        draw_box(-hw + 0.04, 1.65, -0.5, 0.052, 0.05, 0.24, (0.90, 0.12, 0.12))

        # 5. CRAC Environmental & Temperature Wall Controller
        draw_box(-hw + 0.04, 1.55, 1.5, 0.04, 0.32, 0.24, (0.92, 0.94, 0.96))
        draw_box(-hw + 0.062, 1.60, 1.5, 0.005, 0.10, 0.18, (0.12, 0.75, 0.85))
        draw_box(-hw + 0.062, 1.46, 1.5, 0.005, 0.018, 0.018, (0.20, 0.95, 0.35))

        # 6. Synchronized Master Data Center Wall Clock
        draw_box(-hw + 0.03, 2.80, 0.0, 0.03, 0.32, 0.32, (0.12, 0.13, 0.15))
        draw_box(-hw + 0.047, 2.80, 0.0, 0.005, 0.28, 0.28, (0.95, 0.96, 0.98))
        draw_box(-hw + 0.052, 2.80, 0.0, 0.004, 0.10, 0.01, (0.88, 0.12, 0.12))

    def _render_east_wall_fire_safety(self, hw: float, hd: float) -> None:
        """Render fire suppression cylinder, safety equipment, and conduits on East wall."""
        # 1. FM-200 Clean Agent Fire Suppression Master Control Cabinet
        cyl_x = hw - 0.22  # X = 9.78
        draw_box(cyl_x, 1.15, -3.0, 0.42, 2.15, 0.90, (0.78, 0.14, 0.14))
        # Cylinder release head manifold
        draw_box(cyl_x, 2.28, -3.0, 0.15, 0.14, 0.15, (0.72, 0.75, 0.80))
        # Pressure gauge dial
        draw_box(cyl_x - 0.215, 1.70, -3.0, 0.005, 0.10, 0.10, (0.95, 0.95, 0.95))
        draw_box(cyl_x - 0.218, 1.70, -3.0, 0.005, 0.06, 0.06, (0.15, 0.85, 0.25))
        # Manual discharge pull box
        draw_box(cyl_x - 0.215, 1.30, -3.0, 0.005, 0.12, 0.10, (0.95, 0.85, 0.12))
        # Caution safety banner
        draw_box(cyl_x - 0.215, 1.95, -3.0, 0.005, 0.08, 0.75, (0.92, 0.94, 0.96))

        # 2. Safety First Aid Metal Station
        draw_box(hw - 0.04, 1.50, 0.5, 0.04, 0.35, 0.28, (0.95, 0.96, 0.98))
        # Green cross emblem
        draw_box(hw - 0.062, 1.50, 0.5, 0.005, 0.16, 0.05, (0.12, 0.75, 0.25))
        draw_box(hw - 0.062, 1.50, 0.5, 0.005, 0.05, 0.16, (0.12, 0.75, 0.25))

        # 3. Emergency Eyewash Station Bracket & Bottles
        draw_box(hw - 0.04, 1.40, 1.4, 0.05, 0.30, 0.22, (0.15, 0.65, 0.25))
        draw_box(hw - 0.08, 1.40, 1.35, 0.06, 0.18, 0.06, (0.85, 0.92, 0.98))
        draw_box(hw - 0.08, 1.40, 1.45, 0.06, 0.18, 0.06, (0.85, 0.92, 0.98))

        # 4. Horizontal EMT Conduit Pipe & Junction Boxes
        draw_box(hw - 0.03, 2.80, 0.0, 0.035, 0.035, self.depth - 2.0, (0.65, 0.68, 0.72))
        for jz in (-3.0, 0.0, 3.0):
            draw_box(hw - 0.05, 2.80, jz, 0.045, 0.12, 0.12, (0.35, 0.38, 0.42))

    def _render_north_wall_signage_and_dropouts(self, hw: float, hd: float) -> None:
        """Render datacenter facility signage, cable ladder dropouts, and alarm on North wall."""
        # 1. Large Datacenter Facility Acrylic Backlit Sign (Directly centered above server racks)
        sign_z = -hd + 0.05  # Z = -7.45
        draw_box(0.0, 2.75, sign_z, 2.20, 0.42, 0.02, (0.10, 0.11, 0.13))
        draw_box(0.0, 2.75, sign_z + 0.015, 2.10, 0.34, 0.01, (0.12, 0.45, 0.85))
        # Cyan accent glow stripe
        draw_box(0.0, 2.62, sign_z + 0.022, 1.90, 0.015, 0.004, (0.25, 0.90, 1.0))
        # Sign text simulation bar
        draw_box(0.0, 2.78, sign_z + 0.022, 1.80, 0.08, 0.004, (0.95, 0.98, 1.0))

        # 2. Overhead Cable Ladder Waterfall Drop-Outs (Drop into Racks A, B, C)
        for rx in (-0.65, 0.0, 0.65):
            # Yellow ladder rack vertical drop segment
            draw_box(rx, 2.62, -7.05, 0.28, 1.15, 0.03, (0.85, 0.70, 0.15))
            for step_y in (2.3, 2.6, 2.9):
                draw_box(rx, step_y, -7.03, 0.26, 0.02, 0.02, (0.85, 0.70, 0.15))
            # Dense cable feed entering rack top
            draw_box(rx, 2.62, -7.04, 0.18, 1.15, 0.035, (0.12, 0.35, 0.85))

        # 3. Fire Alarm Xenon Strobe / Horn Unit
        draw_box(4.0, 3.10, sign_z, 0.16, 0.18, 0.06, (0.85, 0.15, 0.15))
        draw_box(4.0, 3.14, sign_z + 0.035, 0.10, 0.06, 0.02, (0.98, 0.95, 0.80))
        draw_box(4.0, 3.05, sign_z + 0.035, 0.12, 0.04, 0.01, (0.05, 0.05, 0.06))

        # 4. Cold Aisle Floor/Wall Indicator Placard
        draw_box(-2.5, 1.80, sign_z - 0.02, 0.40, 0.15, 0.005, (0.15, 0.55, 0.95))

    def _render_south_wall_security_entrance(self, hw: float, hd: float) -> None:
        """Render double steel security entry doors, RFID access, and exit signage on South wall."""
        door_z = hd - 0.03  # Z = 7.47
        # 1. Industrial Double Security Doors
        # Steel door frame
        draw_box(0.0, 1.25, door_z, 2.45, 2.45, 0.05, (0.16, 0.18, 0.20))
        # Left & Right door leaves
        draw_box(-0.58, 1.22, door_z, 1.12, 2.35, 0.04, (0.24, 0.26, 0.30))
        draw_box(0.58, 1.22, door_z, 1.12, 2.35, 0.04, (0.24, 0.26, 0.30))
        # Center astragal seam
        draw_box(0.0, 1.22, door_z - 0.025, 0.02, 2.35, 0.01, (0.10, 0.11, 0.13))
        # Wire-glass security vision windows
        draw_box(-0.58, 1.55, door_z - 0.025, 0.22, 0.80, 0.01, (0.75, 0.85, 0.95))
        draw_box(0.58, 1.55, door_z - 0.025, 0.22, 0.80, 0.01, (0.75, 0.85, 0.95))
        # Stainless steel crash push-bars
        draw_box(-0.58, 1.05, door_z - 0.035, 0.85, 0.04, 0.03, (0.75, 0.78, 0.82))
        draw_box(0.58, 1.05, door_z - 0.035, 0.85, 0.04, 0.03, (0.75, 0.78, 0.82))

        # 2. Keycard RFID Access Badge Reader
        draw_box(1.40, 1.30, door_z - 0.01, 0.12, 0.18, 0.03, (0.10, 0.11, 0.13))
        draw_box(1.40, 1.35, door_z - 0.028, 0.02, 0.02, 0.005, (0.15, 0.95, 0.35))
        draw_box(1.40, 1.26, door_z - 0.028, 0.08, 0.08, 0.003, (0.25, 0.28, 0.32))

        # 3. Suspended Illuminated Emergency Exit Sign
        draw_box(0.0, 2.65, door_z - 0.05, 0.45, 0.20, 0.06, (0.88, 0.90, 0.92))
        draw_box(0.0, 2.65, door_z - 0.085, 0.40, 0.16, 0.01, (0.15, 0.85, 0.30))
        draw_box(0.0, 2.65, door_z - 0.092, 0.28, 0.10, 0.004, (0.95, 1.0, 0.95))

    def get_wall_boxes(self) -> List[Tuple[float, float, float, float, float, float]]:
        """Returns AABBs for boundary walls & solid infrastructure cabinets."""
        hw = self.width / 2.0
        hd = self.depth / 2.0
        h = self.height
        return [
            (-hw - 1.0, 0.0, -hd - 1.0, hw + 1.0, h, -hd),       # North Wall
            (-hw - 1.0, 0.0, hd, hw + 1.0, h, hd + 1.0),         # South Wall
            (-hw - 1.0, 0.0, -hd - 1.0, -hw, h, hd + 1.0),       # West Wall
            (hw, 0.0, -hd - 1.0, hw + 1.0, h, hd + 1.0),         # East Wall
            # West Wall 480V PDU Electrical Switchboard Cabinets solid collision
            (-hw, 0.0, -4.2, -hw + 0.45, 2.30, -1.4),
            # East Wall FM-200 Fire Suppression Master Cabinet solid collision
            (hw - 0.45, 0.0, -3.5, hw, 2.30, -2.5),
        ]

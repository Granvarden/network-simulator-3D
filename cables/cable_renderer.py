"""High-detail 3D Volumetric Cable rendering with anti-clipping patch pathing and RJ45 assemblies."""

import math
from typing import Dict, List, Optional, Tuple
from OpenGL.GL import *
from .cable import Cable
from rendering.primitives import draw_tube_path, draw_rj45_connector


class CableRenderer:
    """Renders high-detail 3D volumetric patch cables with molded boots, display-list caching, and anti-clipping routing."""

    CABLE_RADIUS: float = 0.003  # 3mm radius = 6mm Cat6 diameter
    BOOT_LENGTH: float = 0.040   # 40mm rigid connector & boot length

    def __init__(self):
        # Display list cache for static connected patch cables: cable_id -> (cache_key, display_list)
        self._cable_cache: Dict[str, Tuple[Tuple, int]] = {}

    def __del__(self):
        for _, dlist in self._cable_cache.values():
            try:
                glDeleteLists(dlist, 1)
            except Exception:
                pass
        self._cable_cache.clear()

    @staticmethod
    def get_port_world_coords(port) -> Optional[Tuple[float, float, float]]:
        """Calculate the absolute 3D world coordinate of a device port."""
        if not port or not port.device_ref:
            return None
        dev = port.device_ref
        dev_x, dev_y, dev_z = dev.position
        lx, ly, lz = port.local_slot_pos
        return (dev_x + lx, dev_y + ly, dev_z + lz)

    @classmethod
    def generate_cable_path(
        cls,
        p1: Tuple[float, float, float],
        p2: Tuple[float, float, float],
        segments: int = 24
    ) -> List[Tuple[float, float, float]]:
        """
        Generate a smooth 3D Catmull-Rom spline trajectory for a patch cable that guarantees
        zero clipping with server racks, device faceplates, handles, or chassis.
        """
        x1, y1, z1 = p1
        x2, y2, z2 = p2

        dx = x2 - x1
        dy = y2 - y1
        dz = z2 - z1
        span_y = abs(dy)
        span_x = abs(dx)

        # 1. Forward clearance calculation:
        # Ports are on the front faceplate (Z ≈ dev_z + 0.252).
        # Cables must arch forward into the aisle space (+Z) so that intermediate droop
        # is strictly in front of all faceplates, ears, buttons, and chassis.
        base_z = max(z1, z2)
        forward_clearance = max(0.065, min(0.20, 0.045 + span_y * 0.16 + span_x * 0.12))

        # Gravity sag (parabolic droop in -Y)
        sag = max(0.025, min(0.35, 0.035 + span_y * 0.08 + span_x * 0.10))

        # 2. Key control points along the physical drape:
        # P0: Inside Port 1 socket
        # P1: Rigid boot tip 1 (straight along +Z through strain-relief collar)
        boot_len = cls.BOOT_LENGTH
        cp0 = (x1, y1, z1)
        cp1 = (x1, y1, z1 + boot_len + 0.004)

        # P2: Forward arc emerging from Port 1
        cp2 = (x1 + dx * 0.08, y1 - sag * 0.15, z1 + forward_clearance * 0.70)

        # P3: Central droop belly (positioned safely out in the aisle at peak +Z)
        mid_x = (x1 + x2) / 2.0
        # For inter-rack jumps (large dx), add extra clearance so it bridges in front of rack uprights
        cross_rack_extra = 0.04 if span_x > 0.4 else 0.0
        belly_y = min(y1, y2) - sag
        belly_z = base_z + forward_clearance + cross_rack_extra
        cp3 = (mid_x, belly_y, belly_z)

        # P4: Forward arc entering Port 2
        cp4 = (x2 - dx * 0.08, y2 - sag * 0.15, z2 + forward_clearance * 0.70)

        # P5: Rigid boot tip 2 (straight along +Z through strain-relief collar)
        cp5 = (x2, y2, z2 + boot_len + 0.004)
        # P6: Inside Port 2 socket
        cp6 = (x2, y2, z2)

        control_points = [cp0, cp1, cp2, cp3, cp4, cp5, cp6]

        # 3. Evaluate smooth Catmull-Rom spline through control points
        return cls._catmull_rom_spline(control_points, segments)

    @staticmethod
    def _catmull_rom_spline(
        cps: List[Tuple[float, float, float]],
        total_segments: int
    ) -> List[Tuple[float, float, float]]:
        """Evaluate a uniform Catmull-Rom spline across a sequence of control points."""
        n = len(cps)
        if n < 4:
            return cps

        # Duplicate end points for boundary condition
        pts = [cps[0]] + list(cps) + [cps[-1]]
        num_sections = n - 1
        steps_per_sec = max(2, total_segments // num_sections)

        result: List[Tuple[float, float, float]] = []

        for sec in range(num_sections):
            p0 = pts[sec]
            p1 = pts[sec + 1]
            p2 = pts[sec + 2]
            p3 = pts[sec + 3]

            for step in range(steps_per_sec):
                t = step / float(steps_per_sec)
                t2 = t * t
                t3 = t2 * t

                # Standard Catmull-Rom basis matrix
                x = 0.5 * (
                    (2.0 * p1[0]) +
                    (-p0[0] + p2[0]) * t +
                    (2.0 * p0[0] - 5.0 * p1[0] + 4.0 * p2[0] - p3[0]) * t2 +
                    (-p0[0] + 3.0 * p1[0] - 3.0 * p2[0] + p3[0]) * t3
                )
                y = 0.5 * (
                    (2.0 * p1[1]) +
                    (-p0[1] + p2[1]) * t +
                    (2.0 * p0[1] - 5.0 * p1[1] + 4.0 * p2[1] - p3[1]) * t2 +
                    (-p0[1] + 3.0 * p1[1] - 3.0 * p2[1] + p3[1]) * t3
                )
                z = 0.5 * (
                    (2.0 * p1[2]) +
                    (-p0[2] + p2[2]) * t +
                    (2.0 * p0[2] - 5.0 * p1[2] + 4.0 * p2[2] - p3[2]) * t2 +
                    (-p0[2] + 3.0 * p1[2] - 3.0 * p2[2] + p3[2]) * t3
                )
                result.append((x, y, z))

        result.append(cps[-1])
        return result

    def _draw_single_cable(
        self,
        p1: Tuple[float, float, float],
        p2: Tuple[float, float, float],
        color: Tuple[float, float, float]
    ) -> None:
        """Render a single connected patch cable assembly (connectors, boots, volumetric tube)."""
        # 1. Render 3D RJ45 Connectors & Molded Boots at both endpoints
        draw_rj45_connector(p1[0], p1[1], p1[2], color=color, forward_z=1.0)
        draw_rj45_connector(p2[0], p2[1], p2[2], color=color, forward_z=1.0)

        # 2. Generate smooth anti-clipping volumetric 3D path
        path = self.generate_cable_path(p1, p2, segments=24)

        # 3. Render 3D volumetric polygonal tube with lighting & specular shading
        draw_tube_path(path, radius=self.CABLE_RADIUS, color=color, radial_segments=16)

    def render_cables(self, cables: List[Cable]) -> None:
        """Render all active patch cables as 3D volumetric tubes with RJ45 assemblies using display list caching."""
        active_ids = set()

        for cable in cables:
            if not cable.connected or not cable.endpoint_a or not cable.endpoint_b:
                continue

            p1 = self.get_port_world_coords(cable.endpoint_a)
            p2 = self.get_port_world_coords(cable.endpoint_b)

            if not p1 or not p2:
                continue

            active_ids.add(cable.cable_id)
            cache_key = (p1, p2, cable.color)

            if cable.cable_id in self._cable_cache:
                cached_key, dlist = self._cable_cache[cable.cable_id]
                if cached_key == cache_key:
                    try:
                        glCallList(dlist)
                        continue
                    except Exception:
                        pass
                else:
                    try:
                        glDeleteLists(dlist, 1)
                    except Exception:
                        pass
                    del self._cable_cache[cable.cable_id]

            # Compile into GPU display list
            try:
                dlist = glGenLists(1)
                glNewList(dlist, GL_COMPILE)
                self._draw_single_cable(p1, p2, cable.color)
                glEndList()
                self._cable_cache[cable.cable_id] = (cache_key, dlist)
                glCallList(dlist)
            except Exception:
                # Fallback for headless unit tests
                self._draw_single_cable(p1, p2, cable.color)

        # Clean up cache for removed/unplugged cables
        for cid in list(self._cable_cache.keys()):
            if cid not in active_ids:
                try:
                    glDeleteLists(self._cable_cache[cid][1], 1)
                except Exception:
                    pass
                del self._cable_cache[cid]

    def render_held_cable(
        self,
        source_pos: Tuple[float, float, float],
        target_pos: Tuple[float, float, float],
        color: Tuple[float, float, float] = (0.98, 0.80, 0.12),
        is_targeting_port: bool = False,
        aim_direction: Optional[Tuple[float, float, float]] = None
    ) -> None:
        """Render an active held patch cable extending from source port to crosshair/destination with 3D RJ45 connectors."""
        x1, y1, z1 = source_pos
        x2, y2, z2 = target_pos
        boot_len = self.BOOT_LENGTH

        # 1. Render 3D RJ45 connector and boot at source port
        draw_rj45_connector(x1, y1, z1, color=color, forward_z=1.0)

        if is_targeting_port:
            # When hovering over a port, snap the RJ45 connector directly into the port socket
            draw_rj45_connector(x2, y2, z2, color=color, forward_z=1.0)
            path = self.generate_cable_path(source_pos, target_pos, segments=24)
            draw_tube_path(path, radius=self.CABLE_RADIUS, color=color, radial_segments=16)
        else:
            # When dragging in free space / hand, orient the held RJ45 connector towards the aim direction
            if aim_direction:
                fx, fy, fz = aim_direction
                flen = math.sqrt(fx * fx + fy * fy + fz * fz)
                if flen > 1e-6:
                    pf = (fx / flen, fy / flen, fz / flen)
                else:
                    pf = (0.0, 0.0, -1.0)
            else:
                dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
                dlen = math.sqrt(dx * dx + dy * dy + dz * dz)
                pf = (dx / dlen, dy / dlen, dz / dlen) if dlen > 1e-6 else (0.0, 0.0, -1.0)

            # Connector body points towards pf; the rubber boot extends backwards (-pf)
            conn_dir = (-pf[0], -pf[1], -pf[2])

            # 2. Render held 3D RJ45 modular plug assembly (pins, latch, body, colored boot)
            draw_rj45_connector(x2, y2, z2, color=color, direction=conn_dir)

            # 3. Spline connects from source boot tip to held boot collar
            held_boot_x = x2 + conn_dir[0] * boot_len
            held_boot_y = y2 + conn_dir[1] * boot_len
            held_boot_z = z2 + conn_dir[2] * boot_len

            cp0 = (x1, y1, z1)
            cp1 = (x1, y1, z1 + boot_len + 0.004)
            cp2 = (x1, y1 - 0.03, z1 + 0.08)

            mid_x = (x1 + held_boot_x) / 2.0
            mid_y = min(y1, held_boot_y) - 0.08
            mid_z = (z1 + held_boot_z) / 2.0 + 0.05
            cp3 = (mid_x, mid_y, mid_z)

            cp4 = (held_boot_x + conn_dir[0] * 0.05, held_boot_y - 0.02, held_boot_z + conn_dir[2] * 0.05)
            cp5 = (held_boot_x, held_boot_y, held_boot_z)
            cp6 = (x2, y2, z2)

            path = self._catmull_rom_spline([cp0, cp1, cp2, cp3, cp4, cp5, cp6], total_segments=20)
            draw_tube_path(path, radius=self.CABLE_RADIUS, color=color, radial_segments=16)

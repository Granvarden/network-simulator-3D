"""3D Cable rendering with natural catenary sag between port endpoints."""

import math
from typing import List, Optional, Tuple
from OpenGL.GL import *
from .cable import Cable
from rendering.primitives import draw_line_3d


class CableRenderer:
    """Renders 3D cables connecting equipment in the lab."""

    @staticmethod
    def get_port_world_coords(port) -> Optional[Tuple[float, float, float]]:
        """Calculate the absolute 3D world coordinate of a device port."""
        if not port or not port.device_ref:
            return None
        dev = port.device_ref
        dev_x, dev_y, dev_z = dev.position
        lx, ly, lz = port.local_slot_pos
        return (dev_x + lx, dev_y + ly, dev_z + lz)

    def render_cables(self, cables: List[Cable]) -> None:
        """Render all active patch cables with physical droop."""
        glDisable(GL_LIGHTING)
        glLineWidth(2.5)

        for cable in cables:
            if not cable.connected or not cable.endpoint_a or not cable.endpoint_b:
                continue

            p1 = self.get_port_world_coords(cable.endpoint_a)
            p2 = self.get_port_world_coords(cable.endpoint_b)

            if not p1 or not p2:
                continue

            x1, y1, z1 = p1
            x2, y2, z2 = p2

            # Compute catenary sag (sag down based on distance)
            dist_sq = (x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2
            dist = math.sqrt(dist_sq)
            sag_amount = min(0.4, max(0.04, dist * 0.12))

            segments = 12
            glColor3f(*cable.color)
            glBegin(GL_LINE_STRIP)

            for i in range(segments + 1):
                t = i / float(segments)
                # Linear interpolation
                px = x1 + (x2 - x1) * t
                pz = z1 + (z2 - z1) * t
                # Parabolic sag
                sag = 4.0 * sag_amount * t * (1.0 - t)
                py = y1 + (y2 - y1) * t - sag

                glVertex3f(px, py, pz)

            glEnd()

        glEnable(GL_LIGHTING)

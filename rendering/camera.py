"""First-person 3D camera with pitch/yaw orientation and ray generation."""

import math
from typing import Tuple
from OpenGL.GL import *
from OpenGL.GLU import *


class Camera:
    """Calculates perspective view matrix and camera directional vectors."""

    def __init__(self, x: float = 0.0, y: float = 1.7, z: float = 4.0):
        self.x: float = x
        self.y: float = y
        self.z: float = z
        self.yaw: float = -90.0   # Facing negative Z (towards racks)
        self.pitch: float = 0.0

    def rotate(self, delta_yaw: float, delta_pitch: float, max_pitch: float = 89.0) -> None:
        """Apply mouse delta to camera rotation."""
        self.yaw = (self.yaw + delta_yaw) % 360.0
        self.pitch = max(-max_pitch, min(max_pitch, self.pitch + delta_pitch))

    def get_forward_vector(self) -> Tuple[float, float, float]:
        """Normalized 3D forward look direction."""
        rad_yaw = math.radians(self.yaw)
        rad_pitch = math.radians(self.pitch)
        fx = math.cos(rad_pitch) * math.cos(rad_yaw)
        fy = math.sin(rad_pitch)
        fz = math.cos(rad_pitch) * math.sin(rad_yaw)
        length = math.sqrt(fx * fx + fy * fy + fz * fz)
        if length > 0.0001:
            return (fx / length, fy / length, fz / length)
        return (0.0, 0.0, -1.0)

    def get_horizontal_forward(self) -> Tuple[float, float]:
        """Horizontal (X, Z) normalized vector for ground movement."""
        rad_yaw = math.radians(self.yaw)
        fx = math.cos(rad_yaw)
        fz = math.sin(rad_yaw)
        length = math.sqrt(fx * fx + fz * fz)
        if length > 0.0001:
            return (fx / length, fz / length)
        return (0.0, -1.0)

    def get_horizontal_right(self) -> Tuple[float, float]:
        """Horizontal (X, Z) normalized strafe right vector."""
        hx, hz = self.get_horizontal_forward()
        # Perpendicular vector (rotate 90 degrees clockwise)
        return (-hz, hx)

    def apply_view(self) -> None:
        """Sets the OpenGL ModelView matrix using gluLookAt."""
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        fx, fy, fz = self.get_forward_vector()
        target_x = self.x + fx
        target_y = self.y + fy
        target_z = self.z + fz
        gluLookAt(
            self.x, self.y, self.z,
            target_x, target_y, target_z,
            0.0, 1.0, 0.0
        )

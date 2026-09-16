"""3D OpenGL geometric rendering primitives."""

from typing import Tuple
from OpenGL.GL import *
from OpenGL.GLU import *
import math


def draw_box(
    cx: float, cy: float, cz: float,
    sx: float, sy: float, sz: float,
    color: Tuple[float, float, float]
) -> None:
    """Draw a solid 3D box centered at (cx, cy, cz) with dimensions (sx, sy, sz)."""
    hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0

    glColor3f(*color)
    glBegin(GL_QUADS)

    # Front Face (Z+)
    glNormal3f(0.0, 0.0, 1.0)
    glVertex3f(cx - hx, cy - hy, cz + hz)
    glVertex3f(cx + hx, cy - hy, cz + hz)
    glVertex3f(cx + hx, cy + hy, cz + hz)
    glVertex3f(cx - hx, cy + hy, cz + hz)

    # Back Face (Z-)
    glNormal3f(0.0, 0.0, -1.0)
    glVertex3f(cx - hx, cy - hy, cz - hz)
    glVertex3f(cx - hx, cy + hy, cz - hz)
    glVertex3f(cx + hx, cy + hy, cz - hz)
    glVertex3f(cx + hx, cy - hy, cz - hz)

    # Top Face (Y+)
    glNormal3f(0.0, 1.0, 0.0)
    glVertex3f(cx - hx, cy + hy, cz - hz)
    glVertex3f(cx - hx, cy + hy, cz + hz)
    glVertex3f(cx + hx, cy + hy, cz + hz)
    glVertex3f(cx + hx, cy + hy, cz - hz)

    # Bottom Face (Y-)
    glNormal3f(0.0, -1.0, 0.0)
    glVertex3f(cx - hx, cy - hy, cz - hz)
    glVertex3f(cx + hx, cy - hy, cz - hz)
    glVertex3f(cx + hx, cy - hy, cz + hz)
    glVertex3f(cx - hx, cy - hy, cz + hz)

    # Right Face (X+)
    glNormal3f(1.0, 0.0, 0.0)
    glVertex3f(cx + hx, cy - hy, cz - hz)
    glVertex3f(cx + hx, cy + hy, cz - hz)
    glVertex3f(cx + hx, cy + hy, cz + hz)
    glVertex3f(cx + hx, cy - hy, cz + hz)

    # Left Face (X-)
    glNormal3f(-1.0, 0.0, 0.0)
    glVertex3f(cx - hx, cy - hy, cz - hz)
    glVertex3f(cx - hx, cy - hy, cz + hz)
    glVertex3f(cx - hx, cy + hy, cz + hz)
    glVertex3f(cx - hx, cy + hy, cz - hz)

    glEnd()


def draw_wire_box(
    cx: float, cy: float, cz: float,
    sx: float, sy: float, sz: float,
    color: Tuple[float, float, float],
    line_width: float = 1.5
) -> None:
    """Draw a wireframe bounding box."""
    hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0

    glDisable(GL_LIGHTING)
    glLineWidth(line_width)
    glColor3f(*color)

    glBegin(GL_LINES)
    # Bottom 4 lines
    glVertex3f(cx - hx, cy - hy, cz - hz); glVertex3f(cx + hx, cy - hy, cz - hz)
    glVertex3f(cx + hx, cy - hy, cz - hz); glVertex3f(cx + hx, cy - hy, cz + hz)
    glVertex3f(cx + hx, cy - hy, cz + hz); glVertex3f(cx - hx, cy - hy, cz + hz)
    glVertex3f(cx - hx, cy - hy, cz + hz); glVertex3f(cx - hx, cy - hy, cz - hz)

    # Top 4 lines
    glVertex3f(cx - hx, cy + hy, cz - hz); glVertex3f(cx + hx, cy + hy, cz - hz)
    glVertex3f(cx + hx, cy + hy, cz - hz); glVertex3f(cx + hx, cy + hy, cz + hz)
    glVertex3f(cx + hx, cy + hy, cz + hz); glVertex3f(cx - hx, cy + hy, cz + hz)
    glVertex3f(cx - hx, cy + hy, cz + hz); glVertex3f(cx - hx, cy + hy, cz - hz)

    # Vertical 4 lines
    glVertex3f(cx - hx, cy - hy, cz - hz); glVertex3f(cx - hx, cy + hy, cz - hz)
    glVertex3f(cx + hx, cy - hy, cz - hz); glVertex3f(cx + hx, cy + hy, cz - hz)
    glVertex3f(cx + hx, cy - hy, cz + hz); glVertex3f(cx + hx, cy + hy, cz + hz)
    glVertex3f(cx - hx, cy - hy, cz + hz); glVertex3f(cx - hx, cy + hy, cz + hz)
    glEnd()

    glEnable(GL_LIGHTING)


def draw_line_3d(
    x1: float, y1: float, z1: float,
    x2: float, y2: float, z2: float,
    color: Tuple[float, float, float],
    line_width: float = 2.0
) -> None:
    """Draw a 3D line segment."""
    glDisable(GL_LIGHTING)
    glLineWidth(line_width)
    glColor3f(*color)
    glBegin(GL_LINES)
    glVertex3f(x1, y1, z1)
    glVertex3f(x2, y2, z2)
    glEnd()
    glEnable(GL_LIGHTING)


def draw_grid_plane(
    width: float, depth: float, tile_size: float, y_pos: float,
    color_plane: Tuple[float, float, float],
    color_grid: Tuple[float, float, float]
) -> None:
    """Draw a raised floor grid plane with tiles."""
    hw = width / 2.0
    hd = depth / 2.0

    # Base solid floor
    glColor3f(*color_plane)
    glBegin(GL_QUADS)
    glNormal3f(0.0, 1.0, 0.0)
    glVertex3f(-hw, y_pos, -hd)
    glVertex3f(-hw, y_pos, hd)
    glVertex3f(hw, y_pos, hd)
    glVertex3f(hw, y_pos, -hd)
    glEnd()

    # Grid overlay lines
    glDisable(GL_LIGHTING)
    glLineWidth(1.0)
    glColor3f(*color_grid)
    glBegin(GL_LINES)

    x = -hw
    while x <= hw + 0.001:
        glVertex3f(x, y_pos + 0.002, -hd)
        glVertex3f(x, y_pos + 0.002, hd)
        x += tile_size

    z = -hd
    while z <= hd + 0.001:
        glVertex3f(-hw, y_pos + 0.002, z)
        glVertex3f(hw, y_pos + 0.002, z)
        z += tile_size

    glEnd()
    glEnable(GL_LIGHTING)


def draw_cylinder(
    bx: float, by: float, bz: float,
    radius: float, height: float,
    color: Tuple[float, float, float],
    segments: int = 12
) -> None:
    """Draw a vertical cylinder."""
    glColor3f(*color)
    glBegin(GL_QUAD_STRIP)
    for i in range(segments + 1):
        angle = 2.0 * math.pi * i / segments
        dx = math.cos(angle) * radius
        dz = math.sin(angle) * radius
        glNormal3f(math.cos(angle), 0.0, math.sin(angle))
        glVertex3f(bx + dx, by, bz + dz)
        glVertex3f(bx + dx, by + height, bz + dz)
    glEnd()

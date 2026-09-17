"""3D OpenGL geometric rendering primitives."""

from typing import Optional, Tuple
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


def draw_tube_path(
    points: list,
    radius: float,
    color: Tuple[float, float, float],
    radial_segments: int = 16
) -> None:
    """Render a continuous 3D volumetric polygonal tube with lighting and smooth surface normals along a 3D path.

    Uses Wang et al. (2008) Rotation-Minimizing Frames (RMF / Double Reflection) to mathematically
    guarantee zero torsional twist along curves of arbitrary 3D curvature.
    """
    n_pts = len(points)
    if n_pts < 2:
        return

    # 1. Compute unit tangent vectors along the path
    tangents = []
    for i in range(n_pts):
        if i == 0:
            tx = points[1][0] - points[0][0]
            ty = points[1][1] - points[0][1]
            tz = points[1][2] - points[0][2]
        elif i == n_pts - 1:
            tx = points[i][0] - points[i - 1][0]
            ty = points[i][1] - points[i - 1][1]
            tz = points[i][2] - points[i - 1][2]
        else:
            tx = points[i + 1][0] - points[i - 1][0]
            ty = points[i + 1][1] - points[i - 1][1]
            tz = points[i + 1][2] - points[i - 1][2]

        t_len = math.sqrt(tx * tx + ty * ty + tz * tz)
        if t_len > 1e-6:
            tangents.append((tx / t_len, ty / t_len, tz / t_len))
        elif tangents:
            tangents.append(tangents[-1])
        else:
            tangents.append((0.0, 0.0, 1.0))

    # 2. Initial orthonormal frame (T0, N0, B0)
    T0 = tangents[0]
    up = (0.0, 1.0, 0.0) if abs(T0[1]) < 0.9 else (1.0, 0.0, 0.0)
    dot_up_t = up[0] * T0[0] + up[1] * T0[1] + up[2] * T0[2]
    nx0 = up[0] - dot_up_t * T0[0]
    ny0 = up[1] - dot_up_t * T0[1]
    nz0 = up[2] - dot_up_t * T0[2]
    n0_len = math.sqrt(nx0 * nx0 + ny0 * ny0 + nz0 * nz0)
    if n0_len > 1e-6:
        N0 = (nx0 / n0_len, ny0 / n0_len, nz0 / n0_len)
    else:
        N0 = (1.0, 0.0, 0.0)
    B0 = (
        T0[1] * N0[2] - T0[2] * N0[1],
        T0[2] * N0[0] - T0[0] * N0[2],
        T0[0] * N0[1] - T0[1] * N0[0]
    )

    frames = [(T0, N0, B0)]

    # 3. Parallel transport frames using Double Reflection (Wang et al., 2008)
    for i in range(n_pts - 1):
        xi, xnext = points[i], points[i + 1]
        Ti, Ni, Bi = frames[-1]
        Tnext = tangents[i + 1]

        v1 = (xnext[0] - xi[0], xnext[1] - xi[1], xnext[2] - xi[2])
        c1 = v1[0] * v1[0] + v1[1] * v1[1] + v1[2] * v1[2]
        if c1 < 1e-12:
            Ni_next = Ni
        else:
            k1 = 2.0 / c1
            v1_dot_Ni = v1[0] * Ni[0] + v1[1] * Ni[1] + v1[2] * Ni[2]
            v1_dot_Ti = v1[0] * Ti[0] + v1[1] * Ti[1] + v1[2] * Ti[2]
            Ni_L = (
                Ni[0] - k1 * v1_dot_Ni * v1[0],
                Ni[1] - k1 * v1_dot_Ni * v1[1],
                Ni[2] - k1 * v1_dot_Ni * v1[2]
            )
            Ti_L = (
                Ti[0] - k1 * v1_dot_Ti * v1[0],
                Ti[1] - k1 * v1_dot_Ti * v1[1],
                Ti[2] - k1 * v1_dot_Ti * v1[2]
            )
            v2 = (Tnext[0] - Ti_L[0], Tnext[1] - Ti_L[1], Tnext[2] - Ti_L[2])
            c2 = v2[0] * v2[0] + v2[1] * v2[1] + v2[2] * v2[2]
            if c2 < 1e-12:
                Ni_next = Ni_L
            else:
                k2 = 2.0 / c2
                v2_dot_Ni_L = v2[0] * Ni_L[0] + v2[1] * Ni_L[1] + v2[2] * Ni_L[2]
                Ni_next = (
                    Ni_L[0] - k2 * v2_dot_Ni_L * v2[0],
                    Ni_L[1] - k2 * v2_dot_Ni_L * v2[1],
                    Ni_L[2] - k2 * v2_dot_Ni_L * v2[2]
                )

        # Orthonormalize against Tnext
        dot_tn = Ni_next[0] * Tnext[0] + Ni_next[1] * Tnext[1] + Ni_next[2] * Tnext[2]
        nx = Ni_next[0] - dot_tn * Tnext[0]
        ny = Ni_next[1] - dot_tn * Tnext[1]
        nz = Ni_next[2] - dot_tn * Tnext[2]
        n_len = math.sqrt(nx * nx + ny * ny + nz * nz)
        if n_len > 1e-6:
            Ni_next = (nx / n_len, ny / n_len, nz / n_len)
        else:
            Ni_next = Ni

        Bi_next = (
            Tnext[1] * Ni_next[2] - Tnext[2] * Ni_next[1],
            Tnext[2] * Ni_next[0] - Tnext[0] * Ni_next[2],
            Tnext[0] * Ni_next[1] - Tnext[1] * Ni_next[0]
        )
        frames.append((Tnext, Ni_next, Bi_next))

    # 4. Generate vertices for cross-section rings
    rings = []
    cos_table = [math.cos(2.0 * math.pi * j / radial_segments) for j in range(radial_segments + 1)]
    sin_table = [math.sin(2.0 * math.pi * j / radial_segments) for j in range(radial_segments + 1)]

    for i in range(n_pts):
        p = points[i]
        _, N, B = frames[i]
        ring_verts = []
        for j in range(radial_segments + 1):
            cos_a = cos_table[j]
            sin_a = sin_table[j]

            norm_x = cos_a * N[0] + sin_a * B[0]
            norm_y = cos_a * N[1] + sin_a * B[1]
            norm_z = cos_a * N[2] + sin_a * B[2]

            vx = p[0] + radius * norm_x
            vy = p[1] + radius * norm_y
            vz = p[2] + radius * norm_z

            ring_verts.append(((norm_x, norm_y, norm_z), (vx, vy, vz)))
        rings.append(ring_verts)

    glEnable(GL_LIGHTING)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glColor3f(*color)

    # Realistic plastic PVC cable jacket specular sheen
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.35, 0.35, 0.35, 1.0])
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 24.0)

    # Disable face culling temporarily for continuous 3D tube to guarantee seamless solid surface
    glDisable(GL_CULL_FACE)

    # 5. Render connected smooth quad strips with outward-facing normals and CCW winding
    for i in range(len(rings) - 1):
        r0 = rings[i]
        r1 = rings[i + 1]
        glBegin(GL_QUAD_STRIP)
        for j in range(radial_segments + 1):
            n1_v, v1_v = r1[j]
            n0, v0 = r0[j]
            glNormal3f(*n1_v)
            glVertex3f(*v1_v)
            glNormal3f(*n0)
            glVertex3f(*v0)
        glEnd()

    # 6. Watertight disc end caps at tube start and end
    # Start cap
    t0 = frames[0][0]
    glBegin(GL_TRIANGLE_FAN)
    glNormal3f(-t0[0], -t0[1], -t0[2])
    glVertex3f(*points[0])
    for j in range(radial_segments, -1, -1):
        glVertex3f(*rings[0][j][1])
    glEnd()

    # End cap
    tn = frames[-1][0]
    glBegin(GL_TRIANGLE_FAN)
    glNormal3f(tn[0], tn[1], tn[2])
    glVertex3f(*points[-1])
    for j in range(radial_segments + 1):
        glVertex3f(*rings[-1][j][1])
    glEnd()

    glEnable(GL_CULL_FACE)

    # Restore default material specular
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.4, 0.4, 0.4, 1.0])
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 32.0)


def draw_rj45_connector(
    px: float, py: float, pz: float,
    color: Tuple[float, float, float],
    direction: Optional[Tuple[float, float, float]] = None,
    forward_z: float = 1.0,
    up: Optional[Tuple[float, float, float]] = None
) -> None:
    """Render a high-detail 3D modular RJ45 plug assembly with gold pins, latch, and strain-relief boot.

    Parameters:
        px, py, pz: 3D position of the connector tip (plug nose / socket interface).
        color: RGB tuple for the cable and matching strain-relief rubber boot.
        direction: 3D vector pointing FROM plug nose TOWARDS the cable boot.
                   If None, defaults to the world Z-axis based on forward_z.
        forward_z: Direction along Z-axis (+1.0 or -1.0) when direction is None.
        up: Orientation vector for connector top/latch (default: world Up).
    """
    if direction is None:
        direction = (0.0, 0.0, 1.0 if forward_z >= 0 else -1.0)

    dx, dy, dz = direction
    l = math.sqrt(dx * dx + dy * dy + dz * dz)
    if l > 1e-6:
        Z = (dx / l, dy / l, dz / l)
    else:
        Z = (0.0, 0.0, 1.0)

    if up is None:
        up_v = (0.0, 1.0, 0.0) if abs(Z[1]) < 0.9 else (0.0, 0.0, 1.0)
    else:
        up_v = up

    # X = normalize(up x Z) (width axis)
    xx = up_v[1] * Z[2] - up_v[2] * Z[1]
    xy = up_v[2] * Z[0] - up_v[0] * Z[2]
    xz = up_v[0] * Z[1] - up_v[1] * Z[0]
    xl = math.sqrt(xx * xx + xy * xy + xz * xz)
    if xl > 1e-6:
        X = (xx / xl, xy / xl, xz / xl)
    else:
        X = (1.0, 0.0, 0.0)

    # Y = Z x X (height axis, +Y points to retention clip)
    Y = (
        Z[1] * X[2] - Z[2] * X[1],
        Z[2] * X[0] - Z[0] * X[2],
        Z[0] * X[1] - Z[1] * X[0]
    )

    mat = [
        X[0], X[1], X[2], 0.0,
        Y[0], Y[1], Y[2], 0.0,
        Z[0], Z[1], Z[2], 0.0,
        px,   py,   pz,   1.0
    ]

    glPushMatrix()
    glMultMatrixf(mat)

    # 1. Clear / Smoked Polycarbonate RJ45 Modular Plug Body (Length 14mm)
    draw_box(0.0, 0.0, 0.008, 0.0116, 0.0084, 0.014, (0.78, 0.83, 0.90))

    # Front chamfered nose
    draw_box(0.0, -0.0008, 0.0016, 0.0096, 0.0065, 0.003, (0.72, 0.77, 0.85))

    # 2. Gold Contact Pins (8-pin modular block on bottom/nose of plug)
    draw_box(0.0, -0.0044, 0.0045, 0.0088, 0.0016, 0.007, (0.95, 0.78, 0.18))
    # Pin teeth divider accent
    draw_box(0.0, -0.0046, 0.0045, 0.0018, 0.0018, 0.007, (0.80, 0.62, 0.12))

    # 3. Plastic Retention Locking Latch Tab (Spring latch on top of plug)
    draw_box(0.0, 0.0048, 0.0095, 0.0042, 0.0028, 0.010, (0.70, 0.75, 0.82))

    # 4. Molded Snagless Rubber Strain-Relief Boot (Matching cable color seamlessly)
    boot_color = color
    boot_highlight = (min(1.0, color[0] * 1.12), min(1.0, color[1] * 1.12), min(1.0, color[2] * 1.12))
    boot_ridge = (color[0] * 0.82, color[1] * 0.82, color[2] * 0.82)

    # Main boot body (18mm length)
    draw_box(0.0, 0.0, 0.023, 0.0125, 0.0100, 0.018, boot_color)

    # Snagless hood / latch protector ramp (covers the latch clip)
    draw_box(0.0, 0.0055, 0.018, 0.0055, 0.0032, 0.009, boot_highlight)

    # Anti-slip boot grip ridge
    draw_box(0.0, 0.0052, 0.026, 0.0110, 0.0015, 0.003, boot_ridge)

    # 5. Round Molded Strain-Relief Collar (Tapering snugly onto the 6mm round cable)
    glColor3f(*boot_color)
    collar_segs = 12
    glBegin(GL_QUAD_STRIP)
    for s in range(collar_segs + 1):
        ang = 2.0 * math.pi * s / collar_segs
        ca = math.cos(ang)
        sa = math.sin(ang)
        glNormal3f(ca, sa, 0.0)
        glVertex3f(0.0044 * ca, 0.0044 * sa, 0.031)
        glVertex3f(0.0034 * ca, 0.0034 * sa, 0.040)
    glEnd()

    # Strain-relief grip ring
    glColor3f(*boot_ridge)
    glBegin(GL_QUAD_STRIP)
    for s in range(collar_segs + 1):
        ang = 2.0 * math.pi * s / collar_segs
        ca = math.cos(ang)
        sa = math.sin(ang)
        glNormal3f(ca, sa, 0.0)
        glVertex3f(0.0040 * ca, 0.0040 * sa, 0.035)
        glVertex3f(0.0040 * ca, 0.0040 * sa, 0.037)
    glEnd()

    glPopMatrix()


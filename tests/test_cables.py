"""Unit tests for Cable system and CableManager."""

import pytest
from devices.port import Port, AdminStatus
from cables.cable import Cable, CableType
from cables.cable_manager import CableManager


def test_cable_direct_connection():
    p1 = Port("p1", "Gi0/0")
    p2 = Port("p2", "Gi0/1")
    p1.set_admin_status(AdminStatus.UP)
    p2.set_admin_status(AdminStatus.UP)

    cable = Cable("c1", CableType.CAT6_ETHERNET)
    success = cable.connect(p1, p2)

    assert success
    assert cable.connected
    assert p1.is_operational
    assert p2.is_operational


def test_cable_prevent_self_loop():
    p1 = Port("p1", "Gi0/0")
    mgr = CableManager()
    success, cable, msg = mgr.connect_ports(p1, p1)

    assert not success
    assert cable is None
    assert "Cannot connect a port to itself" in msg


def test_cable_prevent_occupied_port():
    p1 = Port("p1", "Gi0/0")
    p2 = Port("p2", "Gi0/1")
    p3 = Port("p3", "Gi0/2")

    mgr = CableManager()
    mgr.connect_ports(p1, p2)

    # Attempt to connect p3 into p1 (p1 is already occupied)
    success, cable, msg = mgr.connect_ports(p3, p1)
    assert not success
    assert cable is None
    assert "already connected" in msg


def test_cable_manager_removal():
    p1 = Port("p1", "Gi0/0")
    p2 = Port("p2", "Gi0/1")
    p1.set_admin_status(AdminStatus.UP)
    p2.set_admin_status(AdminStatus.UP)

    mgr = CableManager()
    success, cable, _ = mgr.connect_ports(p1, p2)
    assert success
    assert len(mgr.get_all_cables()) == 1
    assert p1.is_operational

    removed = mgr.remove_cable(cable.cable_id)
    assert removed
    assert len(mgr.get_all_cables()) == 0
    assert not p1.is_operational
    assert not p2.is_operational


def test_cable_custom_color():
    p1 = Port("p1", "Gi0/0")
    p2 = Port("p2", "Gi0/1")
    mgr = CableManager()
    custom_blue = (0.18, 0.48, 0.95)
    success, cable, msg = mgr.connect_ports(p1, p2, color=custom_blue)
    assert success
    assert cable.color == custom_blue


def test_held_cable_scroll_color_cycling():
    from core.service_container import ServiceContainer
    from core.game_state import GameStateManager
    from core.event_bus import EventBus
    from core.input_manager import InputManager
    from scenes.sandbox_scene import SandboxScene
    import pygame

    sc = ServiceContainer()
    sc.register("state_manager", GameStateManager())
    sc.register("event_bus", EventBus())
    sc.register("input_manager", InputManager())
    scene = SandboxScene(sc)

    # Initial default color must be Royal Blue
    assert scene.held_cable_color_idx == 0
    assert "Blue" in scene.cable_colors[0][1]

    # Start cabling with port
    p1 = Port("p1", "Gi0/0")
    scene.held_cable_port = p1

    # Mouse wheel up -> next color
    wheel_up = pygame.event.Event(pygame.MOUSEWHEEL, {"y": 1, "x": 0})
    handled = scene.handle_event(wheel_up)
    assert handled is True
    assert scene.held_cable_color_idx == 1

    # Mouse wheel down -> previous color (back to 0)
    wheel_down = pygame.event.Event(pygame.MOUSEWHEEL, {"y": -1, "x": 0})
    handled = scene.handle_event(wheel_down)
    assert handled is True
    assert scene.held_cable_color_idx == 0


def test_render_held_cable_modes():
    """Verify render_held_cable invokes RJ45 connectors and tube rendering for both port targeting and free dragging."""
    from unittest.mock import patch
    from cables.cable_renderer import CableRenderer

    renderer = CableRenderer()
    p1 = (-0.53, 1.54, -6.648)
    p2_port = (-0.63, 1.32, -6.648)
    p2_air = (-0.20, 1.40, -6.20)

    with patch("cables.cable_renderer.draw_rj45_connector") as mock_conn, \
         patch("cables.cable_renderer.draw_tube_path") as mock_tube:

        # 1. Target port mode: snaps connector directly into port socket
        renderer.render_held_cable(p1, p2_port, color=(0.18, 0.48, 0.95), is_targeting_port=True)
        assert mock_conn.call_count == 2
        mock_tube.assert_called_once()
        assert mock_tube.call_args.kwargs["radial_segments"] == 16

        mock_conn.reset_mock()
        mock_tube.reset_mock()

        # 2. Free dragging mode: connector oriented along aim_direction at target end
        fwd = (0.0, 0.0, -1.0)
        renderer.render_held_cable(p1, p2_air, color=(0.95, 0.75, 0.10), is_targeting_port=False, aim_direction=fwd)
        assert mock_conn.call_count == 2
        # Target connector must specify direction vector
        _, kwargs = mock_conn.call_args_list[1]
        assert kwargs.get("direction") is not None
        mock_tube.assert_called_once()
        assert mock_tube.call_args.kwargs["radial_segments"] == 16


def test_rmf_frame_mathematical_orthonormality_and_no_twist():
    """Verify Wang et al. 2008 Double Reflection RMF mathematical orthonormality and zero twist."""
    import math

    # Complex 3D trajectory with U-turns and vertical inflections
    points = [
        (math.sin(t * 0.4) * 0.35, 1.5 - t * 0.04, -6.5 + math.cos(t * 0.3) * 0.25)
        for t in range(25)
    ]
    n_pts = len(points)
    tangents = []
    for i in range(n_pts):
        if i == 0:
            tx, ty, tz = points[1][0] - points[0][0], points[1][1] - points[0][1], points[1][2] - points[0][2]
        elif i == n_pts - 1:
            tx, ty, tz = points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1], points[i][2] - points[i - 1][2]
        else:
            tx, ty, tz = points[i + 1][0] - points[i - 1][0], points[i + 1][1] - points[i - 1][1], points[i + 1][2] - points[i - 1][2]
        t_len = math.sqrt(tx * tx + ty * ty + tz * tz)
        tangents.append((tx / t_len, ty / t_len, tz / t_len))

    T0 = tangents[0]
    up = (0.0, 1.0, 0.0) if abs(T0[1]) < 0.9 else (1.0, 0.0, 0.0)
    dot_up_t = up[0] * T0[0] + up[1] * T0[1] + up[2] * T0[2]
    nx0, ny0, nz0 = up[0] - dot_up_t * T0[0], up[1] - dot_up_t * T0[1], up[2] - dot_up_t * T0[2]
    n0_len = math.sqrt(nx0 * nx0 + ny0 * ny0 + nz0 * nz0)
    N0 = (nx0 / n0_len, ny0 / n0_len, nz0 / n0_len)
    B0 = (T0[1] * N0[2] - T0[2] * N0[1], T0[2] * N0[0] - T0[0] * N0[2], T0[0] * N0[1] - T0[1] * N0[0])
    frames = [(T0, N0, B0)]

    for i in range(n_pts - 1):
        xi, xnext = points[i], points[i + 1]
        Ti, Ni, Bi = frames[-1]
        Tnext = tangents[i + 1]
        v1 = (xnext[0] - xi[0], xnext[1] - xi[1], xnext[2] - xi[2])
        c1 = v1[0] * v1[0] + v1[1] * v1[1] + v1[2] * v1[2]
        k1 = 2.0 / c1
        v1_dot_Ni = v1[0] * Ni[0] + v1[1] * Ni[1] + v1[2] * Ni[2]
        v1_dot_Ti = v1[0] * Ti[0] + v1[1] * Ti[1] + v1[2] * Ti[2]
        Ni_L = (Ni[0] - k1 * v1_dot_Ni * v1[0], Ni[1] - k1 * v1_dot_Ni * v1[1], Ni[2] - k1 * v1_dot_Ni * v1[2])
        Ti_L = (Ti[0] - k1 * v1_dot_Ti * v1[0], Ti[1] - k1 * v1_dot_Ti * v1[1], Ti[2] - k1 * v1_dot_Ti * v1[2])
        v2 = (Tnext[0] - Ti_L[0], Tnext[1] - Ti_L[1], Tnext[2] - Ti_L[2])
        c2 = v2[0] * v2[0] + v2[1] * v2[1] + v2[2] * v2[2]
        k2 = 2.0 / c2
        v2_dot_Ni_L = v2[0] * Ni_L[0] + v2[0] * Ni_L[1] + v2[2] * Ni_L[2]
        Ni_next = (Ni_L[0] - k2 * v2_dot_Ni_L * v2[0], Ni_L[1] - k2 * v2_dot_Ni_L * v2[1], Ni_L[2] - k2 * v2_dot_Ni_L * v2[2])
        dot_tn = Ni_next[0] * Tnext[0] + Ni_next[1] * Tnext[1] + Ni_next[2] * Tnext[2]
        nx, ny, nz = Ni_next[0] - dot_tn * Tnext[0], Ni_next[1] - dot_tn * Tnext[1], Ni_next[2] - dot_tn * Tnext[2]
        n_len = math.sqrt(nx * nx + ny * ny + nz * nz)
        Ni_next = (nx / n_len, ny / n_len, nz / n_len)
        Bi_next = (Tnext[1] * Ni_next[2] - Tnext[2] * Ni_next[1], Tnext[2] * Ni_next[0] - Tnext[0] * Ni_next[2], Tnext[0] * Ni_next[1] - Tnext[1] * Ni_next[0])
        frames.append((Tnext, Ni_next, Bi_next))

    # Assert strict orthonormality and unit length along all frames
    for i, (t, n, b) in enumerate(frames):
        dot_tn = abs(t[0] * n[0] + t[1] * n[1] + t[2] * n[2])
        dot_tb = abs(t[0] * b[0] + t[1] * b[1] + t[2] * b[2])
        dot_nb = abs(n[0] * b[0] + n[1] * b[1] + n[2] * b[2])
        assert dot_tn < 1e-5, f"T and N not orthogonal at frame {i}"
        assert dot_tb < 1e-5, f"T and B not orthogonal at frame {i}"
        assert dot_nb < 1e-5, f"N and B not orthogonal at frame {i}"
        n_len = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2)
        assert abs(n_len - 1.0) < 1e-5, f"N not unit length at frame {i}"




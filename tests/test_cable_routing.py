"""Unit tests verifying anti-clipping cable trajectory and 3D volumetric patch routing."""

import pytest
from cables.cable_renderer import CableRenderer
from world.rack import Rack
from devices.device_factory import DeviceFactory


def test_cable_path_anti_clipping_front_clearance():
    """Verify that cable trajectory arches strictly forward in front of equipment faceplates."""
    # Port on PC at U33 (y ≈ 1.54, z ≈ -6.648)
    # Port on Router at U28 (y ≈ 1.32, z ≈ -6.648)
    p1 = (-0.53, 1.54, -6.648)
    p2 = (-0.63, 1.32, -6.648)

    faceplate_z = max(p1[2], p2[2])
    path = CableRenderer.generate_cable_path(p1, p2, segments=32)

    assert len(path) >= 20

    # Start and end must touch sockets
    assert abs(path[0][0] - p1[0]) < 1e-4
    assert abs(path[0][1] - p1[1]) < 1e-4
    assert abs(path[-1][0] - p2[0]) < 1e-4
    assert abs(path[-1][1] - p2[1]) < 1e-4

    # All intermediate points (beyond socket connection) must have Z >= faceplate_z
    # and arch forward (+Z) safely into the aisle
    for idx, (x, y, z) in enumerate(path[1:-1]):
        assert z >= faceplate_z, f"Point {idx} clipped behind faceplate: z={z} < {faceplate_z}"

    # Peak clearance in the central droop must provide at least 5cm of clearance in front of chassis
    peak_z = max(pt[2] for pt in path)
    assert peak_z >= faceplate_z + 0.05, f"Peak Z clearance {peak_z - faceplate_z}m is insufficient"


def test_inter_rack_cable_forward_clearance():
    """Verify that cables spanning across different racks have sufficient aisle clearance to bridge past rack posts."""
    # Port in Rack A (x = -0.65) to Port in Rack B (x = 0.0)
    p1 = (-0.63, 1.32, -6.648)
    p2 = (0.02, 1.32, -6.648)

    base_z = -6.648
    path = CableRenderer.generate_cable_path(p1, p2, segments=32)

    # In the middle (where the vertical rack post is located between racks at x ≈ -0.35)
    # Z coordinate must be well in front of rack uprights (which sit at z <= -6.61)
    mid_points = [pt for pt in path if -0.45 < pt[0] < -0.20]
    assert len(mid_points) > 0

    for pt in mid_points:
        assert pt[2] >= base_z + 0.06, f"Cross-rack point at x={pt[0]} has z={pt[2]}, risking post collision"


def test_no_device_bounding_box_penetration():
    """Verify that patch cables never penetrate the solid bounding volume of installed devices."""
    rack = Rack("Rack A", position=(-0.65, 0.0, -7.05))
    router = DeviceFactory.create_device("Router", "R1")
    switch = DeviceFactory.create_device("Switch", "SW1")
    pc = DeviceFactory.create_device("PC", "PC1")

    # Install R1 at U28 (takes U28-U29: y ≈ 1.30 to 1.39, z <= -6.648)
    # Install SW1 at U31 (takes U31: y ≈ 1.43 to 1.48, z <= -6.648)
    # Install PC1 at U33 (takes U33-U34: y ≈ 1.52 to 1.61, z <= -6.648)
    rack.install_device(router, 28)
    rack.install_device(switch, 31)
    rack.install_device(pc, 33)

    # Path from PC1 (U33) down to Router (U28) spanning over Switch (U31)
    p_pc = CableRenderer.get_port_world_coords(pc.get_port("eth0"))
    p_router = CableRenderer.get_port_world_coords(router.get_port("Gi0/0"))
    assert p_pc is not None and p_router is not None

    path = CableRenderer.generate_cable_path(p_pc, p_router, segments=32)

    # Check Switch at U31 chassis bounding box
    sw_cx, sw_cy, sw_cz = switch.position
    sw_min_x = sw_cx - 0.22
    sw_max_x = sw_cx + 0.22
    sw_min_y = sw_cy - 0.043 / 2.0
    sw_max_y = sw_cy + 0.043 / 2.0
    sw_max_z = sw_cz + 0.250  # Faceplate plane

    # Any cable point that shares Switch Y and X range MUST have Z > sw_max_z
    for idx, (px, py, pz) in enumerate(path):
        if sw_min_y <= py <= sw_max_y and sw_min_x <= px <= sw_max_x:
            assert pz > sw_max_z + 0.02, (
                f"Cable point {idx} at ({px:.3f}, {py:.3f}, {pz:.3f}) penetrated Switch chassis! (sw_max_z={sw_max_z:.3f})"
            )

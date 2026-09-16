"""Unit tests for 42U Rack System and device occupancy."""

import pytest
from world.rack import Rack
from devices.router import Router
from devices.switch import Switch
from devices.pc import PC


def test_rack_dimensions_and_capacity():
    rack = Rack("Rack A", position=(0.0, 0.0, 0.0))
    assert rack.height_units == 42
    assert len(rack.devices) == 0
    assert len(rack.occupied_units) == 0


def test_install_devices_in_rack():
    rack = Rack("Rack A", position=(0.0, 0.0, 0.0))
    r1 = Router("r1", "R1")    # 2U
    sw1 = Switch("sw1", "SW1")  # 1U

    # Install R1 at U1-U2
    success, msg = rack.install_device(r1, 1)
    assert success
    assert r1 in rack.devices
    assert rack.get_device_at_u(1) == r1
    assert rack.get_device_at_u(2) == r1
    assert rack.get_device_at_u(3) is None

    # Install SW1 at U4
    success, msg = rack.install_device(sw1, 4)
    assert success
    assert sw1 in rack.devices
    assert rack.get_device_at_u(4) == sw1


def test_rack_occupancy_collision_prevention():
    rack = Rack("Rack A", position=(0.0, 0.0, 0.0))
    r1 = Router("r1", "R1")      # 2U (U1, U2)
    sw1 = Switch("sw1", "SW1")    # 1U

    rack.install_device(r1, 1)

    # Attempt to install SW1 at U2 (collision with R1!)
    success, msg = rack.install_device(sw1, 2)
    assert not success
    assert "already occupied" in msg
    assert sw1 not in rack.devices
    assert rack.get_device_at_u(2) == r1

    # Attempt to install a 2U PC at U2-U3 (collision at U2)
    pc = PC("pc1", "PC1")
    success, msg = rack.install_device(pc, 2)
    assert not success
    assert "already occupied" in msg


def test_rack_boundary_checks():
    rack = Rack("Rack A", position=(0.0, 0.0, 0.0))
    r1 = Router("r1", "R1")  # 2U

    # Slot < 1
    success, msg = rack.install_device(r1, 0)
    assert not success

    # Slot 42 for a 2U device exceeds top (42 + 2 - 1 = 43 > 42)
    success, msg = rack.install_device(r1, 42)
    assert not success
    assert "exceeds rack height" in msg

    # Slot 41 for a 2U device fits exactly (41, 42)
    success, msg = rack.install_device(r1, 41)
    assert success
    assert rack.get_device_at_u(41) == r1
    assert rack.get_device_at_u(42) == r1


def test_rack_device_removal():
    rack = Rack("Rack A", position=(0.0, 0.0, 0.0))
    r1 = Router("r1", "R1")
    rack.install_device(r1, 5)

    assert rack.get_device_at_u(5) == r1
    assert rack.get_device_at_u(6) == r1

    success, msg = rack.remove_device(r1)
    assert success
    assert r1 not in rack.devices
    assert rack.get_device_at_u(5) is None
    assert rack.get_device_at_u(6) is None
    assert r1.start_u is None
    assert r1.rack_id is None

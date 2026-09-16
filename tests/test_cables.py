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

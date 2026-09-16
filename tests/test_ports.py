"""Unit tests for Port states and status transitions."""

import pytest
from devices.port import Port, PortType, AdminStatus, LinkStatus


def test_port_initial_states():
    p = Port("p1", "Gi0/0", PortType.GIGABIT_ETHERNET)
    assert p.admin_status == AdminStatus.DOWN
    assert p.link_status == LinkStatus.DOWN
    assert not p.is_operational
    assert p.connected_port is None


def test_port_admin_up_no_cable():
    p = Port("p1", "Gi0/0")
    p.set_admin_status(AdminStatus.UP)
    assert p.admin_status == AdminStatus.UP
    # Without physical cable, operational link must stay DOWN
    assert p.link_status == LinkStatus.DOWN
    assert not p.is_operational


def test_port_cable_connection_both_up():
    p1 = Port("p1", "Gi0/0")
    p2 = Port("p2", "Gi0/1")

    p1.set_admin_status(AdminStatus.UP)
    p2.set_admin_status(AdminStatus.UP)

    success = p1.connect_to(p2)
    assert success
    assert p1.connected_port == p2
    assert p2.connected_port == p1

    # Both endpoints operational
    assert p1.link_status == LinkStatus.UP
    assert p2.link_status == LinkStatus.UP
    assert p1.is_operational
    assert p2.is_operational


def test_port_one_side_admin_down():
    p1 = Port("p1", "Gi0/0")
    p2 = Port("p2", "Gi0/1")

    p1.set_admin_status(AdminStatus.UP)
    p2.set_admin_status(AdminStatus.DOWN)

    p1.connect_to(p2)

    # p2 is admin down, so neither port can have link up
    assert p1.link_status == LinkStatus.DOWN
    assert p2.link_status == LinkStatus.DOWN
    assert not p1.is_operational
    assert not p2.is_operational


def test_port_disconnect():
    p1 = Port("p1", "Gi0/0")
    p2 = Port("p2", "Gi0/1")

    p1.set_admin_status(AdminStatus.UP)
    p2.set_admin_status(AdminStatus.UP)
    p1.connect_to(p2)

    assert p1.is_operational

    p1.disconnect()

    assert p1.connected_port is None
    assert p2.connected_port is None
    assert p1.link_status == LinkStatus.DOWN
    assert p2.link_status == LinkStatus.DOWN

"""Unit tests for NetworkEngine, Subnetting, MAC learning, and ICMP Ping."""

import pytest
from devices.router import Router
from devices.switch import Switch
from devices.pc import PC
from devices.port import AdminStatus
from network.subnet import (
    ip_to_int,
    int_to_ip,
    get_network_address,
    is_same_subnet,
    cidr_to_netmask,
    netmask_to_cidr,
)
from network.network_engine import NetworkEngine
from cables.cable_manager import CableManager


def test_subnet_math():
    assert ip_to_int("192.168.1.1") == 3232235777
    assert int_to_ip(3232235777) == "192.168.1.1"
    assert get_network_address("192.168.1.55", "255.255.255.0") == "192.168.1.0"
    assert is_same_subnet("192.168.1.10", "192.168.1.20", "255.255.255.0")
    assert not is_same_subnet("192.168.1.10", "192.168.2.20", "255.255.255.0")
    assert netmask_to_cidr("255.255.255.0") == 24
    assert cidr_to_netmask(24) == "255.255.255.0"
    assert cidr_to_netmask(16) == "255.255.0.0"


def test_network_engine_end_to_end_ping_success():
    engine = NetworkEngine()
    cable_mgr = CableManager()

    # 1. Create topology: PC1 <-> SW1 <-> R1
    pc1 = PC("pc1", "PC1")
    sw1 = Switch("sw1", "SW1")
    r1 = Router("r1", "R1")

    engine.register_device(pc1)
    engine.register_device(sw1)
    engine.register_device(r1)

    # 2. Configure Router Gi0/0
    r1_g0 = r1.get_port("Gi0/0")
    r1_g0.ip_address = "192.168.1.1"
    r1_g0.subnet_mask = "255.255.255.0"
    r1_g0.set_admin_status(AdminStatus.UP)

    # 3. Configure PC1
    pc1.set_ip_config("192.168.1.10", "255.255.255.0", "192.168.1.1")

    # 4. Patch Cables
    cable_mgr.connect_ports(pc1.eth0, sw1.get_port("Gi0/1"))
    cable_mgr.connect_ports(r1_g0, sw1.get_port("Gi0/24"))

    engine.update_links()

    # 5. Verify Links are operational
    assert pc1.eth0.is_operational
    assert r1_g0.is_operational
    assert sw1.get_port("Gi0/1").is_operational
    assert sw1.get_port("Gi0/24").is_operational

    # 6. Execute Ping from PC1 to Router R1 (192.168.1.1)
    result = engine.ping(pc1, "192.168.1.1", count=4)
    assert result.success
    assert result.packets_received == 4
    assert result.packet_loss_percent == 0.0

    # 7. Verify Switch learned PC1 MAC address
    mac_entry = sw1.lookup_mac(pc1.eth0.mac_address)
    assert mac_entry == "Gi0/1"


def test_network_engine_ping_failure_on_cable_disconnect():
    engine = NetworkEngine()
    cable_mgr = CableManager()

    pc1 = PC("pc1", "PC1")
    r1 = Router("r1", "R1")
    engine.register_device(pc1)
    engine.register_device(r1)

    r1_g0 = r1.get_port("Gi0/0")
    r1_g0.ip_address = "192.168.1.1"
    r1_g0.subnet_mask = "255.255.255.0"
    r1_g0.set_admin_status(AdminStatus.UP)

    pc1.set_ip_config("192.168.1.10", "255.255.255.0")

    # Connect directly PC1 <-> R1
    _, cable, _ = cable_mgr.connect_ports(pc1.eth0, r1_g0)
    engine.update_links()

    # Ping succeeds
    res1 = engine.ping(pc1, "192.168.1.1")
    assert res1.success

    # Disconnect cable
    cable_mgr.remove_cable(cable.cable_id)
    engine.update_links()

    # Ping now fails due to physical link down!
    res2 = engine.ping(pc1, "192.168.1.1")
    assert not res2.success
    assert res2.packets_received == 0
    assert any("timed out" in line or "cable disconnected" in line for line in res2.output_lines)


def test_network_engine_ping_failure_on_interface_shutdown():
    engine = NetworkEngine()
    cable_mgr = CableManager()

    pc1 = PC("pc1", "PC1")
    r1 = Router("r1", "R1")
    engine.register_device(pc1)
    engine.register_device(r1)

    r1_g0 = r1.get_port("Gi0/0")
    r1_g0.ip_address = "192.168.1.1"
    r1_g0.subnet_mask = "255.255.255.0"
    r1_g0.set_admin_status(AdminStatus.UP)

    pc1.set_ip_config("192.168.1.10", "255.255.255.0")
    cable_mgr.connect_ports(pc1.eth0, r1_g0)
    engine.update_links()

    # Administratively shutdown the router interface
    r1_g0.set_admin_status(AdminStatus.DOWN)
    engine.update_links()

    # Ping fails because destination is not operational
    res = engine.ping(pc1, "192.168.1.1")
    assert not res.success

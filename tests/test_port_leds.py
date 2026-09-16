"""Tests verifying real-time port status LED states on Router, Switch, and PC during cabling and configuration."""

import pytest
from devices.device_factory import DeviceFactory
from devices.port import AdminStatus, LinkStatus
from devices.models.device_model import DeviceModel
from cables.cable_manager import CableManager
from network.network_engine import NetworkEngine
from cli.router_cli import RouterCLI
from cli.switch_cli import SwitchCLI
from cli.pc_cli import PCCLI


def test_port_led_unconnected_state():
    """Unconnected ports must have their Link and Activity LEDs turned OFF."""
    router = DeviceFactory.create_device("Router", "R1")
    switch = DeviceFactory.create_device("Switch", "SW1")
    pc = DeviceFactory.create_device("PC", "PC1")

    for port in list(router.ports.values()) + list(switch.ports.values()) + list(pc.ports.values()):
        lnk_c, act_c = DeviceModel.get_port_led_colors(port)
        # Off color is dark gray
        assert lnk_c == (0.12, 0.14, 0.17)
        assert act_c == (0.12, 0.14, 0.17)


def test_port_led_connected_and_operational():
    """Connected ports with Admin UP must show bright green Link & Activity LEDs."""
    cable_mgr = CableManager()
    router = DeviceFactory.create_device("Router", "R1")
    switch = DeviceFactory.create_device("Switch", "SW1")

    r_port = router.get_port("Gi0/0")
    sw_port = switch.get_port("Gi0/1")
    assert r_port is not None and sw_port is not None

    # Connect ports
    ok, cable, _ = cable_mgr.connect_ports(r_port, sw_port)
    assert ok is True

    # Bring router port UP
    r_port.set_admin_status(AdminStatus.UP)
    assert r_port.is_operational is True
    assert sw_port.is_operational is True

    # Check LED colors
    r_lnk, r_act = DeviceModel.get_port_led_colors(r_port)
    sw_lnk, sw_act = DeviceModel.get_port_led_colors(sw_port)

    # Vibrant Green
    assert r_lnk == (0.12, 0.98, 0.28)
    assert r_act == (0.22, 1.00, 0.40)
    assert sw_lnk == (0.12, 0.98, 0.28)
    assert sw_act == (0.22, 1.00, 0.40)


def test_port_led_amber_when_admin_down():
    """Connected ports must switch to AMBER when administratively disabled."""
    cable_mgr = CableManager()
    net_engine = NetworkEngine()
    router = DeviceFactory.create_device("Router", "R1")
    switch = DeviceFactory.create_device("Switch", "SW1")

    r_port = router.get_port("Gi0/0")
    sw_port = switch.get_port("Gi0/1")
    cable_mgr.connect_ports(r_port, sw_port)
    r_port.set_admin_status(AdminStatus.UP)

    # Initially Green
    assert r_port.is_operational is True

    # Shutdown router interface via RouterCLI
    cli = RouterCLI(router, net_engine)
    cli.execute("enable")
    cli.execute("configure terminal")
    cli.execute("interface GigabitEthernet0/0")
    out = cli.execute("shutdown")
    assert any("down" in line.lower() for line in out)

    assert r_port.admin_status == AdminStatus.DOWN
    assert r_port.is_operational is False

    # Check LEDs: Must show solid Amber
    r_lnk, r_act = DeviceModel.get_port_led_colors(r_port)
    sw_lnk, sw_act = DeviceModel.get_port_led_colors(sw_port)

    amber = (0.98, 0.62, 0.08)
    off = (0.12, 0.14, 0.17)
    assert r_lnk == amber
    assert r_act == off
    assert sw_lnk == amber
    assert sw_act == off

    # Re-enable interface via 'no shutdown'
    out2 = cli.execute("no shutdown")
    assert any("up" in line.lower() for line in out2)

    r_lnk2, r_act2 = DeviceModel.get_port_led_colors(r_port)
    sw_lnk2, sw_act2 = DeviceModel.get_port_led_colors(sw_port)
    assert r_lnk2 == (0.12, 0.98, 0.28)
    assert sw_lnk2 == (0.12, 0.98, 0.28)


def test_port_led_unplug_cable_turns_off():
    """Unplugging a connected cable must immediately turn port LEDs OFF."""
    cable_mgr = CableManager()
    router = DeviceFactory.create_device("Router", "R1")
    switch = DeviceFactory.create_device("Switch", "SW1")

    r_port = router.get_port("Gi0/0")
    sw_port = switch.get_port("Gi0/1")
    _, cable, _ = cable_mgr.connect_ports(r_port, sw_port)
    r_port.set_admin_status(AdminStatus.UP)

    assert r_port.is_operational is True

    # Unplug cable
    cable_mgr.remove_cable(cable.cable_id)

    r_lnk, r_act = DeviceModel.get_port_led_colors(r_port)
    sw_lnk, sw_act = DeviceModel.get_port_led_colors(sw_port)
    off = (0.12, 0.14, 0.17)

    assert r_lnk == off
    assert r_act == off
    assert sw_lnk == off
    assert sw_act == off


def test_pc_adapter_status_led_control():
    """PC Ethernet adapter LEDs respond to CLI disable/enable and cabling."""
    cable_mgr = CableManager()
    pc = DeviceFactory.create_device("PC", "PC1")
    switch = DeviceFactory.create_device("Switch", "SW1")

    cable_mgr.connect_ports(pc.eth0, switch.get_port("Gi0/2"))
    assert pc.eth0.is_operational is True

    # PC CLI disable eth0
    cli = PCCLI(pc)
    cli.execute("disable eth0")
    assert pc.eth0.admin_status == AdminStatus.DOWN

    lnk_c, act_c = DeviceModel.get_port_led_colors(pc.eth0)
    assert lnk_c == (0.98, 0.62, 0.08)  # Amber

    # PC CLI enable eth0
    cli.execute("enable eth0")
    assert pc.eth0.admin_status == AdminStatus.UP

    lnk_c2, act_c2 = DeviceModel.get_port_led_colors(pc.eth0)
    assert lnk_c2 == (0.12, 0.98, 0.28)  # Green

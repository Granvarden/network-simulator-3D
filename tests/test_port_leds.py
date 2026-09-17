"""Unit tests for realistic physical Port Status LEDs across PC, Switch, and Router."""

import pytest
from config.graphics_config import GraphicsConfig
from devices.device_factory import DeviceFactory
from devices.port import Port, PortType, AdminStatus, LinkStatus
from cables.cable_manager import CableManager
from cli.router_cli import RouterCLI
from cli.switch_cli import SwitchCLI
from cli.pc_cli import PCCLI


def test_port_led_disconnected():
    p = Port("p1", "Gi0/0")
    p.admin_status = AdminStatus.UP
    link_col, act_col = p.get_led_colors(power_state=True)
    assert link_col == GraphicsConfig.COLOR_LED_OFF
    assert act_col == GraphicsConfig.COLOR_LED_OFF


def test_port_led_connected_operational():
    p1 = Port("p1", "Gi0/0")
    p2 = Port("p2", "Gi0/1")
    p1.admin_status = AdminStatus.UP
    p2.admin_status = AdminStatus.UP
    p1.connect_to(p2)

    assert p1.is_operational
    link_col, act_col = p1.get_led_colors(power_state=True)
    assert link_col == GraphicsConfig.COLOR_LED_GREEN
    assert act_col in (GraphicsConfig.COLOR_LED_GREEN, GraphicsConfig.COLOR_LED_ACTIVITY)


def test_port_led_connected_admin_down_shows_amber():
    p1 = Port("p1", "Gi0/0")
    p2 = Port("p2", "Gi0/1")
    p1.admin_status = AdminStatus.DOWN  # shutdown
    p2.admin_status = AdminStatus.UP
    p1.connect_to(p2)

    # p1 is shutdown -> Link LED must be solid AMBER, Act LED is OFF
    link1, act1 = p1.get_led_colors(power_state=True)
    assert link1 == GraphicsConfig.COLOR_LED_AMBER
    assert act1 == GraphicsConfig.COLOR_LED_OFF

    # p2 has cable connected, but peer is down -> Link LED must be AMBER
    link2, act2 = p2.get_led_colors(power_state=True)
    assert link2 == GraphicsConfig.COLOR_LED_AMBER
    assert act2 == GraphicsConfig.COLOR_LED_OFF


def test_port_led_power_off():
    p1 = Port("p1", "Gi0/0")
    p2 = Port("p2", "Gi0/1")
    p1.admin_status = AdminStatus.UP
    p2.admin_status = AdminStatus.UP
    p1.connect_to(p2)

    # When device power is off, LEDs must be completely off
    link_col, act_col = p1.get_led_colors(power_state=False)
    assert link_col == GraphicsConfig.COLOR_LED_OFF
    assert act_col == GraphicsConfig.COLOR_LED_OFF


def test_router_cli_shutdown_no_shutdown_led_transition():
    router = DeviceFactory.create_device("Router", "R1")
    switch = DeviceFactory.create_device("Switch", "SW1")
    cable_mgr = CableManager()

    r_g0 = router.get_port("Gi0/0")
    sw_g1 = switch.get_port("Gi0/1")
    r_g0.set_admin_status(AdminStatus.UP)
    sw_g1.set_admin_status(AdminStatus.UP)
    cable_mgr.connect_ports(r_g0, sw_g1)

    # 1. Initially both up -> Green
    link_r, _ = r_g0.get_led_colors(router.power_state)
    link_sw, _ = sw_g1.get_led_colors(switch.power_state)
    assert link_r == GraphicsConfig.COLOR_LED_GREEN
    assert link_sw == GraphicsConfig.COLOR_LED_GREEN

    # 2. Shutdown via CLI
    cli = RouterCLI(router)
    cli.execute("enable")
    cli.execute("conf t")
    cli.execute("interface Gi0/0")
    cli.execute("shutdown")

    assert r_g0.admin_status == AdminStatus.DOWN
    # Both endpoints should now display AMBER
    link_r, _ = r_g0.get_led_colors(router.power_state)
    link_sw, _ = sw_g1.get_led_colors(switch.power_state)
    assert link_r == GraphicsConfig.COLOR_LED_AMBER
    assert link_sw == GraphicsConfig.COLOR_LED_AMBER

    # 3. Re-enable via CLI (no shutdown)
    cli.execute("no shutdown")
    assert r_g0.admin_status == AdminStatus.UP
    link_r, _ = r_g0.get_led_colors(router.power_state)
    link_sw, _ = sw_g1.get_led_colors(switch.power_state)
    assert link_r == GraphicsConfig.COLOR_LED_GREEN
    assert link_sw == GraphicsConfig.COLOR_LED_GREEN

    # 4. Unplug cable -> Immediately turns OFF
    cable = cable_mgr.get_cable_for_port(r_g0)
    cable_mgr.remove_cable(cable.cable_id)

    link_r, _ = r_g0.get_led_colors(router.power_state)
    link_sw, _ = sw_g1.get_led_colors(switch.power_state)
    assert link_r == GraphicsConfig.COLOR_LED_OFF
    assert link_sw == GraphicsConfig.COLOR_LED_OFF


def test_router_console_port_led():
    router = DeviceFactory.create_device("Router", "R1")
    con_port = router.get_port("Console")
    assert con_port is not None
    assert con_port.port_type == PortType.CONSOLE

    # Unplugged -> OFF
    link_col, act_col = con_port.get_led_colors(router.power_state)
    assert link_col == GraphicsConfig.COLOR_LED_OFF
    assert act_col == GraphicsConfig.COLOR_LED_OFF

    # Plug in console rollover cable to another device/adapter
    peer_con = Port("term_con", "Console", PortType.CONSOLE)
    con_port.connect_to(peer_con)

    # Plugged in -> Sky Blue Console LED
    link_col, act_col = con_port.get_led_colors(router.power_state)
    assert link_col == GraphicsConfig.COLOR_LED_CONSOLE
    assert act_col == GraphicsConfig.COLOR_LED_CONSOLE

    # Disconnect -> OFF
    con_port.disconnect()
    link_col, act_col = con_port.get_led_colors(router.power_state)
    assert link_col == GraphicsConfig.COLOR_LED_OFF


def test_pc_eth0_cli_enable_disable_led():
    pc = DeviceFactory.create_device("PC", "PC1")
    switch = DeviceFactory.create_device("Switch", "SW1")
    cable_mgr = CableManager()

    sw_g2 = switch.get_port("Gi0/2")
    cable_mgr.connect_ports(pc.eth0, sw_g2)

    # Initial state: Connected and UP -> Green
    link_col, _ = pc.eth0.get_led_colors(pc.power_state)
    assert link_col == GraphicsConfig.COLOR_LED_GREEN

    # Disable via CLI
    cli = PCCLI(pc)
    cli.execute("ipconfig /disable")
    assert pc.eth0.admin_status == AdminStatus.DOWN

    # Should turn AMBER
    link_col, _ = pc.eth0.get_led_colors(pc.power_state)
    assert link_col == GraphicsConfig.COLOR_LED_AMBER

    # Enable via netsh
    cli.execute("netsh interface set interface eth0 admin=enable")
    assert pc.eth0.admin_status == AdminStatus.UP

    # Should return to GREEN
    link_col, _ = pc.eth0.get_led_colors(pc.power_state)
    assert link_col == GraphicsConfig.COLOR_LED_GREEN


def test_switch_all_24_ports_led_functionality():
    switch = DeviceFactory.create_device("Switch", "SW1")
    assert len(switch.ports) == 24

    # All initially unplugged -> all OFF
    for i in range(1, 25):
        port = switch.get_port(f"Gi0/{i}")
        assert port is not None
        link_col, act_col = port.get_led_colors(switch.power_state)
        assert link_col == GraphicsConfig.COLOR_LED_OFF
        assert act_col == GraphicsConfig.COLOR_LED_OFF

    # Plug cables into loopback pair (Gi0/1 <-> Gi0/2)
    p1 = switch.get_port("Gi0/1")
    p2 = switch.get_port("Gi0/2")
    p1.connect_to(p2)

    link1, act1 = p1.get_led_colors(switch.power_state)
    link2, act2 = p2.get_led_colors(switch.power_state)
    assert link1 == GraphicsConfig.COLOR_LED_GREEN
    assert link2 == GraphicsConfig.COLOR_LED_GREEN

    # Other 22 ports remain OFF
    for i in range(3, 25):
        port = switch.get_port(f"Gi0/{i}")
        l_col, _ = port.get_led_colors(switch.power_state)
        assert l_col == GraphicsConfig.COLOR_LED_OFF

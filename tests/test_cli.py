"""Unit tests for Cisco IOS-inspired CLI engine and state mutations."""

import pytest
from devices.router import Router
from devices.switch import Switch
from devices.pc import PC
from devices.port import AdminStatus
from cli.router_cli import RouterCLI
from cli.switch_cli import SwitchCLI
from cli.pc_cli import PCCLI
from cli.cli_context import CLIMode


def test_router_cli_mode_transitions():
    r = Router("r1", "Router")
    cli = RouterCLI(r)

    # Initial mode is User EXEC
    assert cli.context.mode == CLIMode.USER_EXEC
    assert cli.context.get_prompt(r.hostname) == "Router>"

    # enable -> Privileged EXEC
    cli.execute("enable")
    assert cli.context.mode == CLIMode.PRIVILEGED_EXEC
    assert cli.context.get_prompt(r.hostname) == "Router#"

    # configure terminal -> Global Config
    cli.execute("configure terminal")
    assert cli.context.mode == CLIMode.GLOBAL_CONFIG
    assert cli.context.get_prompt(r.hostname) == "Router(config)#"

    # interface Gi0/0 -> Interface Config
    cli.execute("interface Gi0/0")
    assert cli.context.mode == CLIMode.INTERFACE_CONFIG
    assert cli.context.get_prompt(r.hostname) == "Router(config-if)#"

    # exit -> Global Config
    cli.execute("exit")
    assert cli.context.mode == CLIMode.GLOBAL_CONFIG

    # exit -> Privileged EXEC
    cli.execute("exit")
    assert cli.context.mode == CLIMode.PRIVILEGED_EXEC


def test_router_cli_state_mutations():
    r = Router("r1", "Router")
    cli = RouterCLI(r)

    cli.execute("enable")
    cli.execute("conf t")

    # 1. Mutate Hostname
    cli.execute("hostname Core-R1")
    assert r.hostname == "Core-R1"
    assert cli.context.get_prompt(r.hostname) == "Core-R1(config)#"

    # 2. Enter Interface
    cli.execute("interface Gi0/0")

    # 3. Assign IP & Mask
    cli.execute("ip address 192.168.1.1 255.255.255.0")
    g0 = r.get_port("Gi0/0")
    assert g0.ip_address == "192.168.1.1"
    assert g0.subnet_mask == "255.255.255.0"

    # 4. Toggling shutdown / no shutdown
    cli.execute("shutdown")
    assert g0.admin_status == AdminStatus.DOWN

    cli.execute("no shutdown")
    assert g0.admin_status == AdminStatus.UP

    # 5. Static route in Global Config
    cli.execute("exit")
    cli.execute("ip route 10.0.0.0 255.255.255.0 192.168.1.254")
    assert ("10.0.0.0", "255.255.255.0", "192.168.1.254") in r.static_routes


def test_switch_cli_vlan_mutation():
    sw = Switch("sw1", "Switch")
    cli = SwitchCLI(sw)

    cli.execute("enable")
    cli.execute("conf t")
    cli.execute("interface Gi0/5")
    cli.execute("switchport access vlan 20")

    port = sw.get_port("Gi0/5")
    assert port.vlan == 20


def test_pc_cli_ipconfig_set():
    pc = PC("pc1", "PC1")
    cli = PCCLI(pc)

    out = cli.execute("ipconfig /set 192.168.1.50 255.255.255.0 192.168.1.1")
    assert pc.eth0.ip_address == "192.168.1.50"
    assert pc.eth0.subnet_mask == "255.255.255.0"
    assert pc.default_gateway == "192.168.1.1"
    assert any("updated successfully" in line for line in out)

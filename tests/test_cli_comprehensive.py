"""Comprehensive test suite for Cisco IOS CLI, Single Source of Truth, and Service Layer architecture."""

import pytest
from devices.router import Router
from devices.switch import Switch
from devices.pc import PC
from devices.port import AdminStatus, LinkStatus
from devices.interface_normalizer import InterfaceNormalizer
from devices.mac_generator import MacAddressGenerator
from devices.vlan_database import VLANDatabase
from network.network_engine import NetworkEngine
from network.routing_table import RouteType
from cli.router_cli import RouterCLI
from cli.switch_cli import SwitchCLI
from cli.pc_cli import PCCLI
from cli.cli_context import CLIMode
from cli.cli_engine import CLIEngine
from services.interface_service import InterfaceService
from services.vlan_service import VlanService
from services.routing_service import RoutingService
from services.device_service import DeviceService


# =====================================================================
# 1. Interface Normalizer & Port Resolution Tests
# =====================================================================

def test_interface_normalizer_canonical_and_short():
    assert InterfaceNormalizer.normalize("g0/0") == "GigabitEthernet0/0"
    assert InterfaceNormalizer.normalize("gi0/1") == "GigabitEthernet0/1"
    assert InterfaceNormalizer.normalize("Gi0/2") == "GigabitEthernet0/2"
    assert InterfaceNormalizer.normalize("gigabitethernet0/3") == "GigabitEthernet0/3"
    assert InterfaceNormalizer.normalize("fa0/1") == "FastEthernet0/1"
    assert InterfaceNormalizer.normalize("eth0") == "eth0"

    assert InterfaceNormalizer.to_short("GigabitEthernet0/0") == "Gi0/0"
    assert InterfaceNormalizer.to_short("FastEthernet0/1") == "Fa0/1"
    assert InterfaceNormalizer.to_short("eth0") == "eth0"


def test_device_port_lookup_aliases():
    r = Router("r1", "Core-R1")
    # All aliases resolve to the same Port instance
    p1 = r.get_port("Gi0/0")
    p2 = r.get_port("gi0/0")
    p3 = r.get_port("g0/0")
    p4 = r.get_port("GigabitEthernet0/0")
    assert p1 is not None
    assert p1 == p2 == p3 == p4
    assert p1.canonical_name == "GigabitEthernet0/0"
    assert p1.short_name == "Gi0/0"

    # Dictionary access transparently resolves aliases
    assert r.ports["Gi0/0"] == p1
    assert r.ports["GigabitEthernet0/0"] == p1
    assert r.ports["g0/0"] == p1


# =====================================================================
# 2. Deterministic Hexadecimal MAC Address Generator Tests
# =====================================================================

def test_deterministic_mac_generator():
    # Verify MAC format
    mac1 = MacAddressGenerator.generate("r1", 0)
    mac2 = MacAddressGenerator.generate("r1", 0)
    mac3 = MacAddressGenerator.generate("r1", 1)
    mac_sw = MacAddressGenerator.generate("sw1", 5)

    assert mac1 == mac2, "Generator must be deterministic"
    assert mac1 != mac3, "Different port indexes on same device must have different MACs"
    assert MacAddressGenerator.validate(mac1)
    assert MacAddressGenerator.validate(mac_sw)

    # Validate RFC locally administered unicast bit
    first_byte = int(mac1.split(":")[0], 16)
    assert (first_byte & 0x02) == 0x02, "Bit 1 must be 1 (locally administered)"
    assert (first_byte & 0x01) == 0x00, "Bit 0 must be 0 (unicast)"

    # Verify Cisco format conversion
    cisco_mac = MacAddressGenerator.to_cisco_format(mac1)
    assert len(cisco_mac.split(".")) == 3
    assert MacAddressGenerator.validate(cisco_mac)


def test_device_initial_mac_addresses_are_valid():
    r = Router("r1", "Router1")
    sw = Switch("sw1", "Switch1")
    pc = PC("pc1", "PC1")

    for port in r.ports.values():
        if port.port_type.value != "Console":
            assert MacAddressGenerator.validate(port.mac_address)

    for port in sw.ports.values():
        assert MacAddressGenerator.validate(port.mac_address)

    assert MacAddressGenerator.validate(pc.eth0.mac_address)


# =====================================================================
# 3. Routing Table as Single Source of Truth Tests
# =====================================================================

def test_routing_table_single_source_of_truth():
    r = Router("r1", "Router1")
    rt = r.routing_table

    # Add static route
    r.add_static_route("10.0.0.0", "255.255.255.0", "192.168.1.254")
    assert len(r.static_routes) == 1
    assert r.static_routes[0] == ("10.0.0.0", "255.255.255.0", "192.168.1.254")

    # LPM lookup
    match = rt.lookup("10.0.0.5")
    assert match is not None
    assert match.network == "10.0.0.0"
    assert match.next_hop == "192.168.1.254"

    # Default route S*
    r.add_static_route("0.0.0.0", "0.0.0.0", "192.168.1.1")
    def_match = rt.lookup("8.8.8.8")
    assert def_match is not None
    assert def_match.route_type == RouteType.DEFAULT

    # Interface directly connected route synchronization
    p0 = r.get_port("Gi0/0")
    p0.ip_address = "172.16.1.1"
    p0.subnet_mask = "255.255.255.0"
    p0.admin_status = AdminStatus.UP
    p0.link_status = LinkStatus.UP
    r.sync_connected_routes()

    c_match = rt.lookup("172.16.1.50")
    assert c_match is not None
    assert c_match.route_type == RouteType.CONNECTED
    assert c_match.interface == "GigabitEthernet0/0"

    # Remove static route
    r.remove_static_route("10.0.0.0", "255.255.255.0", "192.168.1.254")
    assert len(r.static_routes) == 1  # only default route remains


# =====================================================================
# 4. VLAN Database Single Source of Truth Tests
# =====================================================================

def test_vlan_database_single_source_of_truth():
    sw = Switch("sw1", "Switch1")
    vdb = sw.vlan_database

    # Default VLANs
    assert vdb.has_vlan(1)
    assert vdb.get_vlan(1).name == "default"
    assert vdb.has_vlan(1002)

    # Creating user VLANs
    v10 = vdb.add_vlan(10, "Sales")
    assert v10.name == "Sales"
    assert sw.vlans[10] == "Sales"

    # Renaming VLAN
    vdb.set_vlan_name(10, "Corporate-Sales")
    assert vdb.get_vlan(10).name == "Corporate-Sales"

    # Protected VLANs cannot be deleted or renamed
    assert not vdb.remove_vlan(1)
    assert not vdb.set_vlan_name(1, "Hacked")
    assert not vdb.remove_vlan(1002)

    # User VLAN can be deleted
    assert vdb.remove_vlan(10)
    assert not vdb.has_vlan(10)


# =====================================================================
# 5. CLI Abbreviations, Ambiguity, Caret Positioning & Quotes Tests
# =====================================================================

def test_cli_abbreviation_and_piping():
    r = Router("r1", "Core-R1")
    cli = RouterCLI(r)

    # 'en' -> 'enable'
    cli.execute("en")
    assert cli.context.mode == CLIMode.PRIVILEGED_EXEC

    # 'conf t' -> 'configure terminal'
    cli.execute("conf t")
    assert cli.context.mode == CLIMode.GLOBAL_CONFIG

    # 'int g0/0' -> 'interface Gi0/0'
    cli.execute("int g0/0")
    assert cli.context.mode == CLIMode.INTERFACE_CONFIG
    assert cli.context.active_interface == "GigabitEthernet0/0"

    # 'desc "Link to Spine SW1"' -> quotes handling
    cli.execute('desc "Link to Spine SW1"')
    p0 = r.get_port("Gi0/0")
    assert p0.description == "Link to Spine SW1"

    # 'no shut' -> 'no shutdown'
    cli.execute("no shut")
    assert p0.admin_status == AdminStatus.UP

    # Output filtering pipe: 'do sh run | inc hostname'
    out = cli.execute("do sh run | inc hostname")
    assert any("hostname Core-R1" in line for line in out)


def test_cli_ambiguity_and_syntax_error():
    r = Router("r1", "Router")
    cli = RouterCLI(r)

    # In user exec: 's' matches 'show' unambiguously
    # In privileged exec: 'c' matches both 'configure' and 'copy' -> Ambiguous!
    cli.execute("enable")
    out = cli.execute("c")
    assert any("% Ambiguous command" in line for line in out)

    # Unknown command produces caret marker
    out = cli.execute("invalidcommand")
    assert any("% Invalid input detected at '^' marker." in line for line in out)

    # Incomplete command
    out = cli.execute("show ip")
    assert any("% Incomplete command." in line for line in out)


# =====================================================================
# 6. Service Layer Validation & Diagnostics Tests
# =====================================================================

def test_service_layer_duplicate_ip_and_broadcast_rejection():
    r = Router("r1", "Router")

    # 1. Reject network address for /24
    ok, msg = InterfaceService.set_ip_address(r, "Gi0/0", "192.168.1.0", "255.255.255.0")
    assert not ok
    assert "network address" in msg

    # 2. Reject broadcast address for /24
    ok, msg = InterfaceService.set_ip_address(r, "Gi0/0", "192.168.1.255", "255.255.255.0")
    assert not ok
    assert "broadcast address" in msg

    # 3. Valid assignment
    ok, _ = InterfaceService.set_ip_address(r, "Gi0/0", "192.168.1.1", "255.255.255.0")
    assert ok

    # 4. Duplicate IP assignment on different interface
    ok, msg = InterfaceService.set_ip_address(r, "Gi0/1", "192.168.1.1", "255.255.255.0")
    assert not ok
    assert "conflict" in msg.lower()


def test_switch_cli_vlan_service_integration():
    sw = Switch("sw1", "Switch")
    cli = SwitchCLI(sw)

    cli.execute("enable")
    cli.execute("conf t")
    cli.execute("vlan 50")
    assert cli.context.mode == CLIMode.VLAN_CONFIG

    cli.execute("name Engineering")
    assert sw.vlan_database.get_vlan(50).name == "Engineering"

    cli.execute("exit")
    assert cli.context.mode == CLIMode.GLOBAL_CONFIG

    # Assign port
    cli.execute("interface Gi0/10")
    cli.execute("switchport access vlan 50")
    p10 = sw.get_port("Gi0/10")
    assert p10.vlan == 50

    # show vlan brief includes Gi0/10
    out = cli.execute("do show vlan brief")
    assert any("Engineering" in line and "Gi0/10" in line for line in out)


# =====================================================================
# 7. Multi-Device CLI Session Isolation Tests
# =====================================================================

def test_cli_engine_session_isolation():
    r1 = Router("r1", "Router1")
    sw1 = Switch("sw1", "Switch1")
    engine = CLIEngine()

    # 1. Attach to Router1 and move to INTERFACE_CONFIG
    engine.attach_device(r1)
    engine.active_session.input_buffer = "enable"
    engine.submit_command()
    engine.active_session.input_buffer = "conf t"
    engine.submit_command()
    engine.active_session.input_buffer = "interface Gi0/0"
    engine.submit_command()

    assert engine.get_prompt() == "Router1(config-if)#"
    assert len(engine.history) == 3

    # 2. Switch terminal to Switch1
    engine.attach_device(sw1)
    # Switch1 must start fresh in USER_EXEC, not in config-if!
    assert engine.get_prompt() == "Switch1>"
    assert len(engine.history) == 0

    engine.active_session.input_buffer = "enable"
    engine.submit_command()
    assert engine.get_prompt() == "Switch1#"

    # 3. Switch back to Router1
    engine.attach_device(r1)
    # Router1 session must still be in config-if with its original history!
    assert engine.get_prompt() == "Router1(config-if)#"
    assert len(engine.history) == 3
    assert engine.history[-1] == "interface Gi0/0"


# =====================================================================
# 8. PC Workstation CLI Commands Tests
# =====================================================================

def test_pc_cli_full_features():
    pc = PC("pc1", "Engineer-PC")
    cli = PCCLI(pc)

    # Prompt
    assert cli.get_prompt() == "C:\\Users\\Engineer>"

    # ipconfig /set
    out = cli.execute("ipconfig /set 10.0.0.15 255.255.255.0 10.0.0.1")
    assert pc.eth0.ip_address == "10.0.0.15"
    assert pc.default_gateway == "10.0.0.1"

    # ipconfig /all
    out = cli.execute("ipconfig /all")
    assert any("Engineer-PC" in line for line in out)
    assert any("10.0.0.15" in line for line in out)

    # cls
    res = cli.parser.execute("cls", pc, cli.context)
    assert res.clear_screen

    # arp -a
    out = cli.execute("arp -a")
    assert any("10.0.0.1" in line for line in out)


# =====================================================================
# 9. Tab Completion & Context-Sensitive Help Tests
# =====================================================================

def test_cli_tab_completion_and_help():
    from cli.completer import CLICompleter

    r = Router("r1", "Core-R1")
    cli = RouterCLI(r)

    # 1. Tab complete 'en' -> 'enable '
    completed, matches = CLICompleter.complete("en", cli)
    assert completed == "enable "

    # 2. Context-sensitive Help '?'
    help_out = cli.execute("?")
    assert any("enable" in line for line in help_out)

    # 3. Mode transition then complete in privileged mode
    cli.execute("enable")
    completed, matches = CLICompleter.complete("conf", cli)
    assert completed == "configure "

    cli.execute("conf t")
    # Subcommand complete in config mode
    completed, matches = CLICompleter.complete("inter", cli)
    assert completed == "interface "


# =====================================================================
# 10. Dynamic Running-Config Generation Tests
# =====================================================================

def test_dynamic_running_config_generation():
    r = Router("r1", "Core-R1")
    cli = RouterCLI(r)

    cli.execute("enable")
    cli.execute("conf t")
    cli.execute("hostname Gateway-R1")
    cli.execute("interface Gi0/0")
    cli.execute("ip address 192.168.10.1 255.255.255.0")
    cli.execute("description Uplink-To-ISP")
    cli.execute("no shutdown")
    cli.execute("exit")
    cli.execute("ip route 0.0.0.0 0.0.0.0 192.168.10.254")
    cli.execute("end")

    # show running-config must reflect LIVE state directly
    out = cli.execute("show run")
    full_text = "\n".join(out)

    assert "hostname Gateway-R1" in full_text
    assert "interface GigabitEthernet0/0" in full_text
    assert "ip address 192.168.10.1 255.255.255.0" in full_text
    assert "description Uplink-To-ISP" in full_text
    assert "ip route 0.0.0.0 0.0.0.0 192.168.10.254" in full_text
    assert "shutdown" not in full_text.split("interface GigabitEthernet0/0")[1].split("interface")[0]


# =====================================================================
# 11. End and Ctrl+Z Mode Navigation Tests
# =====================================================================

def test_end_and_ctrl_z_mode_navigation():
    r = Router("r1", "Router1")
    cli = RouterCLI(r)

    cli.execute("enable")
    cli.execute("conf t")
    cli.execute("interface Gi0/0")
    assert cli.context.mode == CLIMode.INTERFACE_CONFIG

    # 'end' takes us straight back to PRIVILEGED_EXEC
    cli.execute("end")
    assert cli.context.mode == CLIMode.PRIVILEGED_EXEC
    assert cli.context.active_interface is None


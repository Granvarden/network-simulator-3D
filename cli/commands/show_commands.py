"""Cisco IOS show diagnostic commands."""

from typing import Any, List
from ..prompts.mode import CLIMode
from ..command_result import CommandResult
from ..command_registry import CommandRegistry
from ..cli_context import CLIContext
from services.device_service import DeviceService
from services.interface_service import InterfaceService
from services.vlan_service import VlanService
from services.routing_service import RoutingService
from network.routing_table import RouteType
from network.subnet import netmask_to_cidr
from devices.mac_generator import MacAddressGenerator


class ShowCommands:
    """Handles all 'show' diagnostic inspection commands."""

    @classmethod
    def register_commands(cls, registry: CommandRegistry) -> None:
        exec_modes = {CLIMode.USER_EXEC, CLIMode.PRIVILEGED_EXEC}
        priv_modes = {CLIMode.PRIVILEGED_EXEC}

        # 1. show running-config
        registry.register(
            tokens=["show", "running-config"],
            handler=cls.handle_show_running_config,
            modes=priv_modes,
            help_summary="Current operating configuration",
            min_args=0,
            max_args=0
        )

        # 2. show ip interface brief
        registry.register(
            tokens=["show", "ip", "interface", "brief"],
            handler=cls.handle_show_ip_interface_brief,
            modes=exec_modes,
            help_summary="Brief summary of IP status and configuration",
            min_args=0,
            max_args=0
        )

        # 3. show interfaces
        registry.register(
            tokens=["show", "interfaces"],
            handler=cls.handle_show_interfaces,
            modes=exec_modes,
            help_summary="Interface status and configuration",
            min_args=0,
            max_args=1
        )

        # 4. show ip route
        registry.register(
            tokens=["show", "ip", "route"],
            handler=cls.handle_show_ip_route,
            modes=exec_modes,
            help_summary="IP routing table",
            min_args=0,
            max_args=0
        )

        # 5. show vlan brief
        registry.register(
            tokens=["show", "vlan", "brief"],
            handler=cls.handle_show_vlan_brief,
            modes=exec_modes,
            help_summary="VLAN status brief summary",
            min_args=0,
            max_args=0
        )

        # 6. show vlan (alias for show vlan brief)
        registry.register(
            tokens=["show", "vlan"],
            handler=cls.handle_show_vlan_brief,
            modes=exec_modes,
            help_summary="VLAN information",
            min_args=0,
            max_args=1
        )

        # 7. show mac address-table
        registry.register(
            tokens=["show", "mac", "address-table"],
            handler=cls.handle_show_mac_table,
            modes=exec_modes,
            help_summary="MAC forwarding table",
            min_args=0,
            max_args=0
        )

        # 8. show version
        registry.register(
            tokens=["show", "version"],
            handler=cls.handle_show_version,
            modes=exec_modes,
            help_summary="System hardware and software status",
            min_args=0,
            max_args=0
        )

    @staticmethod
    def handle_show_running_config(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        lines = DeviceService.get_running_config(device)
        return CommandResult.ok(output=lines)

    @staticmethod
    def handle_show_ip_interface_brief(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        lines = [
            f"{'Interface':<24} {'IP-Address':<16} {'OK?':<5} {'Method':<8} {'Status':<22} {'Protocol':<10}"
        ]
        summary = InterfaceService.get_interface_summary(device)
        for s in summary:
            c_name = s["canonical_name"]
            ip_str = s["ip_address"]
            status_str = "administratively down" if s["admin_status"] == "down" else "up"
            proto_str = "up" if s["is_operational"] else "down"
            lines.append(
                f"{c_name:<24} {ip_str:<16} {'YES':<5} {'manual':<8} {status_str:<22} {proto_str:<10}"
            )
        return CommandResult.ok(output=lines)

    @staticmethod
    def handle_show_interfaces(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        target_name = args[0] if args else None
        lines = []
        summary = InterfaceService.get_interface_summary(device)

        if target_name:
            port = InterfaceService.get_port(device, target_name)
            if not port:
                return CommandResult.error(f"% Invalid interface {target_name}")
            summary = [s for s in summary if s["port_name"] == port.port_name]

        for s in summary:
            c_name = s["canonical_name"]
            status_str = "administratively down" if s["admin_status"] == "down" else "up"
            proto_str = "up" if s["is_operational"] else "down"
            lines.append(f"{c_name} is {status_str}, line protocol is {proto_str}")

            cisco_mac = MacAddressGenerator.to_cisco_format(s["mac_address"]) if s["mac_address"] else "0000.0000.0000"
            lines.append(f"  Hardware is Gigabit Ethernet, address is {cisco_mac}")

            if s["description"]:
                lines.append(f"  Description: {s['description']}")

            if s["ip_address"] != "unassigned" and s["subnet_mask"]:
                cidr = netmask_to_cidr(s["subnet_mask"])
                lines.append(f"  Internet address is {s['ip_address']}/{cidr}")

            lines.append(f"  {s['duplex']}-duplex, {s['speed']}Mb/s, media type is 1000BaseTX")
            lines.append("  0 packets input, 0 bytes, 0 no buffer")
            lines.append("  0 packets output, 0 bytes, 0 underruns")
            lines.append("")

        return CommandResult.ok(output=lines)

    @staticmethod
    def handle_show_ip_route(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        if not hasattr(device, "routing_table"):
            return CommandResult.error("% Device does not support routing table")

        routes = RoutingService.get_routes(device)

        lines = [
            "Codes: L - local, C - connected, S - static, R - RIP, M - mobile, B - BGP",
            "       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area",
            "       * - candidate default, U - per-user static route",
            ""
        ]

        # Check for default gateway / default route
        default_routes = [r for r in routes if r.route_type == RouteType.DEFAULT]
        if default_routes:
            dr = default_routes[0]
            via = dr.next_hop if dr.next_hop else dr.interface
            lines.append(f"Gateway of last resort is {via} to network 0.0.0.0")
        else:
            lines.append("Gateway of last resort is not set")
        lines.append("")

        # Connected and static routes
        for r in routes:
            cidr = r.prefix_len
            if r.route_type == RouteType.CONNECTED:
                lines.append(f"C    {r.network}/{cidr} is directly connected, {r.interface}")
            elif r.route_type == RouteType.STATIC:
                via = f"via {r.next_hop}" if r.next_hop else f"is directly connected, {r.interface}"
                lines.append(f"S    {r.network}/{cidr} [1/0] {via}")
            elif r.route_type == RouteType.DEFAULT:
                via = f"via {r.next_hop}" if r.next_hop else f"is directly connected, {r.interface}"
                lines.append(f"S*   0.0.0.0/0 [1/0] {via}")

        return CommandResult.ok(output=lines)

    @staticmethod
    def handle_show_vlan_brief(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        if not hasattr(device, "vlan_database"):
            return CommandResult.error("% Device does not support VLAN database")

        vlan_brief = VlanService.get_vlan_brief(device)
        lines = [
            f"{'VLAN':<5} {'Name':<32} {'Status':<9} {'Ports'}",
            f"{'----':<5} {'--------------------------------':<32} {'---------':<9} {'-------------------------------'}"
        ]

        for v in vlan_brief:
            vid = v["vlan_id"]
            name = v["name"][:32]
            status = v["status"]
            ports_str = ", ".join(v["ports"]) if v["ports"] else ""
            lines.append(f"{vid:<5} {name:<32} {status:<9} {ports_str}")

        return CommandResult.ok(output=lines)

    @staticmethod
    def handle_show_mac_table(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        mac_table = getattr(device, "mac_table", None)
        if mac_table is None:
            return CommandResult.error("% Device does not maintain a MAC address table")

        lines = [
            "          Mac Address Table",
            "-------------------------------------------",
            "",
            f"{'Vlan':<7} {'Mac Address':<17} {'Type':<11} {'Ports':<10}",
            f"{'----':<7} {'-----------':<17} {'--------':<11} {'-----':<10}"
        ]

        count = 0
        for mac, entry in sorted(mac_table.items()):
            cisco_mac = MacAddressGenerator.to_cisco_format(mac) if MacAddressGenerator.validate(mac) else mac.lower()
            vlan = entry.get("vlan", 1)
            port = entry.get("port", "")
            lines.append(f"{vlan:<7} {cisco_mac:<17} {'DYNAMIC':<11} {port:<10}")
            count += 1

        lines.append(f"Total Mac Addresses for this criterion: {count}")
        return CommandResult.ok(output=lines)

    @staticmethod
    def handle_show_version(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        lines = DeviceService.get_version_info(device)
        return CommandResult.ok(output=lines)

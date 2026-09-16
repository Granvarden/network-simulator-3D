"""Cisco IOS Router CLI Command Processor."""

from typing import List, Optional
from devices.router import Router
from devices.port import AdminStatus
from network.network_engine import NetworkEngine
from network.subnet import is_valid_ip, is_valid_netmask, get_network_address
from .cli_context import CLIMode, CLIContext
from .cli_parser import parse_command_tokens


class RouterCLI:
    """Executes Cisco IOS-inspired commands directly against a Router's state."""

    def __init__(self, router: Router, network_engine: Optional[NetworkEngine] = None):
        self.router: Router = router
        self.context: CLIContext = CLIContext(router.hostname)
        self.network_engine: Optional[NetworkEngine] = network_engine

    def execute(self, cmd_line: str) -> List[str]:
        """Execute a single line of input and return output lines."""
        tokens = parse_command_tokens(cmd_line)
        if not tokens:
            return []

        verb = tokens[0].lower()

        # Global navigation commands across all modes
        if verb in ("exit", "quit"):
            if not self.context.exit_mode():
                return ["% Disconnected from session"]
            return []

        if verb == "end":
            self.context.end_mode()
            return []

        # Route by current mode
        if self.context.mode == CLIMode.USER_EXEC:
            return self._exec_user(tokens)
        elif self.context.mode == CLIMode.PRIVILEGED_EXEC:
            return self._exec_priv(tokens)
        elif self.context.mode == CLIMode.GLOBAL_CONFIG:
            return self._exec_config(tokens)
        elif self.context.mode == CLIMode.INTERFACE_CONFIG:
            return self._exec_config_if(tokens)

        return ["% Invalid input detected"]

    def _exec_user(self, tokens: List[str]) -> List[str]:
        verb = tokens[0].lower()
        if verb in ("enable", "en"):
            self.context.mode = CLIMode.PRIVILEGED_EXEC
            return []
        elif verb in ("show", "sh"):
            return self._handle_show(tokens[1:])
        elif verb == "ping":
            return self._handle_ping(tokens[1:])
        elif verb == "help" or verb == "?":
            return [
                "Exec commands:",
                "  enable             Turn on privileged commands",
                "  show <param>       Show running system information",
                "  ping <ip>          Send ICMP echo packets to destination",
                "  exit               Exit from the EXEC"
            ]
        return [f"% Invalid input detected at '{tokens[0]}'"]

    def _exec_priv(self, tokens: List[str]) -> List[str]:
        verb = tokens[0].lower()
        if verb in ("disable", "dis"):
            self.context.mode = CLIMode.USER_EXEC
            return []
        elif verb in ("configure", "conf"):
            if len(tokens) > 1 and tokens[1].lower() in ("terminal", "t"):
                self.context.mode = CLIMode.GLOBAL_CONFIG
                return ["Enter configuration commands, one per line.  End with CNTL/Z."]
            return ["% Incomplete command. Use 'configure terminal'"]
        elif verb in ("show", "sh"):
            return self._handle_show(tokens[1:])
        elif verb == "ping":
            return self._handle_ping(tokens[1:])
        return [f"% Invalid input detected at '{tokens[0]}'"]

    def _exec_config(self, tokens: List[str]) -> List[str]:
        verb = tokens[0].lower()
        if verb in ("hostname", "host"):
            if len(tokens) > 1:
                new_name = tokens[1]
                self.router.set_hostname(new_name)
                return []
            return ["% Incomplete command: hostname <name>"]

        elif verb in ("interface", "int"):
            if len(tokens) > 1:
                if_name = tokens[1]
                port = self.router.get_port(if_name)
                if port:
                    self.context.mode = CLIMode.INTERFACE_CONFIG
                    self.context.active_interface = port.port_name
                    return []
                return [f"% Invalid interface {if_name}"]
            return ["% Incomplete command: interface <name>"]

        elif verb == "ip" and len(tokens) >= 5 and tokens[1].lower() == "route":
            # ip route <dest> <mask> <next_hop>
            dest_net, mask, next_hop = tokens[2], tokens[3], tokens[4]
            if not is_valid_ip(dest_net) or not is_valid_netmask(mask) or not is_valid_ip(next_hop):
                return ["% Invalid route parameters"]
            self.router.add_static_route(dest_net, mask, next_hop)
            return []

        elif verb == "no" and len(tokens) >= 6 and tokens[1].lower() == "ip" and tokens[2].lower() == "route":
            dest_net, mask, next_hop = tokens[3], tokens[4], tokens[5]
            if self.router.remove_static_route(dest_net, mask, next_hop):
                return []
            return ["% Route not found in table"]

        elif verb in ("do",):
            # Cisco 'do' prefix executes EXEC commands in config mode
            if len(tokens) > 1:
                if tokens[1].lower() in ("show", "sh"):
                    return self._handle_show(tokens[2:])
                elif tokens[1].lower() == "ping":
                    return self._handle_ping(tokens[2:])
            return ["% Invalid do command"]

        return [f"% Invalid input detected at '{tokens[0]}'"]

    def _exec_config_if(self, tokens: List[str]) -> List[str]:
        port = self.router.get_port(self.context.active_interface or "")
        if not port:
            return ["% No interface selected"]

        verb = tokens[0].lower()

        if verb == "ip" and len(tokens) >= 4 and tokens[1].lower() == "address":
            ip, mask = tokens[2], tokens[3]
            if not is_valid_ip(ip):
                return [f"% Invalid IP address: {ip}"]
            if not is_valid_netmask(mask):
                return [f"% Invalid subnet mask: {mask}"]
            port.ip_address = ip
            port.subnet_mask = mask
            return []

        elif verb == "shutdown" or verb == "shut":
            port.set_admin_status(AdminStatus.DOWN)
            return [f"% Interface {port.port_name}, changed state to administratively down"]

        elif verb == "no" and len(tokens) > 1 and tokens[1].lower() in ("shutdown", "shut"):
            port.set_admin_status(AdminStatus.UP)
            return [
                f"% Interface {port.port_name}, changed state to up",
                f"% LINEPROTO-5-UPDOWN: Line protocol on Interface {port.port_name}, changed state to {'up' if port.is_operational else 'down'}"
            ]

        elif verb in ("description", "desc"):
            port.description = " ".join(tokens[1:])
            return []

        elif verb == "do" and len(tokens) > 1:
            if tokens[1].lower() in ("show", "sh"):
                return self._handle_show(tokens[2:])

        return [f"% Invalid input detected at '{tokens[0]}'"]

    def _handle_show(self, args: List[str]) -> List[str]:
        if not args:
            return ["% Incomplete show command"]
        sub = args[0].lower()

        if sub in ("version", "ver"):
            return [
                f"Cisco IOS Software, Simulator 15.2",
                f"Router uptime is 1 hour, 24 minutes",
                f"System image file is 'flash:c2900-universalk9-mz.SPA.152-4.M4.bin'",
                f"Processor ID {self.router.device_id.upper()}",
                f"2 Gigabit Ethernet interfaces",
                f"Configuration register is 0x2102"
            ]

        elif sub in ("running-config", "run"):
            lines = [
                f"! Running Configuration for {self.router.hostname}",
                f"version 15.2",
                f"hostname {self.router.hostname}",
                f"!"
            ]
            for p in self.router.ports.values():
                lines.append(f"interface {p.port_name}")
                if p.description:
                    lines.append(f" description {p.description}")
                if p.ip_address and p.subnet_mask:
                    lines.append(f" ip address {p.ip_address} {p.subnet_mask}")
                lines.append(" shutdown" if p.admin_status == AdminStatus.DOWN else " no shutdown")
                lines.append("!")
            for net, mask, gw in self.router.static_routes:
                lines.append(f"ip route {net} {mask} {gw}")
            lines.append("end")
            return lines

        elif sub == "interfaces" or sub == "int":
            lines = []
            for p in self.router.ports.values():
                lines.append(f"{p.port_name} is {p.admin_status.value}, line protocol is {p.link_status.value}")
                lines.append(f"  Hardware is {p.port_type.value}, address is {p.mac_address}")
                if p.ip_address:
                    lines.append(f"  Internet address is {p.ip_address}/{p.subnet_mask}")
                lines.append(f"  MTU 1500 bytes, BW {p.speed*1000} Kbit/sec, DLY 10 usec")
            return lines

        elif sub == "ip":
            if len(args) > 1:
                ip_sub = args[1].lower()
                if ip_sub in ("interface", "int"):
                    # show ip interface brief
                    lines = [
                        f"{'Interface':<18} {'IP-Address':<16} {'OK?':<5} {'Method':<8} {'Status':<22} {'Protocol':<10}",
                        "-" * 78
                    ]
                    for p in self.router.ports.values():
                        ip_str = p.ip_address or "unassigned"
                        status_str = "administratively down" if p.admin_status == AdminStatus.DOWN else "up"
                        proto_str = p.link_status.value
                        lines.append(f"{p.port_name:<18} {ip_str:<16} {'YES':<5} {'manual':<8} {status_str:<22} {proto_str:<10}")
                    return lines

                elif ip_sub == "route":
                    lines = [
                        "Codes: C - connected, S - static, R - RIP, M - mobile, B - BGP",
                        "Gateway of last resort is not set",
                        ""
                    ]
                    for p in self.router.get_operational_ports():
                        if p.ip_address and p.subnet_mask:
                            net = get_network_address(p.ip_address, p.subnet_mask)
                            lines.append(f"C    {net} is directly connected, {p.port_name}")
                    for s_net, s_mask, s_gw in self.router.static_routes:
                        lines.append(f"S    {s_net} [{1}/0] via {s_gw}")
                    return lines

        return [f"% Invalid show command: '{' '.join(args)}'"]

    def _handle_ping(self, args: List[str]) -> List[str]:
        if not args:
            return ["% Incomplete ping command: ping <ip>"]
        dest = args[0]
        if not self.network_engine:
            return ["% Network engine not available"]
        res = self.network_engine.ping(self.router, dest, count=4)
        return res.output_lines

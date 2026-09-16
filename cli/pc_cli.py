"""PC Command Prompt CLI Processor."""

from typing import List, Optional
from devices.pc import PC
from network.network_engine import NetworkEngine
from network.subnet import is_valid_ip, is_valid_netmask
from .cli_parser import parse_command_tokens


class PCCLI:
    """Simulates Windows / Linux terminal on PC workstations."""

    def __init__(self, pc: PC, network_engine: Optional[NetworkEngine] = None):
        self.pc: PC = pc
        self.network_engine: Optional[NetworkEngine] = network_engine

    def get_prompt(self) -> str:
        return f"C:\\Users\\Engineer>"

    def execute(self, cmd_line: str) -> List[str]:
        tokens = parse_command_tokens(cmd_line)
        if not tokens:
            return []

        cmd = tokens[0].lower()

        if cmd == "ipconfig":
            return self._handle_ipconfig(tokens[1:])
        elif cmd == "ping":
            return self._handle_ping(tokens[1:])
        elif cmd == "arp":
            return self._handle_arp(tokens[1:])
        elif cmd == "help":
            return [
                "Available PC Commands:",
                "  ipconfig                         Display basic network configuration",
                "  ipconfig /all                    Display full network details (MAC, Gateway)",
                "  ipconfig /set <ip> <mask> [gw]   Configure IP, subnet mask, and default gateway",
                "  ping <destination_ip>            Send ICMP echo requests to target",
                "  arp -a                           Display ARP cache table",
                "  exit                             Close command prompt"
            ]
        elif cmd in ("exit", "quit"):
            return ["% Exiting PC Command Prompt"]

        return [f"'{tokens[0]}' is not recognized as an internal or external command, operable program or batch file."]

    def _handle_ipconfig(self, args: List[str]) -> List[str]:
        if args and args[0].lower() == "/set":
            # ipconfig /set <ip> <mask> [gw]
            if len(args) < 3:
                return ["Usage: ipconfig /set <ip_address> <subnet_mask> [default_gateway]"]
            ip = args[1]
            mask = args[2]
            gw = args[3] if len(args) > 3 else None

            if not is_valid_ip(ip):
                return [f"Error: Invalid IP address '{ip}'"]
            if not is_valid_netmask(mask):
                return [f"Error: Invalid subnet mask '{mask}'"]
            if gw and not is_valid_ip(gw):
                return [f"Error: Invalid default gateway '{gw}'"]

            self.pc.set_ip_config(ip, mask, gw)
            return [
                "IP Configuration updated successfully:",
                f"   IPv4 Address. . . . . . . . . . . : {ip}",
                f"   Subnet Mask . . . . . . . . . . . : {mask}",
                f"   Default Gateway . . . . . . . . . : {gw or 'None'}"
            ]

        is_all = any(a.lower() in ("/all", "-a") for a in args)
        p = self.pc.eth0
        lines = [
            "Windows IP Configuration",
            "",
            "Ethernet adapter Ethernet0:",
            f"   Connection-specific DNS Suffix  . : localdomain",
            f"   Link-local IPv6 Address . . . . . : fe80::9c2a:4e51:2b1f%12"
        ]
        if is_all:
            lines.append(f"   Physical Address. . . . . . . . . : {p.mac_address}")
            lines.append(f"   DHCP Enabled. . . . . . . . . . . : No")
            lines.append(f"   Autoconfiguration Enabled . . . . : Yes")

        ip_str = p.ip_address or "0.0.0.0 (Unconfigured)"
        mask_str = p.subnet_mask or "0.0.0.0"
        gw_str = self.pc.default_gateway or "0.0.0.0"

        lines.append(f"   IPv4 Address. . . . . . . . . . . : {ip_str}")
        lines.append(f"   Subnet Mask . . . . . . . . . . . : {mask_str}")
        lines.append(f"   Default Gateway . . . . . . . . . : {gw_str}")
        return lines

    def _handle_ping(self, args: List[str]) -> List[str]:
        if not args:
            return ["Usage: ping [-t] [-n count] target_name"]
        dest = args[0]
        if not self.network_engine:
            return ["Network engine is offline."]
        res = self.network_engine.ping(self.pc, dest, count=4)
        return res.output_lines

    def _handle_arp(self, args: List[str]) -> List[str]:
        lines = [
            f"Interface: {self.pc.eth0.ip_address or '0.0.0.0'} --- 0xb",
            f"{'Internet Address':<18} {'Physical Address':<18} {'Type':<10}",
            "-" * 46
        ]
        if self.pc.default_gateway:
            lines.append(f"{self.pc.default_gateway:<18} {'00-11-22-33-44-55':<18} {'dynamic':<10}")
        lines.append(f"{'224.0.0.22':<18} {'01-00-5e-00-00-16':<18} {'static':<10}")
        lines.append(f"{'255.255.255.255':<18} {'ff-ff-ff-ff-ff-ff':<18} {'static':<10}")
        return lines

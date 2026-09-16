"""Cisco IOS Switch CLI Command Processor."""

from typing import List, Optional
from devices.switch import Switch
from devices.port import AdminStatus
from network.network_engine import NetworkEngine
from .cli_context import CLIMode, CLIContext
from .cli_parser import parse_command_tokens


class SwitchCLI:
    """Executes Cisco IOS-inspired commands directly against a Switch's state."""

    def __init__(self, switch: Switch, network_engine: Optional[NetworkEngine] = None):
        self.switch: Switch = switch
        self.context: CLIContext = CLIContext(switch.hostname)
        self.network_engine: Optional[NetworkEngine] = network_engine

    def execute(self, cmd_line: str) -> List[str]:
        tokens = parse_command_tokens(cmd_line)
        if not tokens:
            return []

        verb = tokens[0].lower()

        if verb in ("exit", "quit"):
            if not self.context.exit_mode():
                return ["% Disconnected from session"]
            return []

        if verb == "end":
            self.context.end_mode()
            return []

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
            return ["% Incomplete command: configure terminal"]
        elif verb in ("show", "sh"):
            return self._handle_show(tokens[1:])
        elif verb in ("clear",):
            if len(tokens) > 1 and tokens[1].lower() in ("mac", "mac-address-table"):
                self.switch.clear_mac_table()
                return ["% MAC address table cleared"]
        return [f"% Invalid input detected at '{tokens[0]}'"]

    def _exec_config(self, tokens: List[str]) -> List[str]:
        verb = tokens[0].lower()
        if verb in ("hostname", "host"):
            if len(tokens) > 1:
                self.switch.set_hostname(tokens[1])
                return []
            return ["% Incomplete command: hostname <name>"]

        elif verb in ("interface", "int"):
            if len(tokens) > 1:
                if_name = tokens[1]
                port = self.switch.get_port(if_name)
                if port:
                    self.context.mode = CLIMode.INTERFACE_CONFIG
                    self.context.active_interface = port.port_name
                    return []
                return [f"% Invalid interface {if_name}"]
            return ["% Incomplete command: interface <name>"]

        elif verb in ("do",):
            if len(tokens) > 1 and tokens[1].lower() in ("show", "sh"):
                return self._handle_show(tokens[2:])

        return [f"% Invalid input detected at '{tokens[0]}'"]

    def _exec_config_if(self, tokens: List[str]) -> List[str]:
        port = self.switch.get_port(self.context.active_interface or "")
        if not port:
            return ["% No interface selected"]

        verb = tokens[0].lower()

        if verb in ("shutdown", "shut"):
            port.set_admin_status(AdminStatus.DOWN)
            return [f"% Interface {port.port_name}, changed state to administratively down"]

        elif verb == "no" and len(tokens) > 1 and tokens[1].lower() in ("shutdown", "shut"):
            port.set_admin_status(AdminStatus.UP)
            return [f"% Interface {port.port_name}, changed state to up"]

        elif verb == "switchport":
            if len(tokens) >= 4 and tokens[1].lower() == "access" and tokens[2].lower() == "vlan":
                try:
                    vlan_id = int(tokens[3])
                    port.vlan = vlan_id
                    return []
                except ValueError:
                    return ["% Invalid VLAN ID"]
            return ["% Incomplete switchport command"]

        elif verb == "description" or verb == "desc":
            port.description = " ".join(tokens[1:])
            return []

        elif verb == "do" and len(tokens) > 1 and tokens[1].lower() in ("show", "sh"):
            return self._handle_show(tokens[2:])

        return [f"% Invalid input detected at '{tokens[0]}'"]

    def _handle_show(self, args: List[str]) -> List[str]:
        if not args:
            return ["% Incomplete show command"]
        sub = args[0].lower()

        if sub in ("version", "ver"):
            return [
                "Cisco IOS Software, C2960 Software (C2960-LANBASEK9-M), Version 15.0(2)SE4",
                f"Switch uptime is 2 hours, 10 minutes",
                f"Model: WS-C2960-24TT-L",
                f"Base Ethernet MAC Address: {self.switch.ports['Gi0/1'].mac_address[:8]}XX",
                f"24 Gigabit Ethernet interfaces"
            ]

        elif sub in ("mac", "mac-address-table") or (sub == "mac" and len(args) > 1 and "address" in args[1].lower()):
            lines = [
                f"{'Vlan':<8} {'Mac Address':<20} {'Type':<10} {'Ports':<10}",
                "-" * 48
            ]
            if not self.switch.mac_table:
                lines.append("  (No dynamic MAC entries learned yet)")
            else:
                for mac, info in self.switch.mac_table.items():
                    lines.append(f"{info['vlan']:<8} {mac:<20} {'DYNAMIC':<10} {info['port']:<10}")
            return lines

        elif sub in ("vlan", "vlans"):
            lines = [
                f"{'VLAN':<6} {'Name':<18} {'Status':<10} {'Ports'}",
                "-" * 60
            ]
            # Group ports by vlan
            vlan_ports = {}
            for p in self.switch.ports.values():
                vlan_ports.setdefault(p.vlan, []).append(p.port_name)

            for vlan_id, vlan_name in self.switch.vlans.items():
                p_list = ", ".join(vlan_ports.get(vlan_id, []))
                lines.append(f"{vlan_id:<6} {vlan_name:<18} {'active':<10} {p_list}")
            return lines

        elif sub in ("interfaces", "int"):
            lines = [
                f"{'Port':<10} {'Name':<14} {'Status':<14} {'Vlan':<6} {'Duplex':<8} {'Speed':<8} {'Type'}",
                "-" * 72
            ]
            for p in self.switch.ports.values():
                status_str = "disabled" if p.admin_status == AdminStatus.DOWN else ("connected" if p.is_operational else "notconnect")
                lines.append(f"{p.port_name:<10} {p.description[:12]:<14} {status_str:<14} {p.vlan:<6} {p.duplex:<8} {p.speed:<8} 1000BaseTX")
            return lines

        elif sub in ("running-config", "run"):
            lines = [
                f"! Running Configuration for {self.switch.hostname}",
                f"version 15.0",
                f"hostname {self.switch.hostname}",
                "!"
            ]
            for p in self.switch.ports.values():
                lines.append(f"interface {p.port_name}")
                if p.vlan != 1:
                    lines.append(f" switchport access vlan {p.vlan}")
                if p.admin_status == AdminStatus.DOWN:
                    lines.append(" shutdown")
                lines.append("!")
            lines.append("end")
            return lines

        return [f"% Invalid show command: '{' '.join(args)}'"]

"""Windows Host Command Prompt CLI commands for PC devices."""

from typing import Any, List
from ..prompts.mode import CLIMode
from ..command_result import CommandResult
from ..command_registry import CommandRegistry
from ..cli_context import CLIContext
from network.subnet import is_valid_ip, is_valid_netmask
from devices.mac_generator import MacAddressGenerator


class PCCommands:
    """Handles PC command prompt utilities (ipconfig, ping, arp, cls)."""

    @classmethod
    def register_commands(cls, registry: CommandRegistry) -> None:
        pc_mode = {CLIMode.PC_PROMPT}

        # 1. ipconfig
        registry.register(
            tokens=["ipconfig"],
            handler=cls.handle_ipconfig,
            modes=pc_mode,
            help_summary="Display or configure network IP settings",
            min_args=0,
            max_args=4
        )

        # 2. netsh
        registry.register(
            tokens=["netsh"],
            handler=cls.handle_netsh,
            modes=pc_mode,
            help_summary="Configure network interfaces and configuration",
            min_args=1,
            max_args=None
        )

        # 3. ping <ip>
        registry.register(
            tokens=["ping"],
            handler=cls.handle_ping,
            modes=pc_mode,
            help_summary="Send ICMP echo packets to destination",
            min_args=1,
            max_args=1
        )

        # 4. arp -a
        registry.register(
            tokens=["arp"],
            handler=cls.handle_arp,
            modes=pc_mode,
            help_summary="Displays current ARP entries",
            min_args=0,
            max_args=1
        )

        # 5. cls
        registry.register(
            tokens=["cls"],
            handler=cls.handle_cls,
            modes=pc_mode,
            help_summary="Clear the terminal screen",
            min_args=0,
            max_args=0
        )

        # 6. help
        registry.register(
            tokens=["help"],
            handler=cls.handle_help,
            modes=pc_mode,
            help_summary="Provides Help information for Windows commands",
            min_args=0,
            max_args=0
        )

        # 7. shutdown / no shutdown convenience
        registry.register(
            tokens=["shutdown"],
            handler=cls.handle_shutdown,
            modes=pc_mode,
            help_summary="Shut down eth0",
            min_args=0,
            max_args=0
        )
        registry.register(
            tokens=["no", "shutdown"],
            handler=cls.handle_no_shutdown,
            modes=pc_mode,
            help_summary="Enable eth0",
            min_args=0,
            max_args=0
        )

    @staticmethod
    def handle_ipconfig(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        from devices.port import AdminStatus

        if args and args[0].lower() in ("/disable", "/down", "-d"):
            eth0 = getattr(device, "eth0", None)
            if eth0:
                eth0.set_admin_status(AdminStatus.DOWN)
            return CommandResult.ok(output=["Interface 'Ethernet0' administratively disabled."])

        if args and args[0].lower() in ("/enable", "/up", "-e"):
            eth0 = getattr(device, "eth0", None)
            if eth0:
                eth0.set_admin_status(AdminStatus.UP)
            return CommandResult.ok(output=["Interface 'Ethernet0' administratively enabled."])
        if args and args[0].lower() == "/set":
            if len(args) < 3:
                return CommandResult.error("Usage: ipconfig /set <ip> <mask> [gateway]")
            ip, mask = args[1], args[2]
            gw = args[3] if len(args) >= 4 else None

            if not is_valid_ip(ip):
                return CommandResult.error(f"Invalid IP address: {ip}")
            if not is_valid_netmask(mask):
                return CommandResult.error(f"Invalid subnet mask: {mask}")
            if gw and not is_valid_ip(gw):
                return CommandResult.error(f"Invalid default gateway: {gw}")

            device.set_ip_config(ip, mask, gw)
            # Sync connected routes if applicable
            if hasattr(device, "sync_connected_routes"):
                device.sync_connected_routes()

            return CommandResult.ok(output=[
                f"IP configuration updated successfully for {device.hostname}:",
                f"   IPv4 Address. . . . . . . . . . . : {ip}",
                f"   Subnet Mask . . . . . . . . . . . : {mask}",
                f"   Default Gateway . . . . . . . . . : {gw or 'None'}"
            ])

        is_all = bool(args and args[0].lower() in ("/all", "-all"))
        lines = [
            "Windows IP Configuration",
            ""
        ]
        if is_all:
            lines.extend([
                f"   Host Name . . . . . . . . . . . . : {device.hostname}",
                f"   Primary Dns Suffix  . . . . . . . : ",
                f"   Node Type . . . . . . . . . . . . : Hybrid",
                f"   IP Routing Enabled. . . . . . . . : No",
                ""
            ])

        lines.extend([
            "Ethernet adapter Ethernet0:",
            ""
        ])

        eth0 = getattr(device, "eth0", None)
        mac = eth0.mac_address if eth0 else "00:00:00:00:00:00"
        ip = eth0.ip_address if eth0 and eth0.ip_address else "0.0.0.0"
        mask = eth0.subnet_mask if eth0 and eth0.subnet_mask else "0.0.0.0"
        gw = getattr(device, "default_gateway", None) or ""

        if is_all:
            formatted_mac = mac.replace(":", "-").upper()
            lines.extend([
                f"   Description . . . . . . . . . . . : Intel(R) 82574L Gigabit Network Connection",
                f"   Physical Address. . . . . . . . . : {formatted_mac}",
                f"   DHCP Enabled. . . . . . . . . . . : No",
                f"   Autoconfiguration Enabled . . . . : Yes"
            ])

        lines.extend([
            f"   IPv4 Address. . . . . . . . . . . : {ip}",
            f"   Subnet Mask . . . . . . . . . . . : {mask}",
            f"   Default Gateway . . . . . . . . . : {gw}"
        ])
        return CommandResult.ok(output=lines)

    @staticmethod
    def handle_ping(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        dest_ip = args[0]
        if not is_valid_ip(dest_ip):
            return CommandResult.error(f"Ping request could not find host {dest_ip}. Please check the name and try again.")

        network_engine = getattr(device, "network_engine", None)
        if network_engine is None and hasattr(context, "network_engine"):
            network_engine = getattr(context, "network_engine")

        if not network_engine:
            return CommandResult.error("General failure: Network Engine unavailable.")

        res = network_engine.ping(device, dest_ip, count=4)
        return CommandResult.ok(output=res.output_lines)

    @staticmethod
    def handle_arp(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        eth0 = getattr(device, "eth0", None)
        my_ip = eth0.ip_address if eth0 and eth0.ip_address else "127.0.0.1"

        lines = [
            f"Interface: {my_ip} --- 0x2",
            f"  {'Internet Address':<18} {'Physical Address':<19} {'Type'}"
        ]
        # Include gateway if known
        gw = getattr(device, "default_gateway", None)
        if gw:
            lines.append(f"  {gw:<18} {'02-00-00-01-00-00':<19} {'dynamic'}")
        return CommandResult.ok(output=lines)

    @staticmethod
    def handle_cls(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        return CommandResult(clear_screen=True)

    @staticmethod
    def handle_help(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        return CommandResult.ok(output=[
            "For more information on a specific command, type HELP command-name",
            "ARP        Displays and modifies the IP-to-Physical address translation tables.",
            "CLS        Clears the screen.",
            "EXIT       Quits the CMD.EXE program (closes terminal session).",
            "HELP       Provides Help information for Windows commands.",
            "IPCONFIG   Displays all current TCP/IP network configuration values.",
            "NETSH      Configures network interfaces and state.",
            "PING       Verifies IP-level connectivity to another TCP/IP computer."
        ])

    @staticmethod
    def handle_netsh(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        from devices.port import AdminStatus

        arg_str = " ".join(args).lower()
        eth0 = getattr(device, "eth0", None)
        if "disable" in arg_str:
            if eth0:
                eth0.set_admin_status(AdminStatus.DOWN)
            return CommandResult.ok(output=["Interface 'eth0' administratively disabled."])
        elif "enable" in arg_str:
            if eth0:
                eth0.set_admin_status(AdminStatus.UP)
            return CommandResult.ok(output=["Interface 'eth0' administratively enabled."])
        return CommandResult.ok(output=['Usage: netsh interface set interface [name=]"eth0" [admin=]ENABLED|DISABLED'])

    @staticmethod
    def handle_shutdown(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        from devices.port import AdminStatus

        eth0 = getattr(device, "eth0", None)
        if eth0:
            eth0.set_admin_status(AdminStatus.DOWN)
        return CommandResult.ok(output=["Interface 'eth0' changed state to administratively down."])

    @staticmethod
    def handle_no_shutdown(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        from devices.port import AdminStatus

        eth0 = getattr(device, "eth0", None)
        if eth0:
            eth0.set_admin_status(AdminStatus.UP)
        return CommandResult.ok(output=["Interface 'eth0' changed state to up."])

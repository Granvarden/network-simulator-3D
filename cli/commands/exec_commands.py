"""Privileged and User EXEC operational commands (ping, clear, write memory)."""

from typing import Any, List
from ..prompts.mode import CLIMode
from ..command_result import CommandResult
from ..command_registry import CommandRegistry
from ..cli_context import CLIContext
from network.subnet import is_valid_ip


class ExecCommands:
    """Handles operational commands like ping, clear MAC table, write memory."""

    @classmethod
    def register_commands(cls, registry: CommandRegistry) -> None:
        exec_modes = {CLIMode.USER_EXEC, CLIMode.PRIVILEGED_EXEC}
        priv_modes = {CLIMode.PRIVILEGED_EXEC}

        # 1. ping <ip>
        registry.register(
            tokens=["ping"],
            handler=cls.handle_ping,
            modes=exec_modes,
            help_summary="Send ICMP echo packets to destination",
            min_args=1,
            max_args=1
        )

        # 2. clear mac address-table
        registry.register(
            tokens=["clear", "mac", "address-table"],
            handler=cls.handle_clear_mac,
            modes=priv_modes,
            help_summary="Clear dynamic MAC forwarding table",
            min_args=0,
            max_args=0
        )

        # 3. write memory / write
        registry.register(
            tokens=["write", "memory"],
            handler=cls.handle_write_memory,
            modes=priv_modes,
            help_summary="Write configuration to NVRAM",
            min_args=0,
            max_args=0
        )
        registry.register(
            tokens=["write"],
            handler=cls.handle_write_memory,
            modes=priv_modes,
            help_summary="Write configuration to NVRAM",
            min_args=0,
            max_args=0
        )

        # 4. copy running-config startup-config
        registry.register(
            tokens=["copy", "running-config", "startup-config"],
            handler=cls.handle_write_memory,
            modes=priv_modes,
            help_summary="Copy running configuration to startup configuration",
            min_args=0,
            max_args=0
        )

    @staticmethod
    def handle_ping(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        dest_ip = args[0]
        if not is_valid_ip(dest_ip):
            return CommandResult.error(f"% Invalid IP address: {dest_ip}")

        # Retrieve network engine from device or CLI session
        network_engine = getattr(device, "network_engine", None)
        if network_engine is None and hasattr(context, "network_engine"):
            network_engine = getattr(context, "network_engine")

        if not network_engine:
            return CommandResult.error("% Network Engine unavailable to perform ping")

        # Run ping simulation
        res = network_engine.ping(device, dest_ip, count=5)

        # Format output in Cisco IOS style
        symbols = []
        if res.success:
            symbols = ["!"] * res.packets_received + ["."] * (res.packets_sent - res.packets_received)
        else:
            symbols = ["."] * res.packets_sent

        cisco_output = [
            f"Type escape sequence to abort.",
            f"Sending 5, 100-byte ICMP Echos to {dest_ip}, timeout is 2 seconds:",
            "".join(symbols),
            f"Success rate is {int(100 - res.packet_loss_percent)} percent ({res.packets_received}/{res.packets_sent}), round-trip min/avg/max = {int(res.min_rtt_ms)}/{int(res.avg_rtt_ms)}/{int(res.max_rtt_ms)} ms"
        ]
        return CommandResult.ok(output=cisco_output)

    @staticmethod
    def handle_clear_mac(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        if hasattr(device, "clear_mac_table"):
            device.clear_mac_table()
            return CommandResult.ok()
        return CommandResult.error("% Device does not maintain a MAC address table")

    @staticmethod
    def handle_write_memory(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        return CommandResult.ok(output=[
            "Building configuration...",
            "[OK]"
        ])

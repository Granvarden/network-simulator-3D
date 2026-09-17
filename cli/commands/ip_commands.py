"""IP routing and gateway configuration commands."""

from typing import Any, List
from ..prompts.mode import CLIMode
from ..command_result import CommandResult
from ..command_registry import CommandRegistry
from ..cli_context import CLIContext
from services.routing_service import RoutingService
from network.subnet import is_valid_ip


class IPCommands:
    """Handles static routing and default gateway configuration."""

    @classmethod
    def register_commands(cls, registry: CommandRegistry) -> None:
        # 1. ip route <network> <netmask> <next_hop>
        registry.register(
            tokens=["ip", "route"],
            handler=cls.handle_ip_route,
            modes={CLIMode.GLOBAL_CONFIG},
            help_summary="Establish static routes",
            min_args=3,
            max_args=3
        )

        # 2. no ip route <network> <netmask> <next_hop>
        registry.register(
            tokens=["no", "ip", "route"],
            handler=cls.handle_no_ip_route,
            modes={CLIMode.GLOBAL_CONFIG},
            help_summary="Remove static routes",
            min_args=3,
            max_args=3
        )

        # 3. ip default-gateway <ip>
        registry.register(
            tokens=["ip", "default-gateway"],
            handler=cls.handle_default_gateway,
            modes={CLIMode.GLOBAL_CONFIG},
            help_summary="Specify default gateway (for this device)",
            min_args=1,
            max_args=1
        )

    @staticmethod
    def handle_ip_route(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        net, mask, next_hop = args[0], args[1], args[2]
        ok, msg = RoutingService.add_static_route(device, net, mask, next_hop)
        if not ok:
            return CommandResult.error(msg)
        return CommandResult.ok()

    @staticmethod
    def handle_no_ip_route(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        net, mask, next_hop = args[0], args[1], args[2]
        ok, msg = RoutingService.remove_static_route(device, net, mask, next_hop)
        if not ok:
            return CommandResult.error(msg)
        return CommandResult.ok()

    @staticmethod
    def handle_default_gateway(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        gw = args[0]
        if not is_valid_ip(gw):
            return CommandResult.error(f"% Invalid default gateway IP: {gw}")

        device.default_gateway = gw
        return CommandResult.ok()

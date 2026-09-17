"""VLAN database configuration commands."""

from typing import Any, List
from ..prompts.mode import CLIMode
from ..command_result import CommandResult
from ..command_registry import CommandRegistry
from ..cli_context import CLIContext
from services.vlan_service import VlanService


class VlanCommands:
    """Handles VLAN database creation, deletion, and naming commands."""

    @classmethod
    def register_commands(cls, registry: CommandRegistry) -> None:
        # 1. vlan <id>
        registry.register(
            tokens=["vlan"],
            handler=cls.handle_vlan,
            modes={CLIMode.GLOBAL_CONFIG},
            help_summary="VLAN configuration commands",
            min_args=1,
            max_args=1
        )

        # 2. name <name>
        registry.register(
            tokens=["name"],
            handler=cls.handle_name,
            modes={CLIMode.VLAN_CONFIG},
            help_summary="Set name for VLAN",
            min_args=1,
            max_args=1
        )

        # 3. no vlan <id>
        registry.register(
            tokens=["no", "vlan"],
            handler=cls.handle_no_vlan,
            modes={CLIMode.GLOBAL_CONFIG},
            help_summary="Delete a VLAN",
            min_args=1,
            max_args=1
        )

    @staticmethod
    def handle_vlan(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        try:
            vlan_id = int(args[0])
        except ValueError:
            return CommandResult.error(f"% Invalid VLAN ID: {args[0]}")

        ok, msg = VlanService.create_vlan(device, vlan_id)
        if not ok:
            return CommandResult.error(msg)

        context.enter_mode(CLIMode.VLAN_CONFIG, vlan=vlan_id)
        return CommandResult.ok()

    @staticmethod
    def handle_name(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        if context.active_vlan is None:
            return CommandResult.error("% No VLAN selected")

        vlan_name = args[0]
        ok, msg = VlanService.set_vlan_name(device, context.active_vlan, vlan_name)
        if not ok:
            return CommandResult.error(msg)
        return CommandResult.ok()

    @staticmethod
    def handle_no_vlan(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        try:
            vlan_id = int(args[0])
        except ValueError:
            return CommandResult.error(f"% Invalid VLAN ID: {args[0]}")

        ok, msg = VlanService.delete_vlan(device, vlan_id)
        if not ok:
            return CommandResult.error(msg)
        return CommandResult.ok()

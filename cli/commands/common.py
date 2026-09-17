"""Common Cisco IOS navigation and basic system commands."""

from typing import Any, List
from ..prompts.mode import CLIMode
from ..command_result import CommandResult
from ..command_registry import CommandRegistry
from ..cli_context import CLIContext
from services.device_service import DeviceService


class CommonCommands:
    """Handles global navigation commands (enable, disable, conf t, exit, end, hostname)."""

    @classmethod
    def register_commands(cls, registry: CommandRegistry) -> None:
        # 1. enable
        registry.register(
            tokens=["enable"],
            handler=cls.handle_enable,
            modes={CLIMode.USER_EXEC},
            help_summary="Turn on privileged commands",
            min_args=0,
            max_args=1
        )

        # 2. disable
        registry.register(
            tokens=["disable"],
            handler=cls.handle_disable,
            modes={CLIMode.PRIVILEGED_EXEC},
            help_summary="Turn off privileged commands",
            min_args=0,
            max_args=0
        )

        # 3. configure terminal
        registry.register(
            tokens=["configure", "terminal"],
            handler=cls.handle_configure_terminal,
            modes={CLIMode.PRIVILEGED_EXEC},
            help_summary="Enter configuration mode",
            min_args=0,
            max_args=0
        )

        # 4. exit
        all_modes = {
            CLIMode.USER_EXEC,
            CLIMode.PRIVILEGED_EXEC,
            CLIMode.GLOBAL_CONFIG,
            CLIMode.INTERFACE_CONFIG,
            CLIMode.VLAN_CONFIG,
            CLIMode.LINE_CONFIG,
            CLIMode.ROUTER_CONFIG,
            CLIMode.PC_PROMPT
        }
        registry.register(
            tokens=["exit"],
            handler=cls.handle_exit,
            modes=all_modes,
            help_summary="Exit from the current mode",
            min_args=0,
            max_args=0
        )
        registry.register(
            tokens=["quit"],
            handler=cls.handle_exit,
            modes=all_modes,
            help_summary="Exit from the current mode",
            min_args=0,
            max_args=0
        )

        # 5. end
        config_modes = {
            CLIMode.GLOBAL_CONFIG,
            CLIMode.INTERFACE_CONFIG,
            CLIMode.VLAN_CONFIG,
            CLIMode.LINE_CONFIG,
            CLIMode.ROUTER_CONFIG
        }
        registry.register(
            tokens=["end"],
            handler=cls.handle_end,
            modes=config_modes,
            help_summary="End configuration and return to privileged EXEC",
            min_args=0,
            max_args=0
        )

        # 6. hostname <name>
        registry.register(
            tokens=["hostname"],
            handler=cls.handle_hostname,
            modes={CLIMode.GLOBAL_CONFIG},
            help_summary="Set system network name",
            min_args=1,
            max_args=1
        )

        # 7. help
        registry.register(
            tokens=["help"],
            handler=cls.handle_help,
            modes=all_modes,
            help_summary="Description of the interactive help system",
            min_args=0,
            max_args=0
        )

    @staticmethod
    def handle_help(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        lines = [
            "Help may be requested at any point in a command by entering",
            "a question mark '?'. If nothing matches, the help list will",
            "be empty and you must back up until entering a '?' shows the",
            "available options.",
            "Two styles of help are provided:",
            "1. Full help is available when you are ready to enter a",
            "   command argument (e.g. 'show ?') and will describe each possible",
            "   argument.",
            "2. Partial help is provided when an abbreviated argument is entered",
            "   and you want to know what legal arguments begin with the characters",
            "   already typed (e.g. 'sh?').",
            "",
            "Type '?' and press Enter to view all available commands in the current mode."
        ]
        return CommandResult.ok(output=lines)

    @staticmethod
    def handle_enable(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        context.mode = CLIMode.PRIVILEGED_EXEC
        return CommandResult.ok()

    @staticmethod
    def handle_disable(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        context.mode = CLIMode.USER_EXEC
        return CommandResult.ok()

    @staticmethod
    def handle_configure_terminal(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        context.enter_mode(CLIMode.GLOBAL_CONFIG)
        return CommandResult.ok(output=["Enter configuration commands, one per line.  End with CNTL/Z."])

    @staticmethod
    def handle_exit(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        if not context.exit_mode():
            return CommandResult(output=["% Disconnected from session"], exit_requested=True)
        return CommandResult.ok()

    @staticmethod
    def handle_end(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        context.end_mode()
        return CommandResult.ok()

    @staticmethod
    def handle_hostname(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        new_name = args[0]
        ok, msg = DeviceService.set_hostname(device, new_name)
        if not ok:
            return CommandResult.error(msg)
        return CommandResult.ok()

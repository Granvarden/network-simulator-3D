"""Cisco IOS Router CLI Command Processor.

Architected with Single Source of Truth, Service Layer delegation, and CommandRegistry dispatch.
"""

from typing import List, Optional
from devices.router import Router
from network.network_engine import NetworkEngine
from .prompts.mode import CLIMode
from .cli_context import CLIContext
from .command_registry import CommandRegistry
from .cli_parser import CLIParser
from .commands.common import CommonCommands
from .commands.interface_commands import InterfaceCommands
from .commands.ip_commands import IPCommands
from .commands.show_commands import ShowCommands
from .commands.exec_commands import ExecCommands


class RouterCLI:
    """Executes Cisco IOS commands on a Router via the CommandRegistry and Service Layer."""

    def __init__(self, router: Router, network_engine: Optional[NetworkEngine] = None):
        self.router: Router = router
        self.device: Router = router
        self.network_engine: Optional[NetworkEngine] = network_engine
        if network_engine is not None:
            self.router.network_engine = network_engine

        self.context: CLIContext = CLIContext(router.hostname, CLIMode.USER_EXEC)
        self.context.network_engine = network_engine

        # Initialize Command Registry and register supported commands
        self.registry: CommandRegistry = CommandRegistry()
        self._register_commands()

        # Command Parser
        self.parser: CLIParser = CLIParser(self.registry)

    def _register_commands(self) -> None:
        CommonCommands.register_commands(self.registry)
        InterfaceCommands.register_commands(self.registry)
        IPCommands.register_commands(self.registry)
        ShowCommands.register_commands(self.registry)
        ExecCommands.register_commands(self.registry)

    def execute(self, cmd_line: str) -> List[str]:
        """Execute a line of command input and return formatted output lines."""
        result = self.parser.execute(cmd_line, self.router, self.context)
        return result.output

    def get_prompt(self) -> str:
        """Return the current dynamic prompt string."""
        return self.context.get_prompt(self.router.hostname)

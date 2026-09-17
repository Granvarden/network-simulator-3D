"""PC Command Prompt CLI Processor.

Architected with CommandRegistry dispatch and PCCommands.
"""

from typing import List, Optional
from devices.pc import PC
from network.network_engine import NetworkEngine
from .prompts.mode import CLIMode
from .cli_context import CLIContext
from .command_registry import CommandRegistry
from .cli_parser import CLIParser
from .commands.common import CommonCommands
from .commands.pc_commands import PCCommands


class PCCLI:
    """Simulates Windows Command Prompt terminal on PC workstations."""

    def __init__(self, pc: PC, network_engine: Optional[NetworkEngine] = None):
        self.pc: PC = pc
        self.device: PC = pc
        self.network_engine: Optional[NetworkEngine] = network_engine
        if network_engine is not None:
            self.pc.network_engine = network_engine

        self.context: CLIContext = CLIContext(pc.hostname, CLIMode.PC_PROMPT)
        self.context.network_engine = network_engine

        # Command registry for PC commands
        self.registry: CommandRegistry = CommandRegistry()
        self._register_commands()

        self.parser: CLIParser = CLIParser(self.registry)

    def _register_commands(self) -> None:
        CommonCommands.register_commands(self.registry)
        PCCommands.register_commands(self.registry)

    def execute(self, cmd_line: str) -> List[str]:
        """Execute a line of command input and return formatted output lines."""
        result = self.parser.execute(cmd_line, self.pc, self.context)
        return result.output

    def get_prompt(self) -> str:
        """Return prompt for PC terminal."""
        return "C:\\Users\\Engineer>"

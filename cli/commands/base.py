"""Base definitions for command handlers."""

from typing import Any, Callable, List
from ..command_result import CommandResult
from ..command_registry import CommandRegistry
from ..cli_context import CLIContext


class BaseCommandHandler:
    """Base class for registering modular command handlers into a CommandRegistry."""

    @classmethod
    def register_commands(cls, registry: CommandRegistry) -> None:
        """Subclasses implement this method to register their commands into the registry."""
        raise NotImplementedError

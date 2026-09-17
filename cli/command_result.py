"""Execution result data structure for CLI commands."""

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class CommandResult:
    """Standard result returned by all CLI command handlers."""
    output: List[str] = field(default_factory=list)
    success: bool = True
    new_mode: Optional[Any] = None  # CLIMode if mode transition occurred
    exit_requested: bool = False   # True if exit/quit requested session close
    clear_screen: bool = False     # True if screen clear requested (e.g. 'cls')

    @classmethod
    def ok(cls, output: Optional[List[str]] = None, new_mode: Optional[Any] = None) -> "CommandResult":
        """Convenience constructor for successful execution."""
        return cls(output=output or [], success=True, new_mode=new_mode)

    @classmethod
    def error(cls, message: str) -> "CommandResult":
        """Convenience constructor for error output."""
        return cls(output=[message] if message else [], success=False)

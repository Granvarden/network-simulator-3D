"""Cisco IOS-inspired CLI modes and context tracking."""

from enum import Enum, auto
from typing import Optional


class CLIMode(Enum):
    USER_EXEC = auto()
    PRIVILEGED_EXEC = auto()
    GLOBAL_CONFIG = auto()
    INTERFACE_CONFIG = auto()


class CLIContext:
    """Tracks current prompt level and active sub-configuration context."""

    def __init__(self, default_hostname: str = "Device"):
        self.mode: CLIMode = CLIMode.USER_EXEC
        self.active_interface: Optional[str] = None

    def get_prompt(self, hostname: str) -> str:
        """Construct Cisco IOS prompt string based on current mode."""
        if self.mode == CLIMode.USER_EXEC:
            return f"{hostname}>"
        elif self.mode == CLIMode.PRIVILEGED_EXEC:
            return f"{hostname}#"
        elif self.mode == CLIMode.GLOBAL_CONFIG:
            return f"{hostname}(config)#"
        elif self.mode == CLIMode.INTERFACE_CONFIG:
            return f"{hostname}(config-if)#"
        return f"{hostname}>"

    def exit_mode(self) -> bool:
        """Move one level back up the hierarchy. Returns False if already at USER_EXEC."""
        if self.mode == CLIMode.INTERFACE_CONFIG:
            self.mode = CLIMode.GLOBAL_CONFIG
            self.active_interface = None
            return True
        elif self.mode == CLIMode.GLOBAL_CONFIG:
            self.mode = CLIMode.PRIVILEGED_EXEC
            return True
        elif self.mode == CLIMode.PRIVILEGED_EXEC:
            self.mode = CLIMode.USER_EXEC
            return True
        return False

    def end_mode(self) -> None:
        """Return immediately to PRIVILEGED_EXEC (like Ctrl+Z or end command in Cisco IOS)."""
        self.mode = CLIMode.PRIVILEGED_EXEC
        self.active_interface = None

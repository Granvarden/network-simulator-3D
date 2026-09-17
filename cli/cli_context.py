"""Cisco IOS-inspired CLI modes and context tracking."""

from typing import Any, Dict, List, Optional, Tuple
from .prompts.mode import CLIMode
from .prompts.prompt_builder import PromptBuilder


class CLIContext:
    """Tracks current prompt level, sub-configuration contexts, and mode navigation stack."""

    def __init__(self, default_hostname: str = "Device", initial_mode: CLIMode = CLIMode.USER_EXEC):
        self.hostname: str = default_hostname
        self.mode: CLIMode = initial_mode
        self.active_interface: Optional[str] = None
        self.active_vlan: Optional[int] = None

        # Mode history stack for hierarchical transitions: list of (mode, context_dict)
        self.mode_stack: List[Tuple[CLIMode, Dict[str, Any]]] = []

        # Terminal paging preferences
        self.terminal_width: int = 80
        self.terminal_length: int = 24

    def get_prompt(self, hostname: Optional[str] = None) -> str:
        """Construct Cisco IOS prompt string based on current mode."""
        host = hostname or self.hostname
        return PromptBuilder.build(host, self.mode, self)

    def enter_mode(self, new_mode: CLIMode, **kwargs: Any) -> None:
        """Enter a sub-mode and preserve previous context on stack."""
        current_ctx = {
            "active_interface": self.active_interface,
            "active_vlan": self.active_vlan,
        }
        self.mode_stack.append((self.mode, current_ctx))
        self.mode = new_mode

        if "interface" in kwargs:
            self.active_interface = kwargs["interface"]
        if "vlan" in kwargs:
            self.active_vlan = kwargs["vlan"]

    def exit_mode(self) -> bool:
        """Move one level back up the hierarchy. Returns False if already at base USER_EXEC / PC_PROMPT."""
        if self.mode_stack:
            prev_mode, prev_ctx = self.mode_stack.pop()
            self.mode = prev_mode
            self.active_interface = prev_ctx.get("active_interface")
            self.active_vlan = prev_ctx.get("active_vlan")
            return True

        # Fallback hierarchy transitions if stack was not populated
        if self.mode in (CLIMode.INTERFACE_CONFIG, CLIMode.VLAN_CONFIG, CLIMode.LINE_CONFIG, CLIMode.ROUTER_CONFIG):
            self.mode = CLIMode.GLOBAL_CONFIG
            self.active_interface = None
            self.active_vlan = None
            return True
        elif self.mode == CLIMode.GLOBAL_CONFIG:
            self.mode = CLIMode.PRIVILEGED_EXEC
            self.active_interface = None
            self.active_vlan = None
            return True
        elif self.mode == CLIMode.PRIVILEGED_EXEC:
            self.mode = CLIMode.USER_EXEC
            self.active_interface = None
            self.active_vlan = None
            return True

        return False

    def end_mode(self) -> None:
        """Return immediately to PRIVILEGED_EXEC (like Ctrl+Z or 'end' in Cisco IOS)."""
        self.mode_stack.clear()
        self.mode = CLIMode.PRIVILEGED_EXEC
        self.active_interface = None
        self.active_vlan = None

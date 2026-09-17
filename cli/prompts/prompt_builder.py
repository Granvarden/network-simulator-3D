"""Cisco IOS and PC Prompt Builder."""

from typing import Any
from .mode import CLIMode


class PromptBuilder:
    """Constructs dynamic prompt strings based on active mode, hostname, and context."""

    @staticmethod
    def build(hostname: str, mode: CLIMode, context: Any = None) -> str:
        r"""
        Generate prompt string.
        Examples:
            Router>
            Router#
            Router(config)#
            Router(config-if)#
            Switch(config-vlan)#
            C:\>
        """
        if mode == CLIMode.PC_PROMPT:
            return "C:\\>"

        if mode == CLIMode.USER_EXEC:
            return f"{hostname}>"
        elif mode == CLIMode.PRIVILEGED_EXEC:
            return f"{hostname}#"
        elif mode == CLIMode.GLOBAL_CONFIG:
            return f"{hostname}(config)#"
        elif mode == CLIMode.INTERFACE_CONFIG:
            return f"{hostname}(config-if)#"
        elif mode == CLIMode.VLAN_CONFIG:
            return f"{hostname}(config-vlan)#"
        elif mode == CLIMode.LINE_CONFIG:
            return f"{hostname}(config-line)#"
        elif mode == CLIMode.ROUTER_CONFIG:
            return f"{hostname}(config-router)#"

        return f"{hostname}>"

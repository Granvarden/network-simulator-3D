"""Cisco IOS and Host CLI operating modes."""

from enum import Enum, auto


class CLIMode(Enum):
    """Hierarchical CLI operating modes."""
    USER_EXEC = auto()          # Router>
    PRIVILEGED_EXEC = auto()    # Router#
    GLOBAL_CONFIG = auto()      # Router(config)#
    INTERFACE_CONFIG = auto()   # Router(config-if)#
    VLAN_CONFIG = auto()        # Switch(config-vlan)#
    LINE_CONFIG = auto()        # Router(config-line)#
    ROUTER_CONFIG = auto()      # Router(config-router)#
    PC_PROMPT = auto()          # C:\>

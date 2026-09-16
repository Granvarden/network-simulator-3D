"""Network configuration constants."""

from dataclasses import dataclass


@dataclass(frozen=True)
class NetworkConfig:
    DEFAULT_SPEED_GBPS: int = 1000
    DEFAULT_DUPLEX: str = "Full"
    DEFAULT_ROUTER_G0_IP: str = "192.168.1.1"
    DEFAULT_ROUTER_G0_MASK: str = "255.255.255.0"
    DEFAULT_ROUTER_G1_IP: str = "10.0.0.1"
    DEFAULT_ROUTER_G1_MASK: str = "255.255.255.0"
    DEFAULT_PC_IP: str = "192.168.1.10"
    DEFAULT_PC_MASK: str = "255.255.255.0"
    DEFAULT_PC_GATEWAY: str = "192.168.1.1"
    DEFAULT_VLAN_ID: int = 1
    DEFAULT_VLAN_NAME: str = "default"
    PING_COUNT: int = 4
    PING_TIMEOUT_SEC: float = 2.0

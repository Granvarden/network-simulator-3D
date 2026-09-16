"""Network port implementation with decoupled administrative and link operational states."""

from enum import Enum
from typing import Any, Optional, Tuple


class AdminStatus(Enum):
    UP = "up"
    DOWN = "down"


class LinkStatus(Enum):
    UP = "up"
    DOWN = "down"


class PortType(Enum):
    ETHERNET = "Ethernet"
    GIGABIT_ETHERNET = "GigabitEthernet"
    FAST_ETHERNET = "FastEthernet"
    CONSOLE = "Console"


class Port:
    """Represents a physical/logical network interface on a device."""

    def __init__(
        self,
        port_id: str,
        port_name: str,
        port_type: PortType = PortType.GIGABIT_ETHERNET,
        speed: int = 1000,
        duplex: str = "Full",
        vlan: int = 1,
        mac_address: str = "00:00:00:00:00:00"
    ):
        self.port_id: str = port_id
        self.port_name: str = port_name
        self.port_type: PortType = port_type
        self.speed: int = speed
        self.duplex: str = duplex
        self.vlan: int = vlan
        self.mac_address: str = mac_address

        self.ip_address: Optional[str] = None
        self.subnet_mask: Optional[str] = None
        self.description: str = ""

        self.admin_status: AdminStatus = AdminStatus.DOWN
        self.link_status: LinkStatus = LinkStatus.DOWN
        self.connected_port: Optional["Port"] = None
        self.device_ref: Optional[Any] = None  # Reference to parent Device

        # 3D relative position on the device faceplate (for cable connection rendering)
        self.local_slot_pos: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    @property
    def is_operational(self) -> bool:
        """Port is fully operational only when both Admin is UP and Physical Link is UP."""
        return self.admin_status == AdminStatus.UP and self.link_status == LinkStatus.UP

    def set_admin_status(self, status: AdminStatus) -> None:
        """Set administrative status and refresh link status."""
        self.admin_status = status
        self.update_link_status()
        if self.connected_port:
            self.connected_port.update_link_status()

    def update_link_status(self) -> None:
        """Calculate link status based on cable connection and both endpoint admin states."""
        if self.admin_status == AdminStatus.DOWN:
            self.link_status = LinkStatus.DOWN
            return

        if self.connected_port is not None and self.connected_port.admin_status == AdminStatus.UP:
            self.link_status = LinkStatus.UP
        else:
            self.link_status = LinkStatus.DOWN

    def connect_to(self, remote_port: "Port") -> bool:
        """Connect physical cable to remote port."""
        if self.connected_port is not None or remote_port.connected_port is not None:
            return False
        if self == remote_port:
            return False

        self.connected_port = remote_port
        remote_port.connected_port = self

        self.update_link_status()
        remote_port.update_link_status()
        return True

    def disconnect(self) -> None:
        """Disconnect physical cable."""
        if self.connected_port is not None:
            other = self.connected_port
            self.connected_port = None
            other.connected_port = None
            self.update_link_status()
            other.update_link_status()

    def __repr__(self) -> str:
        return f"<Port {self.port_name} Admin:{self.admin_status.value} Link:{self.link_status.value}>"

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
        mac_address: str = "00:00:00:00:00:00",
        switchport_mode: str = "access"
    ):
        from .interface_normalizer import InterfaceNormalizer

        self.port_id: str = port_id
        self.port_name: str = port_name
        self.canonical_name: str = InterfaceNormalizer.normalize(port_name)
        self.short_name: str = InterfaceNormalizer.to_short(port_name)
        self.port_type: PortType = port_type
        self.speed: int = speed
        self.duplex: str = duplex
        self.vlan: int = vlan
        self.mac_address: str = mac_address
        self.switchport_mode: str = switchport_mode  # "access" or "trunk"
        self.trunk_allowed_vlans: Optional[set[int]] = None  # None means all VLANs allowed

        self.ip_address: Optional[str] = None
        self.subnet_mask: Optional[str] = None
        self.description: str = ""

        self.admin_status: AdminStatus = AdminStatus.DOWN
        self.link_status: LinkStatus = LinkStatus.DOWN
        self.connected_port: Optional["Port"] = None
        self.device_ref: Optional[Any] = None  # Reference to parent Device

        # 3D relative position on the device faceplate (for cable connection rendering)
        self.local_slot_pos: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        self.last_activity_time: float = 0.0

    @property
    def is_operational(self) -> bool:
        """Port is fully operational only when both Admin is UP and Physical Link is UP."""
        return self.admin_status == AdminStatus.UP and self.link_status == LinkStatus.UP

    def record_activity(self) -> None:
        """Mark recent packet/traffic transmission activity."""
        import time
        self.last_activity_time = time.time()

    def set_admin_status(self, status: AdminStatus) -> None:
        """Set administrative status and refresh link status."""
        self.admin_status = status
        self.update_link_status()
        if self.connected_port:
            self.connected_port.update_link_status()

    def update_link_status(self) -> None:
        """Calculate link status based on cable connection, endpoint admin states, and device power."""
        if self.admin_status == AdminStatus.DOWN:
            self.link_status = LinkStatus.DOWN
            return

        if self.device_ref is not None and not getattr(self.device_ref, "power_state", True):
            self.link_status = LinkStatus.DOWN
            return

        if self.connected_port is not None:
            remote_dev = getattr(self.connected_port, "device_ref", None)
            remote_powered = getattr(remote_dev, "power_state", True) if remote_dev else True
            if self.connected_port.admin_status == AdminStatus.UP and remote_powered:
                self.link_status = LinkStatus.UP
                return

        self.link_status = LinkStatus.DOWN

    def get_led_colors(
        self,
        power_state: bool = True,
        time_sec: float = 0.0
    ) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        """
        Returns (link_led_color, activity_led_color) based on current port and cable state.
        - OFF: Device powered off OR no cable plugged in.
        - AMBER: Cable plugged in, but link is not operational (port shutdown, remote shutdown, or link down).
        - GREEN: Both endpoints Admin UP and cable plugged in (operational).
        - ACTIVITY: Pulsing/flickering Green during active packet transmission or idle heartbeat.
        - CONSOLE: Dedicated Sky Blue when console cable is plugged in.
        """
        from config.graphics_config import GraphicsConfig
        import math
        import time

        if not power_state:
            return GraphicsConfig.COLOR_LED_OFF, GraphicsConfig.COLOR_LED_OFF

        # No cable plugged in -> Both LEDs OFF
        if self.connected_port is None:
            return GraphicsConfig.COLOR_LED_OFF, GraphicsConfig.COLOR_LED_OFF

        # Special handling for Console port
        if self.port_type == PortType.CONSOLE:
            remote_dev = getattr(self.connected_port, "device_ref", None)
            remote_powered = getattr(remote_dev, "power_state", True) if remote_dev else True
            if remote_powered:
                return GraphicsConfig.COLOR_LED_CONSOLE, GraphicsConfig.COLOR_LED_CONSOLE
            return GraphicsConfig.COLOR_LED_OFF, GraphicsConfig.COLOR_LED_OFF

        # Cable is plugged in:
        # Check operational status
        if self.is_operational:
            link_col = GraphicsConfig.COLOR_LED_GREEN

            # Activity LED logic
            curr_t = time_sec if time_sec > 0 else time.time()
            dt_act = curr_t - self.last_activity_time

            if dt_act < 0.8:
                # Rapid 12Hz transmission flicker during active ping/data
                phase = int(curr_t * 14) % 2
                act_col = GraphicsConfig.COLOR_LED_ACTIVITY if phase == 0 else GraphicsConfig.COLOR_LED_GREEN
            else:
                # Ambient idle heartbeat shimmer (subtle pulse based on port hash)
                port_offset = sum(ord(c) for c in self.port_name) * 0.1
                pulse = math.sin((curr_t + port_offset) * 3.0)
                if pulse > 0.85:
                    act_col = GraphicsConfig.COLOR_LED_ACTIVITY
                else:
                    act_col = GraphicsConfig.COLOR_LED_GREEN

            return link_col, act_col

        # Cable connected, but NOT operational (Admin down / remote down) -> Enterprise AMBER
        return GraphicsConfig.COLOR_LED_AMBER, GraphicsConfig.COLOR_LED_OFF

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


"""Physical cable data class."""

from enum import Enum
from typing import Any, Dict, Optional, Tuple
from devices.port import Port


class CableType(Enum):
    CAT6_ETHERNET = "Cat6 Ethernet"
    CONSOLE = "Console Rollover"
    FIBER_OPTIC = "Fiber Optic"


class Cable:
    """Represents a physical patch cable connecting two ports."""

    def __init__(
        self,
        cable_id: str,
        cable_type: CableType = CableType.CAT6_ETHERNET,
        endpoint_a: Optional[Port] = None,
        endpoint_b: Optional[Port] = None,
        color: Tuple[float, float, float] = (0.2, 0.5, 0.95),  # Cat6 Royal Blue
        length: float = 3.0
    ):
        self.cable_id: str = cable_id
        self.cable_type: CableType = cable_type
        self.endpoint_a: Optional[Port] = endpoint_a
        self.endpoint_b: Optional[Port] = endpoint_b
        self.color: Tuple[float, float, float] = color
        self.length: float = length
        self.connected: bool = False

        if endpoint_a is not None and endpoint_b is not None:
            self.connect(endpoint_a, endpoint_b)

    def connect(self, port_a: Port, port_b: Port) -> bool:
        """Connect this cable between port_a and port_b."""
        if port_a == port_b:
            return False
        if port_a.connected_port is not None or port_b.connected_port is not None:
            return False

        success = port_a.connect_to(port_b)
        if success:
            self.endpoint_a = port_a
            self.endpoint_b = port_b
            self.connected = True
            return True
        return False

    def disconnect(self) -> None:
        """Disconnect both ends of the cable."""
        if self.endpoint_a:
            self.endpoint_a.disconnect()
        if self.endpoint_b:
            self.endpoint_b.disconnect()
        self.endpoint_a = None
        self.endpoint_b = None
        self.connected = False

    def get_other_endpoint(self, port: Port) -> Optional[Port]:
        if port == self.endpoint_a:
            return self.endpoint_b
        elif port == self.endpoint_b:
            return self.endpoint_a
        return None

    def serialize(self) -> Dict[str, Any]:
        return {
            "cable_id": self.cable_id,
            "cable_type": self.cable_type.value,
            "endpoint_a": self.endpoint_a.port_id if self.endpoint_a else None,
            "endpoint_b": self.endpoint_b.port_id if self.endpoint_b else None,
            "color": list(self.color),
            "length": self.length,
            "connected": self.connected,
        }

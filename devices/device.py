"""Base Device class for all physical/logical network hardware."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from .port import Port, AdminStatus, LinkStatus


class Device(ABC):
    """Abstract base class for network devices (Routers, Switches, PCs)."""

    def __init__(
        self,
        device_id: str,
        hostname: str,
        device_type: str,
        u_height: int = 1
    ):
        self.device_id: str = device_id
        self.hostname: str = hostname
        self.device_type: str = device_type
        self.u_height: int = u_height

        # Placement in world/rack
        self.rack_id: Optional[str] = None
        self.start_u: Optional[int] = None
        self.position: Tuple[float, float, float] = (0.0, 0.0, 0.0)

        # Operational status
        self.power_state: bool = True
        self.ports: Dict[str, Port] = {}

        # CLI Engine reference
        self.cli: Optional[Any] = None

        # Visual representation reference (Decoupled from logic)
        self.visual_model: Optional[Any] = None

        # General configuration dictionary
        self.config: Dict[str, Any] = {
            "hostname": hostname,
            "banner": f"Welcome to {hostname}",
        }

    def add_port(self, port: Port) -> None:
        """Add a port to this device."""
        port.device_ref = self
        self.ports[port.port_name] = port

    def get_port(self, name: str) -> Optional[Port]:
        """Look up port by name or shorthand abbreviation (e.g. g0/0, Gi0/0)."""
        # Direct match
        if name in self.ports:
            return self.ports[name]

        # Case-insensitive / abbreviated lookup
        name_lower = name.lower()
        for p_name, port in self.ports.items():
            pl = p_name.lower()
            if pl == name_lower:
                return port
            # Handle shorthand like gi0/0 -> GigabitEthernet0/0 or Gi0/0
            if pl.replace("gigabitethernet", "gi") == name_lower.replace("gigabitethernet", "gi"):
                return port
            if pl.replace("fastethernet", "fa") == name_lower.replace("fastethernet", "fa"):
                return port
        return None

    def get_operational_ports(self) -> List[Port]:
        """Return list of ports that are Admin UP and Link UP."""
        if not self.power_state:
            return []
        return [p for p in self.ports.values() if p.is_operational]

    def has_active_cables(self) -> bool:
        """Check if any port currently has a physical cable plugged in."""
        return any(p.connected_port is not None for p in self.ports.values())

    def disconnect_all_cables(self) -> None:
        """Disconnect all physical cables plugged into this device."""
        for port in self.ports.values():
            port.disconnect()

    def set_hostname(self, new_hostname: str) -> None:
        self.hostname = new_hostname
        self.config["hostname"] = new_hostname

    @abstractmethod
    def get_device_info(self) -> str:
        """Return a string summary of the device status."""
        pass

    def serialize(self) -> Dict[str, Any]:
        """Serialize device state to dictionary for JSON saving."""
        return {
            "device_id": self.device_id,
            "hostname": self.hostname,
            "device_type": self.device_type,
            "u_height": self.u_height,
            "rack_id": self.rack_id,
            "start_u": self.start_u,
            "position": list(self.position),
            "power_state": self.power_state,
            "ports": {
                p.port_name: {
                    "admin_status": p.admin_status.value,
                    "ip_address": p.ip_address,
                    "subnet_mask": p.subnet_mask,
                    "vlan": p.vlan,
                    "mac_address": p.mac_address,
                    "description": p.description,
                }
                for p in self.ports.values()
            },
            "config": self.config
        }

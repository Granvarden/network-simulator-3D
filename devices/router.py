"""Router device implementation."""

from typing import Any, Dict, List, Optional, Tuple
from .device import Device
from .port import Port, PortType, AdminStatus


class Router(Device):
    """2U Modular Router with Gigabit Ethernet interfaces and routing capabilities."""

    def __init__(self, device_id: str, hostname: str = "Router"):
        super().__init__(device_id=device_id, hostname=hostname, device_type="Router", u_height=2)

        # Static and connected routes: list of (network_ip, netmask, next_hop_ip_or_interface)
        self.static_routes: List[Tuple[str, str, str]] = []

        self._init_ports()

    def _init_ports(self) -> None:
        """Create 4 Gigabit Ethernet ports (Gi0/0 - Gi0/3) and 1 Console port."""
        face_z = 0.252

        ports_config = [
            ("Gi0/0", 0.020),
            ("Gi0/1", 0.055),
            ("Gi0/2", 0.090),
            ("Gi0/3", 0.125),
        ]
        for idx, (p_name, lx) in enumerate(ports_config):
            port = Port(
                port_id=f"{self.device_id}_gi0_{idx}",
                port_name=p_name,
                port_type=PortType.GIGABIT_ETHERNET,
                mac_address=f"00:11:22:{self.device_id[-2:] if len(self.device_id)>=2 else '01'}:00:{idx:02x}"
            )
            port.local_slot_pos = (lx, -0.015, face_z)
            self.add_port(port)

        con = Port(
            port_id=f"{self.device_id}_console",
            port_name="Console",
            port_type=PortType.CONSOLE
        )
        con.local_slot_pos = (0.165, -0.015, face_z)
        self.add_port(con)

    def add_static_route(self, dest_net: str, netmask: str, next_hop: str) -> None:
        """Add a static route to the router."""
        route = (dest_net, netmask, next_hop)
        if route not in self.static_routes:
            self.static_routes.append(route)

    def remove_static_route(self, dest_net: str, netmask: str, next_hop: str) -> bool:
        route = (dest_net, netmask, next_hop)
        if route in self.static_routes:
            self.static_routes.remove(route)
            return True
        return False

    def get_device_info(self) -> str:
        up_ports = [p.port_name for p in self.get_operational_ports()]
        return f"Router '{self.hostname}' [2U] | Operational: {', '.join(up_ports) if up_ports else 'None'}"

    def serialize(self) -> Dict[str, Any]:
        data = super().serialize()
        data["static_routes"] = self.static_routes
        return data

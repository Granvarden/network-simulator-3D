"""Router device implementation."""

from typing import Any, Dict, List, Optional, Tuple
from .device import Device
from .port import Port, PortType, AdminStatus
from .mac_generator import MacAddressGenerator
from network.routing_table import RoutingTable, RouteType


class Router(Device):
    """2U Modular Router with Gigabit Ethernet interfaces and routing capabilities."""

    def __init__(self, device_id: str, hostname: str = "Router"):
        super().__init__(device_id=device_id, hostname=hostname, device_type="Router", u_height=2)

        # Single Source of Truth for all routing decisions
        self.routing_table: RoutingTable = RoutingTable()

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
                mac_address=MacAddressGenerator.generate(self.device_id, idx)
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

    @property
    def static_routes(self) -> List[Tuple[str, str, str]]:
        """Backwards compatibility view for static routes from the routing table."""
        routes: List[Tuple[str, str, str]] = []
        for r in self.routing_table.get_routes():
            if r.route_type in (RouteType.STATIC, RouteType.DEFAULT):
                routes.append((r.network, r.netmask, r.next_hop or r.interface))
        return routes

    @static_routes.setter
    def static_routes(self, routes: List[Tuple[str, str, str]]) -> None:
        self.routing_table.clear_static_routes()
        for r in routes:
            if len(r) >= 3:
                self.add_static_route(r[0], r[1], r[2])

    def add_static_route(self, dest_net: str, netmask: str, next_hop: str) -> None:
        """Add a static route to the routing table."""
        # Check if next_hop looks like an interface or an IP
        from .interface_normalizer import InterfaceNormalizer
        if InterfaceNormalizer.is_valid_interface_syntax(next_hop):
            self.routing_table.add_static_route(
                network=dest_net,
                netmask=netmask,
                next_hop=None,
                interface=InterfaceNormalizer.normalize(next_hop)
            )
        else:
            self.routing_table.add_static_route(
                network=dest_net,
                netmask=netmask,
                next_hop=next_hop,
                interface=""
            )

    def remove_static_route(self, dest_net: str, netmask: str, next_hop: str) -> bool:
        """Remove a static route from the routing table."""
        return self.routing_table.remove_static_route(dest_net, netmask, next_hop=next_hop)

    def sync_connected_routes(self) -> None:
        """Sync directly connected routes with current operational interfaces."""
        self.routing_table.clear_connected_routes()
        for port in self.ports.values():
            if port.is_operational and port.ip_address and port.subnet_mask:
                self.routing_table.add_connected_route(
                    network=port.ip_address,
                    netmask=port.subnet_mask,
                    interface=port.canonical_name
                )

    def get_device_info(self) -> str:
        up_ports = [p.port_name for p in self.get_operational_ports()]
        return f"Router '{self.hostname}' [2U] | Operational: {', '.join(up_ports) if up_ports else 'None'}"

    def serialize(self) -> Dict[str, Any]:
        data = super().serialize()
        data["static_routes"] = self.static_routes
        data["routing_table"] = self.routing_table.serialize()
        return data

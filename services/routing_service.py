"""Routing Service Layer.

Provides business logic for configuring and inspecting routing tables on Layer 3 devices.
"""

from typing import Any, List, Optional, Tuple
from network.subnet import is_valid_ip, is_valid_netmask, get_network_address
from network.routing_table import RouteEntry, RoutingTable, RouteType
from devices.interface_normalizer import InterfaceNormalizer


class RoutingService:
    """Service managing static routing and route queries for Layer 3 devices."""

    @classmethod
    def add_static_route(
        cls, router: Any, network: str, netmask: str, next_hop: str
    ) -> Tuple[bool, str]:
        """
        Configure a static or default route on a router.
        
        Args:
            router: Router device instance
            network: Target IP network or 0.0.0.0
            netmask: Subnet mask or 0.0.0.0
            next_hop: Next-hop IPv4 address OR egress interface name
        """
        if not hasattr(router, "routing_table"):
            return False, "% Device does not support routing"

        # Special check for default route
        is_default = (network == "0.0.0.0" and netmask == "0.0.0.0")
        if not is_default:
            if not is_valid_ip(network):
                return False, f"% Invalid destination network address: {network}"
            if not is_valid_netmask(netmask):
                return False, f"% Invalid destination subnet mask: {netmask}"
            # Verify network is indeed a network address
            expected_net = get_network_address(network, netmask)
            if network != expected_net:
                return False, f"% Inconsistent address and mask: {network}/{netmask} (expected {expected_net})"

        # Validate next-hop: can be IP or interface
        if InterfaceNormalizer.is_valid_interface_syntax(next_hop):
            port = router.get_port(next_hop)
            if not port:
                return False, f"% Invalid egress interface: {next_hop}"
            egress_name = getattr(port, "canonical_name", port.port_name)
            router.routing_table.add_static_route(
                network=network,
                netmask=netmask,
                next_hop=None,
                interface=egress_name
            )
        elif is_valid_ip(next_hop):
            router.routing_table.add_static_route(
                network=network,
                netmask=netmask,
                next_hop=next_hop,
                interface=""
            )
        else:
            return False, f"% Invalid next-hop IP or interface: {next_hop}"

        return True, ""

    @classmethod
    def remove_static_route(
        cls, router: Any, network: str, netmask: str, next_hop: str
    ) -> Tuple[bool, str]:
        """Remove an existing static route from the routing table."""
        if not hasattr(router, "routing_table"):
            return False, "% Device does not support routing"

        # Resolve next-hop interface if applicable
        target_next = next_hop
        if InterfaceNormalizer.is_valid_interface_syntax(next_hop):
            port = router.get_port(next_hop)
            if port:
                target_next = getattr(port, "canonical_name", port.port_name)

        success = router.routing_table.remove_static_route(network, netmask, next_hop=target_next)
        if not success:
            return False, "% No matching route to delete"
        return True, ""

    @classmethod
    def get_routes(cls, router: Any) -> List[RouteEntry]:
        """Return all active routes (connected and static) after refreshing connected routes."""
        if not hasattr(router, "routing_table"):
            return []
        if hasattr(router, "sync_connected_routes"):
            router.sync_connected_routes()
        return router.routing_table.get_routes()

    @classmethod
    def lookup_route(cls, router: Any, dest_ip: str) -> Optional[RouteEntry]:
        """Evaluate best route for target IP via Longest Prefix Match."""
        if not hasattr(router, "routing_table"):
            return None
        if hasattr(router, "sync_connected_routes"):
            router.sync_connected_routes()
        return router.routing_table.lookup(dest_ip)

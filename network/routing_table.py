"""Routing table implementation with Longest Prefix Match (LPM)."""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from .subnet import ip_to_int, is_valid_ip, netmask_to_cidr, get_network_address


class RouteType(Enum):
    CONNECTED = "C"
    STATIC = "S"
    DEFAULT = "S*"


@dataclass
class RouteEntry:
    network: str
    netmask: str
    next_hop: Optional[str]
    interface: str
    route_type: RouteType
    metric: int = 0

    @property
    def prefix_len(self) -> int:
        return netmask_to_cidr(self.netmask)


class RoutingTable:
    """Manages IP routes and evaluates packet next-hops via Longest Prefix Matching."""

    def __init__(self):
        self.entries: List[RouteEntry] = []

    def add_route(
        self,
        network: str,
        netmask: str,
        next_hop: Optional[str],
        interface: str,
        route_type: RouteType = RouteType.STATIC,
        metric: int = 1
    ) -> None:
        """Add or replace a route entry."""
        # Remove existing route to same network/mask if present
        self.remove_route(network, netmask)
        entry = RouteEntry(
            network=network,
            netmask=netmask,
            next_hop=next_hop,
            interface=interface,
            route_type=route_type,
            metric=metric
        )
        self.entries.append(entry)

    def remove_route(self, network: str, netmask: str) -> bool:
        for r in list(self.entries):
            if r.network == network and r.netmask == netmask:
                self.entries.remove(r)
                return True
        return False

    def lookup(self, dest_ip: str) -> Optional[RouteEntry]:
        """Perform Longest Prefix Match for dest_ip."""
        if not is_valid_ip(dest_ip):
            return None

        dest_int = ip_to_int(dest_ip)
        best_match: Optional[RouteEntry] = None
        max_prefix = -1

        for route in self.entries:
            mask_int = ip_to_int(route.netmask)
            net_int = ip_to_int(route.network)

            if (dest_int & mask_int) == net_int:
                p_len = route.prefix_len
                if p_len > max_prefix:
                    max_prefix = p_len
                    best_match = route

        return best_match

    def clear(self) -> None:
        self.entries.clear()

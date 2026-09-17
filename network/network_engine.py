"""Central Network Engine simulating Layer 2 switching, Layer 3 routing, ARP, and ICMP Ping."""

from __future__ import annotations
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple
from devices.port import Port, AdminStatus, LinkStatus
from .subnet import is_valid_ip, is_same_subnet, get_network_address
from .routing_table import RoutingTable, RouteType

if TYPE_CHECKING:
    from devices.device import Device


@dataclass
class PingResult:
    destination_ip: str
    packets_sent: int
    packets_received: int
    packet_loss_percent: float
    min_rtt_ms: float
    avg_rtt_ms: float
    max_rtt_ms: float
    output_lines: List[str]
    success: bool


class NetworkEngine:
    """Coordinates packet delivery, switching, routing, and reachability between devices."""

    def __init__(self):
        self.devices: Dict[str, Device] = {}

    def register_device(self, device: Device) -> None:
        self.devices[device.device_id] = device

    def unregister_device(self, device: Device) -> None:
        if device.device_id in self.devices:
            del self.devices[device.device_id]

    def update_links(self) -> None:
        """Synchronize operational link status for all device ports."""
        for device in self.devices.values():
            for port in device.ports.values():
                port.update_link_status()

    def find_device_by_ip(self, ip: str) -> Optional[Tuple[Device, Port]]:
        """Find the device and port that owns a specific IP address."""
        for device in self.devices.values():
            if not device.power_state:
                continue
            for port in device.ports.values():
                if port.ip_address == ip and port.is_operational:
                    return device, port
        return None

    def trace_l2_segment(self, start_port: Port) -> List[Port]:
        """Traverse through switches to discover all reachable L2 endpoints from start_port."""
        reachable_ports: List[Port] = []
        visited_switches: Set[str] = set()

        def visit(current_port: Port):
            remote = current_port.connected_port
            if not remote or not remote.is_operational:
                return

            remote_dev = remote.device_ref
            if not remote_dev or not remote_dev.power_state:
                return

            if getattr(remote_dev, "device_type", None) == "Switch":
                # Switch learns MAC of incoming traffic
                if start_port.mac_address:
                    remote_dev.learn_mac(start_port.mac_address, remote.port_name, remote.vlan)

                if remote_dev.device_id in visited_switches:
                    return
                visited_switches.add(remote_dev.device_id)

                # Flood/forward out other operational ports on same VLAN
                for sp in remote_dev.get_operational_ports():
                    if sp != remote and sp.vlan == remote.vlan:
                        visit(sp)
            else:
                # End host (Router or PC)
                if remote not in reachable_ports:
                    reachable_ports.append(remote)

        visit(start_port)
        return reachable_ports

    def ping(self, source_device: Any, dest_ip: str, count: int = 4) -> PingResult:
        """Simulate ICMP Echo Ping with realistic diagnostics and response output."""
        output: List[str] = []

        if not is_valid_ip(dest_ip):
            output.append(f"% Invalid IP address: {dest_ip}")
            return PingResult(dest_ip, 0, 0, 100.0, 0.0, 0.0, 0.0, output, False)

        output.append(f"Pinging {dest_ip} with 32 bytes of data:")

        # 1. Identify source egress port and IP
        source_port: Optional[Port] = None
        gateway_ip: Optional[str] = None

        dev_type = getattr(source_device, "device_type", None)
        if dev_type == "PC":
            source_port = getattr(source_device, "eth0", None)
            gateway_ip = getattr(source_device, "default_gateway", None)
        elif dev_type == "Router":
            # Select operational router interface matching dest_ip subnet, or interface with route
            for p in source_device.get_operational_ports():
                if p.ip_address and p.subnet_mask and is_same_subnet(p.ip_address, dest_ip, p.subnet_mask):
                    source_port = p
                    break
            if not source_port:
                # Fallback to first operational interface
                op_ports = source_device.get_operational_ports()
                if op_ports:
                    source_port = op_ports[0]

        # 2. Check source port operational status
        if not source_port or source_port.admin_status == AdminStatus.DOWN:
            for _ in range(count):
                output.append("Destination host unreachable (Interface is administratively down).")
            return PingResult(dest_ip, count, 0, 100.0, 0.0, 0.0, 0.0, output, False)

        if not source_port.is_operational:
            for _ in range(count):
                output.append("Request timed out (Physical link is down / cable disconnected).")
            return PingResult(dest_ip, count, 0, 100.0, 0.0, 0.0, 0.0, output, False)

        # 3. Check Self-Ping
        if source_port.ip_address == dest_ip:
            source_port.record_activity()
            rtts = [1.0 for _ in range(count)]
            for i in range(count):
                output.append(f"Reply from {dest_ip}: bytes=32 time<1ms TTL=128")
            return PingResult(dest_ip, count, count, 0.0, 1.0, 1.0, 1.0, output, True)

        # 4. Resolve Target IP via L2 or L3
        target_info = self.find_device_by_ip(dest_ip)
        if not target_info:
            for _ in range(count):
                output.append("Request timed out (Host not found or powered off).")
            return PingResult(dest_ip, count, 0, 100.0, 0.0, 0.0, 0.0, output, False)

        target_dev, target_port = target_info

        # 5. Check if in Same Subnet
        if source_port.ip_address and source_port.subnet_mask and is_same_subnet(source_port.ip_address, dest_ip, source_port.subnet_mask):
            # Direct L2 delivery
            reachable_ports = self.trace_l2_segment(source_port)
            if target_port in reachable_ports:
                # Success! Record activity on ingress and egress ports
                source_port.record_activity()
                target_port.record_activity()
                if source_port.connected_port:
                    source_port.connected_port.record_activity()
                if target_port.connected_port:
                    target_port.connected_port.record_activity()

                rtts = [round(random.uniform(1.0, 3.5), 1) for _ in range(count)]
                for rtt in rtts:
                    output.append(f"Reply from {dest_ip}: bytes=32 time={rtt}ms TTL=64")
                return PingResult(
                    destination_ip=dest_ip,
                    packets_sent=count,
                    packets_received=count,
                    packet_loss_percent=0.0,
                    min_rtt_ms=min(rtts),
                    avg_rtt_ms=round(sum(rtts) / len(rtts), 1),
                    max_rtt_ms=max(rtts),
                    output_lines=output,
                    success=True
                )
            else:
                for _ in range(count):
                    output.append("Request timed out (No Layer 2 path to host).")
                return PingResult(dest_ip, count, 0, 100.0, 0.0, 0.0, 0.0, output, False)

        # 6. Different Subnet - Must route via Default Gateway
        if not gateway_ip:
            for _ in range(count):
                output.append("Destination host unreachable (No default gateway configured).")
            return PingResult(dest_ip, count, 0, 100.0, 0.0, 0.0, 0.0, output, False)

        gw_info = self.find_device_by_ip(gateway_ip)
        if not gw_info:
            for _ in range(count):
                output.append(f"Request timed out (Default gateway {gateway_ip} unreachable).")
            return PingResult(dest_ip, count, 0, 100.0, 0.0, 0.0, 0.0, output, False)

        gw_dev, gw_port = gw_info
        # Verify L2 connectivity to Gateway
        reachable_to_gw = self.trace_l2_segment(source_port)
        if gw_port not in reachable_to_gw:
            for _ in range(count):
                output.append(f"Request timed out (Cannot reach gateway {gateway_ip} at L2).")
            return PingResult(dest_ip, count, 0, 100.0, 0.0, 0.0, 0.0, output, False)

        # If gateway is a Router, check if Router can route to target
        if getattr(gw_dev, "device_type", None) == "Router":
            # Check router's own ports for destination subnet
            has_route = False
            for rp in gw_dev.get_operational_ports():
                if rp.ip_address and rp.subnet_mask and is_same_subnet(rp.ip_address, dest_ip, rp.subnet_mask):
                    # Destination is on this router interface
                    # Check L2 reachability from router interface to target
                    if target_port in self.trace_l2_segment(rp):
                        has_route = True
                        source_port.record_activity()
                        gw_port.record_activity()
                        rp.record_activity()
                        target_port.record_activity()
                        if source_port.connected_port:
                            source_port.connected_port.record_activity()
                        if target_port.connected_port:
                            target_port.connected_port.record_activity()
                        break

            # Check routing table / static routes if not directly connected
            if not has_route:
                if hasattr(gw_dev, "routing_table"):
                    route_entry = gw_dev.routing_table.lookup(dest_ip)
                    if route_entry:
                        has_route = True
                        source_port.record_activity()
                        gw_port.record_activity()
                        target_port.record_activity()
                elif hasattr(gw_dev, "static_routes"):
                    for s_net, s_mask, s_next in gw_dev.static_routes:
                        if get_network_address(dest_ip, s_mask) == s_net:
                            has_route = True
                            source_port.record_activity()
                            gw_port.record_activity()
                            target_port.record_activity()
                            break

            if has_route:
                rtts = [round(random.uniform(2.0, 5.0), 1) for _ in range(count)]
                for rtt in rtts:
                    output.append(f"Reply from {dest_ip}: bytes=32 time={rtt}ms TTL=63")
                return PingResult(
                    destination_ip=dest_ip,
                    packets_sent=count,
                    packets_received=count,
                    packet_loss_percent=0.0,
                    min_rtt_ms=min(rtts),
                    avg_rtt_ms=round(sum(rtts) / len(rtts), 1),
                    max_rtt_ms=max(rtts),
                    output_lines=output,
                    success=True
                )


        for _ in range(count):
            output.append("Destination host unreachable.")
        return PingResult(dest_ip, count, 0, 100.0, 0.0, 0.0, 0.0, output, False)

"""Device Service Layer.

Handles high-level device management, hostname validation, power states,
and dynamic running-config generation from live state.
"""

import re
from typing import Any, List, Optional, Tuple
from devices.device import Device
from devices.port import AdminStatus
from network.routing_table import RouteType


class DeviceService:
    """Service managing device-wide configuration, power states, and running-config generation."""

    HOSTNAME_REGEX = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-]{0,62}$")

    @classmethod
    def set_hostname(cls, device: Device, new_hostname: str) -> Tuple[bool, str]:
        """Validate and apply a new hostname to a device."""
        clean = new_hostname.strip()
        if not clean:
            return False, "% Hostname cannot be empty"

        if not cls.HOSTNAME_REGEX.match(clean):
            return False, f"% Invalid hostname '{clean}'. Must be alphanumeric with hyphens (1-63 chars)"

        device.set_hostname(clean)
        return True, ""

    @classmethod
    def set_power_state(cls, device: Device, power: bool) -> Tuple[bool, str]:
        """Toggle device power state and synchronize port link states."""
        device.power_state = power
        for port in device.ports.values():
            port.update_link_status()
            if port.connected_port:
                port.connected_port.update_link_status()
        return True, ""

    @classmethod
    def get_running_config(cls, device: Device) -> List[str]:
        """
        Dynamically synthesize Cisco IOS running-config from live device state.
        Never relies on stale stored configuration strings.
        """
        lines: List[str] = [
            "Building configuration...",
            "",
            "Current configuration : 1024 bytes",
            "!",
            "version 15.1",
            "no service timestamps log datetime msec",
            "no service password-encryption",
            "!",
            f"hostname {device.hostname}",
            "!",
        ]

        # Switch-specific VLAN blocks
        vlan_db = getattr(device, "vlan_database", None)
        if vlan_db is not None:
            # Custom VLANs (exclude 1 and 1002-1005)
            custom_vlans = [v for v in vlan_db.list_vlans() if v.vlan_id not in vlan_db.RESERVED_VLANS]
            for v in custom_vlans:
                lines.append(f"vlan {v.vlan_id}")
                if v.name and v.name != f"VLAN{v.vlan_id:04d}":
                    lines.append(f" name {v.name}")
                lines.append("!")

        # Interface configurations
        for port in device.ports.values():
            if getattr(port, "port_type", None) and port.port_type.value == "Console":
                continue

            c_name = getattr(port, "canonical_name", port.port_name)
            lines.append(f"interface {c_name}")

            if port.description:
                lines.append(f" description {port.description}")

            if port.ip_address and port.subnet_mask:
                lines.append(f" ip address {port.ip_address} {port.subnet_mask}")

            mode = getattr(port, "switchport_mode", None)
            if mode:
                lines.append(f" switchport mode {mode}")

            if port.vlan > 1:
                lines.append(f" switchport access vlan {port.vlan}")

            if port.admin_status == AdminStatus.DOWN:
                lines.append(" shutdown")

            lines.append("!")

        # Router-specific static routes
        routing_table = getattr(device, "routing_table", None)
        if routing_table is not None:
            static_routes = [
                r for r in routing_table.get_routes()
                if r.route_type in (RouteType.STATIC, RouteType.DEFAULT)
            ]
            for r in static_routes:
                target = r.next_hop if r.next_hop else r.interface
                lines.append(f"ip route {r.network} {r.netmask} {target}")
            if static_routes:
                lines.append("!")

        lines.extend([
            "line con 0",
            "line vty 0 4",
            " login",
            "!",
            "end"
        ])
        return lines

    @classmethod
    def get_version_info(cls, device: Device) -> List[str]:
        """Generate accurate simulator version info without false hardware claims."""
        first_mac = "02:00:00:00:00:00"
        for p in device.ports.values():
            if p.mac_address:
                first_mac = p.mac_address
                break

        return [
            "Network Simulator 3D Software, Version 1.0",
            "Technical Support: Granvarden / Network-Simulator-3D",
            f"Compiled for {device.device_type} Platform",
            "",
            f"{device.hostname} uptime is 0 hours, 12 minutes",
            f"System image: 'netsim3d-platform-1.0.bin'",
            "",
            f"Device ID: {device.device_id}",
            f"Form Factor: {device.u_height}U Rackmount Unit",
            f"Base Ethernet MAC Address: {first_mac}",
            f"Active Interfaces: {len(device.get_operational_ports())}/{len(device.ports)}",
            "",
            "Configuration register is 0x2102"
        ]

"""Interface Service Layer.

Provides business logic for configuring and querying device interfaces
without CLI handlers directly modifying port or device internal fields.
"""

from typing import Any, Dict, List, Optional, Tuple
from devices.device import Device
from devices.port import Port, AdminStatus
from devices.interface_normalizer import InterfaceNormalizer
from network.subnet import is_valid_ip, is_valid_netmask, ip_to_int, netmask_to_cidr


class InterfaceService:
    """Service handling interface administrative state, IP addressing, and switchport properties."""

    @classmethod
    def get_port(cls, device: Device, interface_name: str) -> Optional[Port]:
        """Resolve port by canonical or shorthand name."""
        if not device or not interface_name:
            return None
        return device.get_port(interface_name)

    @classmethod
    def set_admin_status(
        cls, device: Device, interface_name: str, status: AdminStatus
    ) -> Tuple[bool, str]:
        """
        Change administrative status of an interface.
        Updates physical link status and synchronizes connected routes if device is a router.
        """
        port = cls.get_port(device, interface_name)
        if not port:
            return False, f"% Invalid interface {interface_name}"

        port.set_admin_status(status)

        # Sync connected routes if router
        if hasattr(device, "sync_connected_routes"):
            device.sync_connected_routes()

        c_name = getattr(port, "canonical_name", port.port_name)
        if status == AdminStatus.DOWN:
            msg = f"% Interface {c_name}, changed state to administratively down"
        else:
            proto_state = "up" if port.is_operational else "down"
            msg = (
                f"% Interface {c_name}, changed state to up\n"
                f"% LINEPROTO-5-UPDOWN: Line protocol on Interface {c_name}, changed state to {proto_state}"
            )
        return True, msg

    @classmethod
    def set_ip_address(
        cls, device: Device, interface_name: str, ip: str, mask: str
    ) -> Tuple[bool, str]:
        """
        Assign an IPv4 address and subnet mask to an interface.
        Validates IP format, subnet mask, duplicate assignment, and network/broadcast bounds.
        """
        port = cls.get_port(device, interface_name)
        if not port:
            return False, f"% Invalid interface {interface_name}"

        if not is_valid_ip(ip):
            return False, f"% Invalid IP address: {ip}"

        if not is_valid_netmask(mask):
            return False, f"% Invalid subnet mask: {mask}"

        # Subnet / broadcast checks for host addresses (except /31 and /32)
        cidr = netmask_to_cidr(mask)
        if cidr < 31:
            ip_val = ip_to_int(ip)
            mask_val = ip_to_int(mask)
            net_val = ip_val & mask_val
            bcast_val = net_val | (~mask_val & 0xFFFFFFFF)
            if ip_val == net_val:
                return False, f"% Invalid host address: {ip} is the network address for subnet {mask}"
            if ip_val == bcast_val:
                return False, f"% Invalid host address: {ip} is the broadcast address for subnet {mask}"

        # Check for duplicate IP on other interfaces of this device
        for other_p in device.ports.values():
            if other_p != port and other_p.ip_address == ip:
                other_name = getattr(other_p, "canonical_name", other_p.port_name)
                return False, f"% IP address conflict: {ip} is already assigned to {other_name}"

        port.ip_address = ip
        port.subnet_mask = mask

        # Sync connected routes if router
        if hasattr(device, "sync_connected_routes"):
            device.sync_connected_routes()

        return True, ""

    @classmethod
    def remove_ip_address(cls, device: Device, interface_name: str) -> Tuple[bool, str]:
        """Remove IP address and subnet mask from an interface."""
        port = cls.get_port(device, interface_name)
        if not port:
            return False, f"% Invalid interface {interface_name}"

        port.ip_address = None
        port.subnet_mask = None

        if hasattr(device, "sync_connected_routes"):
            device.sync_connected_routes()

        return True, ""

    @classmethod
    def set_description(
        cls, device: Device, interface_name: str, description: str
    ) -> Tuple[bool, str]:
        """Set interface description text."""
        port = cls.get_port(device, interface_name)
        if not port:
            return False, f"% Invalid interface {interface_name}"

        port.description = description.strip()
        return True, ""

    @classmethod
    def set_switchport_mode(
        cls, device: Device, interface_name: str, mode: str
    ) -> Tuple[bool, str]:
        """Set switchport operational mode ('access' or 'trunk')."""
        port = cls.get_port(device, interface_name)
        if not port:
            return False, f"% Invalid interface {interface_name}"

        clean_mode = mode.strip().lower()
        if clean_mode not in ("access", "trunk"):
            return False, f"% Invalid switchport mode: {mode} (expected 'access' or 'trunk')"

        port.switchport_mode = clean_mode
        return True, ""

    @classmethod
    def set_switchport_access_vlan(
        cls, device: Device, interface_name: str, vlan_id: int
    ) -> Tuple[bool, str]:
        """Assign access port to a specific VLAN."""
        port = cls.get_port(device, interface_name)
        if not port:
            return False, f"% Invalid interface {interface_name}"

        if not (1 <= vlan_id <= 4094):
            return False, f"% Invalid VLAN ID {vlan_id} (valid range 1-4094)"

        # Check if VLAN exists in switch database; auto-create if needed
        vlan_db = getattr(device, "vlan_database", None)
        msg = ""
        if vlan_db is not None and not vlan_db.has_vlan(vlan_id):
            vlan_db.add_vlan(vlan_id)
            msg = f"% Access VLAN {vlan_id} does not exist. Creating VLAN {vlan_id}"

        port.vlan = vlan_id
        return True, msg

    @classmethod
    def set_switchport_trunk_allowed_vlans(
        cls, device: Device, interface_name: str, vlans: List[int]
    ) -> Tuple[bool, str]:
        """Set allowed VLANs list for a trunk port."""
        port = cls.get_port(device, interface_name)
        if not port:
            return False, f"% Invalid interface {interface_name}"

        for vid in vlans:
            if not (1 <= vid <= 4094):
                return False, f"% Invalid VLAN ID {vid} in allowed list"

        port.trunk_allowed_vlans = set(vlans)
        return True, ""

    @classmethod
    def get_interface_summary(cls, device: Device) -> List[Dict[str, Any]]:
        """Get summary status of all interfaces on a device."""
        summary = []
        for port in device.ports.values():
            c_name = getattr(port, "canonical_name", port.port_name)
            s_name = getattr(port, "short_name", port.port_name)
            summary.append({
                "port_name": port.port_name,
                "canonical_name": c_name,
                "short_name": s_name,
                "admin_status": port.admin_status.value,
                "link_status": port.link_status.value,
                "is_operational": port.is_operational,
                "ip_address": port.ip_address or "unassigned",
                "subnet_mask": port.subnet_mask or "",
                "vlan": port.vlan,
                "speed": port.speed,
                "duplex": port.duplex,
                "description": port.description,
                "mac_address": port.mac_address,
                "switchport_mode": getattr(port, "switchport_mode", "access"),
            })
        return summary

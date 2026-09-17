"""VLAN Service Layer.

Provides business logic for managing VLANs on Layer 2 switches.
"""

from typing import Any, Dict, List, Optional, Tuple
from devices.vlan_database import VLAN, VLANDatabase


class VlanService:
    """Service handling VLAN creation, deletion, naming, and port membership queries."""

    @classmethod
    def create_vlan(
        cls, switch: Any, vlan_id: int, name: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Create or configure a VLAN on a switch."""
        vlan_db: Optional[VLANDatabase] = getattr(switch, "vlan_database", None)
        if not vlan_db:
            return False, "% Switch does not support VLAN database"

        try:
            vlan = vlan_db.add_vlan(vlan_id, name)
            return True, ""
        except ValueError as e:
            return False, f"% {str(e)}"

    @classmethod
    def delete_vlan(cls, switch: Any, vlan_id: int) -> Tuple[bool, str]:
        """Delete a VLAN. Rejects deletion of reserved VLANs (1, 1002-1005)."""
        vlan_db: Optional[VLANDatabase] = getattr(switch, "vlan_database", None)
        if not vlan_db:
            return False, "% Switch does not support VLAN database"

        if vlan_id in VLANDatabase.RESERVED_VLANS:
            return False, f"% Default VLAN {vlan_id} cannot be deleted"

        if not vlan_db.has_vlan(vlan_id):
            return False, f"% VLAN {vlan_id} does not exist"

        # If any access ports were assigned to this deleted VLAN, reset them to VLAN 1
        for port in switch.ports.values():
            if port.vlan == vlan_id:
                port.vlan = 1

        vlan_db.remove_vlan(vlan_id)
        return True, ""

    @classmethod
    def set_vlan_name(cls, switch: Any, vlan_id: int, name: str) -> Tuple[bool, str]:
        """Set the name of an existing VLAN."""
        vlan_db: Optional[VLANDatabase] = getattr(switch, "vlan_database", None)
        if not vlan_db:
            return False, "% Switch does not support VLAN database"

        if vlan_id in VLANDatabase.RESERVED_VLANS:
            return False, f"% Cannot rename default VLAN {vlan_id}"

        if not vlan_db.has_vlan(vlan_id):
            return False, f"% VLAN {vlan_id} does not exist"

        vlan_db.set_vlan_name(vlan_id, name.strip())
        return True, ""

    @classmethod
    def get_vlans(cls, switch: Any) -> List[VLAN]:
        """Get list of all VLAN objects."""
        vlan_db: Optional[VLANDatabase] = getattr(switch, "vlan_database", None)
        if not vlan_db:
            return []
        return vlan_db.list_vlans()

    @classmethod
    def get_vlan_brief(cls, switch: Any) -> List[Dict[str, Any]]:
        """
        Generate structured summary for 'show vlan brief'.
        Maps each VLAN to its member ports.
        """
        vlans = cls.get_vlans(switch)
        # Group ports by access VLAN
        vlan_ports: Dict[int, List[str]] = {}
        for port in switch.ports.values():
            # Include access ports in the list
            mode = getattr(port, "switchport_mode", "access")
            if mode == "access":
                s_name = getattr(port, "short_name", port.port_name)
                vlan_ports.setdefault(port.vlan, []).append(s_name)

        brief = []
        for v in vlans:
            brief.append({
                "vlan_id": v.vlan_id,
                "name": v.name,
                "status": v.state,
                "ports": sorted(vlan_ports.get(v.vlan_id, []))
            })
        return brief

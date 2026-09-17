"""Cisco IOS VLAN Database implementation with standard IEEE 802.1Q VLAN ranges."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class VLAN:
    """Represents an 802.1Q VLAN entity."""
    vlan_id: int
    name: str
    state: str = "active"  # "active" or "suspend"


class VLANDatabase:
    """
    Central VLAN database for Layer 2 switches.
    Maintains default and user-defined VLANs with standard Cisco constraints.
    """

    # Reserved default VLANs that cannot be deleted or renamed in Cisco IOS
    RESERVED_VLANS = {
        1: "default",
        1002: "fddi-default",
        1003: "token-ring-default",
        1004: "fddinet-default",
        1005: "trnet-default",
    }

    def __init__(self):
        self._vlans: Dict[int, VLAN] = {}
        self._init_defaults()

    def _init_defaults(self) -> None:
        """Initialize standard Cisco reserved VLANs."""
        for vid, name in self.RESERVED_VLANS.items():
            self._vlans[vid] = VLAN(vlan_id=vid, name=name, state="active")

    def add_vlan(self, vlan_id: int, name: Optional[str] = None) -> VLAN:
        """
        Create or retrieve a VLAN.
        
        Args:
            vlan_id: VLAN identifier (1-4094)
            name: Optional descriptive name. Defaults to 'VLAN{vlan_id:04d}'
            
        Raises:
            ValueError: If vlan_id is outside the range 1-4094
        """
        if not (1 <= vlan_id <= 4094):
            raise ValueError(f"VLAN ID {vlan_id} out of valid range (1-4094)")

        if vlan_id in self._vlans:
            vlan = self._vlans[vlan_id]
            if name and vlan_id not in self.RESERVED_VLANS:
                vlan.name = name
            return vlan

        default_name = name or f"VLAN{vlan_id:04d}"
        vlan = VLAN(vlan_id=vlan_id, name=default_name, state="active")
        self._vlans[vlan_id] = vlan
        return vlan

    def remove_vlan(self, vlan_id: int) -> bool:
        """
        Delete a user-defined VLAN. Reserved VLANs cannot be deleted.
        
        Returns:
            True if deleted, False if protected or non-existent.
        """
        if vlan_id in self.RESERVED_VLANS:
            return False
        if vlan_id in self._vlans:
            del self._vlans[vlan_id]
            return True
        return False

    def get_vlan(self, vlan_id: int) -> Optional[VLAN]:
        """Retrieve VLAN by ID."""
        return self._vlans.get(vlan_id)

    def has_vlan(self, vlan_id: int) -> bool:
        """Check if VLAN exists."""
        return vlan_id in self._vlans

    def set_vlan_name(self, vlan_id: int, name: str) -> bool:
        """Rename a VLAN. Reserved VLANs cannot be renamed."""
        if vlan_id in self.RESERVED_VLANS:
            return False
        if vlan_id in self._vlans:
            self._vlans[vlan_id].name = name
            return True
        return False

    def list_vlans(self) -> List[VLAN]:
        """Return all VLANs sorted by VLAN ID."""
        return sorted(self._vlans.values(), key=lambda v: v.vlan_id)

    def serialize(self) -> Dict[str, Any]:
        """Serialize VLAN database."""
        return {
            str(v.vlan_id): {
                "name": v.name,
                "state": v.state
            }
            for v in self.list_vlans()
        }

    def deserialize(self, data: Dict[str, Any]) -> None:
        """Deserialize VLAN database from dictionary."""
        self._vlans.clear()
        self._init_defaults()
        for vid_str, vinfo in data.items():
            try:
                vid = int(vid_str)
                name = vinfo.get("name", f"VLAN{vid:04d}")
                state = vinfo.get("state", "active")
                if vid in self._vlans:
                    if vid not in self.RESERVED_VLANS:
                        self._vlans[vid].name = name
                    self._vlans[vid].state = state
                else:
                    self._vlans[vid] = VLAN(vlan_id=vid, name=name, state=state)
            except (ValueError, TypeError):
                continue

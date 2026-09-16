"""Switch device implementation."""

from typing import Any, Dict, List, Optional, Tuple
from .device import Device
from .port import Port, PortType, AdminStatus


class Switch(Device):
    """1U 24-Port Gigabit Ethernet Switch with dynamic MAC address table learning."""

    def __init__(self, device_id: str, hostname: str = "Switch"):
        super().__init__(device_id=device_id, hostname=hostname, device_type="Switch", u_height=1)

        # MAC Address Table: Dict of MAC -> {"port": port_name, "vlan": vlan_id}
        self.mac_table: Dict[str, Dict[str, Any]] = {}
        # VLANs database
        self.vlans: Dict[int, str] = {1: "default"}

        self._init_ports()

    def _init_ports(self) -> None:
        """Create 24 Gigabit Ethernet ports."""
        for i in range(1, 25):
            p_name = f"Gi0/{i}"
            port = Port(
                port_id=f"{self.device_id}_gi0_{i}",
                port_name=p_name,
                port_type=PortType.GIGABIT_ETHERNET,
                speed=1000,
                vlan=1,
                mac_address=f"00:22:33:{self.device_id[-2:] if len(self.device_id)>=2 else '01'}:00:{i:02x}"
            )
            # Switches default to Admin UP (standard Cisco default for switchports)
            port.admin_status = AdminStatus.UP
            # Local 3D slot layout (2 rows of 12 ports centered on faceplate)
            col = (i - 1) % 12
            row = (i - 1) // 12
            x_offset = -0.13 + col * 0.024
            y_offset = -0.008 if row == 0 else 0.008
            port.local_slot_pos = (x_offset, y_offset, 0.252)

            self.add_port(port)

    def learn_mac(self, mac: str, port_name: str, vlan: int = 1) -> None:
        """Learn or update a MAC address entry on a specific port."""
        self.mac_table[mac.upper()] = {
            "port": port_name,
            "vlan": vlan,
        }

    def lookup_mac(self, mac: str, vlan: int = 1) -> Optional[str]:
        """Look up the port for a target MAC address. Returns port_name or None if unknown."""
        entry = self.mac_table.get(mac.upper())
        if entry and entry["vlan"] == vlan:
            return entry["port"]
        return None

    def clear_mac_table(self) -> None:
        self.mac_table.clear()

    def get_device_info(self) -> str:
        active_count = len(self.get_operational_ports())
        return f"Switch '{self.hostname}' [1U] | {active_count}/24 Ports Active | MACs Learned: {len(self.mac_table)}"

    def serialize(self) -> Dict[str, Any]:
        data = super().serialize()
        data["mac_table"] = self.mac_table
        data["vlans"] = self.vlans
        return data

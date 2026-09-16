"""Personal Computer / Workstation host device."""

from typing import Any, Dict, Optional, Tuple
from .device import Device
from .port import Port, PortType, AdminStatus


class PC(Device):
    """Network workstation host with single Ethernet NIC (eth0) and IP configuration."""

    def __init__(self, device_id: str, hostname: str = "PC1"):
        super().__init__(device_id=device_id, hostname=hostname, device_type="PC", u_height=2)

        self.default_gateway: Optional[str] = None
        self.dns_server: Optional[str] = None

        self._init_ports()

    def _init_ports(self) -> None:
        """Create dual Gigabit Ethernet interfaces (eth0 and eth1)."""
        eth0 = Port(
            port_id=f"{self.device_id}_eth0",
            port_name="eth0",
            port_type=PortType.GIGABIT_ETHERNET,
            speed=1000,
            mac_address=f"00:50:56:{self.device_id[-2:] if len(self.device_id)>=2 else '01'}:AA:10"
        )
        eth0.admin_status = AdminStatus.UP
        eth0.local_slot_pos = (0.105, -0.015, 0.252)
        self.add_port(eth0)

        eth1 = Port(
            port_id=f"{self.device_id}_eth1",
            port_name="eth1",
            port_type=PortType.GIGABIT_ETHERNET,
            speed=1000,
            mac_address=f"00:50:56:{self.device_id[-2:] if len(self.device_id)>=2 else '01'}:AA:20"
        )
        eth1.admin_status = AdminStatus.UP
        eth1.local_slot_pos = (0.138, -0.015, 0.252)
        self.add_port(eth1)

    @property
    def eth0(self) -> Port:
        return self.ports["eth0"]

    @property
    def eth1(self) -> Port:
        return self.ports["eth1"]

    def set_ip_config(self, ip: str, mask: str, gateway: Optional[str] = None) -> None:
        """Configure IP address, subnet mask, and default gateway."""
        self.eth0.ip_address = ip
        self.eth0.subnet_mask = mask
        if gateway is not None:
            self.default_gateway = gateway

    def get_device_info(self) -> str:
        ip_str = self.eth0.ip_address or "Not configured"
        gw_str = self.default_gateway or "None"
        status_str = "LINK UP" if self.eth0.is_operational else "LINK DOWN"
        return f"PC '{self.hostname}' | IP: {ip_str} | GW: {gw_str} | [{status_str}]"

    def serialize(self) -> Dict[str, Any]:
        data = super().serialize()
        data["default_gateway"] = self.default_gateway
        data["dns_server"] = self.dns_server
        return data

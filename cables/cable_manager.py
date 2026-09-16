"""Registry and manager for all physical cables in the world."""

from typing import Dict, List, Optional, Tuple
from .cable import Cable, CableType
from devices.port import Port
from core.event_bus import EventBus


class CableManager:
    """Manages creation, registry, and detachment of physical cables."""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self._cables: Dict[str, Cable] = {}
        self._counter: int = 1
        self._event_bus = event_bus

        # Predefined patch cable colors for nice visual variety in racks
        self._color_palette = [
            (0.18, 0.48, 0.95),  # Royal Blue
            (0.95, 0.75, 0.12),  # Amber Yellow
            (0.15, 0.82, 0.45),  # Mint Green
            (0.92, 0.32, 0.32),  # Coral Red
            (0.72, 0.35, 0.88),  # Purple
        ]

    def connect_ports(
        self,
        port_a: Port,
        port_b: Port,
        cable_type: CableType = CableType.CAT6_ETHERNET
    ) -> Tuple[bool, Optional[Cable], str]:
        """Connect two ports with a new cable."""
        if port_a == port_b:
            return False, None, "Cannot connect a port to itself"

        if port_a.connected_port is not None:
            return False, None, f"Port {port_a.port_name} is already connected to {port_a.connected_port.port_name}"

        if port_b.connected_port is not None:
            return False, None, f"Port {port_b.port_name} is already connected to {port_b.connected_port.port_name}"

        # Assign cable ID and color
        cable_id = f"cable_{self._counter}"
        self._counter += 1
        color = self._color_palette[(self._counter - 1) % len(self._color_palette)]

        cable = Cable(cable_id=cable_id, cable_type=cable_type, color=color)
        success = cable.connect(port_a, port_b)
        if not success:
            return False, None, "Failed to connect cable endpoints"

        self._cables[cable_id] = cable

        if self._event_bus:
            self._event_bus.publish(
                "CABLE_CONNECTED",
                cable=cable,
                port_a=port_a,
                port_b=port_b
            )

        return True, cable, f"Connected {port_a.port_name} <-> {port_b.port_name}"

    def remove_cable(self, cable_id: str) -> bool:
        """Disconnect and remove cable from registry."""
        cable = self._cables.get(cable_id)
        if not cable:
            return False

        port_a = cable.endpoint_a
        port_b = cable.endpoint_b
        cable.disconnect()
        del self._cables[cable_id]

        if self._event_bus:
            self._event_bus.publish(
                "CABLE_DISCONNECTED",
                cable_id=cable_id,
                port_a=port_a,
                port_b=port_b
            )

        return True

    def get_cable_for_port(self, port: Port) -> Optional[Cable]:
        for cable in self._cables.values():
            if cable.endpoint_a == port or cable.endpoint_b == port:
                return cable
        return None

    def get_all_cables(self) -> List[Cable]:
        return list(self._cables.values())

    def clear(self) -> None:
        for cable in list(self._cables.values()):
            cable.disconnect()
        self._cables.clear()

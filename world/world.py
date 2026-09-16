"""World manager coordinating room, racks, desk, devices, and cables."""

from typing import Dict, List, Optional, Tuple
from .room import Room
from .rack import Rack
from .desk import Desk
from .interactable import Interactable
from devices.device import Device


class World:
    """Encapsulates the 3D Network Lab world state."""

    def __init__(self):
        self.room: Room = Room()
        self.racks: Dict[str, Rack] = {}
        self.desk: Desk = Desk(position=(0.0, 0.0, 3.5))

        self._init_racks()

    def _init_racks(self) -> None:
        """Create 3 standard 42U server racks aligned side-by-side."""
        # Rack A (Left)
        self.racks["Rack A"] = Rack(rack_id="Rack A", position=(-3.5, 0.0, -3.0))
        # Rack B (Center)
        self.racks["Rack B"] = Rack(rack_id="Rack B", position=(0.0, 0.0, -3.0))
        # Rack C (Right)
        self.racks["Rack C"] = Rack(rack_id="Rack C", position=(3.5, 0.0, -3.0))

    def get_all_interactables(self) -> List[Interactable]:
        """Return list of all interactable world entities."""
        items: List[Interactable] = list(self.racks.values())
        items.append(self.desk)
        return items

    def get_all_devices(self) -> List[Device]:
        """Collect all devices installed across all racks."""
        devices: List[Device] = []
        for rack in self.racks.values():
            devices.extend(rack.devices)
        return devices

    def find_device_by_id(self, device_id: str) -> Optional[Device]:
        for rack in self.racks.values():
            for dev in rack.devices:
                if dev.device_id == device_id:
                    return dev
        return None

    def get_collision_boxes(self) -> List[Tuple[float, float, float, float, float, float]]:
        """Collect AABBs of all solid obstacles in the lab."""
        boxes: List[Tuple[float, float, float, float, float, float]] = []
        # Room boundaries
        boxes.extend(self.room.get_wall_boxes())
        # Server Racks
        for rack in self.racks.values():
            boxes.append(rack.get_bounding_box())
        # Desk
        boxes.append(self.desk.get_bounding_box())
        return boxes

    def render(self) -> None:
        """Render the complete 3D environment."""
        self.room.render()
        self.desk.render()
        for rack in self.racks.values():
            rack.render()

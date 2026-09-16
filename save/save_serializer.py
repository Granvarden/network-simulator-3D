"""JSON State Serializer for world, hardware, and network topologies."""

from typing import Any, Dict
from world.world import World
from player.player import Player
from inventory.inventory import Inventory
from cables.cable_manager import CableManager


class SaveSerializer:
    """Serializes and deserializes simulation state into pure JSON-compatible dictionaries."""

    @staticmethod
    def serialize_game_state(
        world: World,
        player: Player,
        inventory: Inventory,
        cable_manager: CableManager
    ) -> Dict[str, Any]:
        """Convert live simulator objects into JSON dictionary."""
        data: Dict[str, Any] = {
            "version": "1.0",
            "player": {
                "position": list(player.position),
                "yaw": player.camera.yaw,
                "pitch": player.camera.pitch,
            },
            "inventory": {
                item_type.value: count
                for item_type, count in inventory.get_all_stock().items()
            },
            "racks": {},
            "cables": [c.serialize() for c in cable_manager.get_all_cables()]
        }

        for rack_id, rack in world.racks.items():
            data["racks"][rack_id] = {
                "devices": [dev.serialize() for dev in rack.devices]
            }

        return data

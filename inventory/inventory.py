"""Inventory system tracking player network equipment stock."""

from typing import Dict
from config.game_config import GameConfig
from .item import ItemType


class Inventory:
    """Tracks stock of network devices and patch cables available to the engineer."""

    def __init__(self):
        self._stock: Dict[ItemType, int] = {
            ItemType.ROUTER: GameConfig.INITIAL_ROUTERS,
            ItemType.SWITCH: GameConfig.INITIAL_SWITCHES,
            ItemType.PC: GameConfig.INITIAL_PCS,
            ItemType.ETHERNET_CABLE: GameConfig.INITIAL_CABLES,
        }

    def get_count(self, item_type: ItemType) -> int:
        return self._stock.get(item_type, 0)

    def has_item(self, item_type: ItemType, count: int = 1) -> bool:
        return self.get_count(item_type) >= count

    def add_item(self, item_type: ItemType, count: int = 1) -> None:
        if count > 0:
            self._stock[item_type] = self.get_count(item_type) + count

    def remove_item(self, item_type: ItemType, count: int = 1) -> bool:
        if self.has_item(item_type, count):
            self._stock[item_type] -= count
            return True
        return False

    def get_all_stock(self) -> Dict[ItemType, int]:
        return dict(self._stock)

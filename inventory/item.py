"""Inventory item definitions."""

from dataclasses import dataclass
from enum import Enum


class ItemType(Enum):
    ROUTER = "Router"
    SWITCH = "Switch"
    PC = "PC"
    ETHERNET_CABLE = "Ethernet Cable"


@dataclass
class InventoryItem:
    item_type: ItemType
    name: str
    description: str
    u_size: int = 1

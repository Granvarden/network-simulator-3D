"""Unit tests for Save and Load system."""

import os
import shutil
import pytest
from world.world import World
from player.player import Player
from inventory.inventory import Inventory
from cables.cable_manager import CableManager
from devices.router import Router
from devices.switch import Switch
from save.save_serializer import SaveSerializer
from save.save_manager import SaveManager


def test_save_serialization_and_disk_io():
    test_saves_dir = "test_saves_temp"
    os.makedirs(test_saves_dir, exist_ok=True)

    try:
        world = World()
        player = Player((1.0, 0.0, 2.0))
        inventory = Inventory()
        cable_mgr = CableManager()

        # Mount hardware
        r1 = Router("r1", "Core-R1")
        sw1 = Switch("sw1", "Access-SW1")
        world.racks["Rack A"].install_device(r1, 1)
        world.racks["Rack A"].install_device(sw1, 4)

        # Connect cable
        cable_mgr.connect_ports(r1.get_port("Gi0/0"), sw1.get_port("Gi0/1"))

        # 1. Serialize
        data = SaveSerializer.serialize_game_state(world, player, inventory, cable_mgr)

        assert data["version"] == "1.0"
        assert "player" in data
        assert "racks" in data
        assert "Rack A" in data["racks"]
        assert len(data["racks"]["Rack A"]["devices"]) == 2
        assert len(data["cables"]) == 1

        # 2. Write to File
        save_mgr = SaveManager(saves_dir=test_saves_dir)
        saved = save_mgr.save_to_file(data, "test_save.json")
        assert saved

        # 3. Read back from File
        loaded_data = save_mgr.load_from_file("test_save.json")
        assert loaded_data is not None
        assert loaded_data["player"]["position"] == [1.0, 0.0, 2.0]
        assert len(loaded_data["cables"]) == 1

    finally:
        if os.path.exists(test_saves_dir):
            shutil.rmtree(test_saves_dir)

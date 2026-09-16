"""Unit tests for the revamped interaction modes (Cabling & CLI vs Hardware Management)."""

import pytest
from world.rack import Rack
from devices.device_factory import DeviceFactory
from devices.port import Port, AdminStatus, LinkStatus
from player.interaction import InteractionDetector, InteractionTarget
from cables.cable_manager import CableManager
from inventory.inventory import Inventory
from inventory.item import ItemType
from network.network_engine import NetworkEngine
from ui.interaction_panel import InteractionPanel


def test_interaction_detector_modes():
    detector = InteractionDetector()
    rack = Rack("Rack A", position=(0.0, 0.0, -3.0))
    router = DeviceFactory.create_device("Router", "R1")
    rack.install_device(router, 1)

    # 1. Aiming directly at empty U slot in HARDWARE_MGMT mode
    target_empty_hw = detector.find_target(
        eye_pos=(0.0, rack.get_world_y_for_u(10), -1.5),
        forward=(0.0, 0.0, -1.0),
        interactables=[rack],
        mode="HARDWARE_MGMT"
    )
    assert target_empty_hw.target_type == "RACK"
    assert "Install Device" in target_empty_hw.hint_text

    # 2. Aiming directly at empty U slot in CABLING_CLI mode
    target_empty_cabling = detector.find_target(
        eye_pos=(0.0, rack.get_world_y_for_u(10), -1.5),
        forward=(0.0, 0.0, -1.0),
        interactables=[rack],
        mode="CABLING_CLI"
    )
    assert target_empty_cabling.target_type == "RACK"
    assert "Available" in target_empty_cabling.hint_text

    # 3. Aiming at installed device in HARDWARE_MGMT mode
    dev_y = rack.get_world_y_for_u(1) + 0.04
    target_dev_hw = detector.find_target(
        eye_pos=(0.0, dev_y, -1.5),
        forward=(0.0, 0.0, -1.0),
        interactables=[rack],
        mode="HARDWARE_MGMT"
    )
    assert target_dev_hw.device == router
    assert "Remove R1" in target_dev_hw.hint_text

    # 4. Aiming at installed device in CABLING_CLI mode
    target_dev_cabling = detector.find_target(
        eye_pos=(0.0, dev_y, -1.5),
        forward=(0.0, 0.0, -1.0),
        interactables=[rack],
        mode="CABLING_CLI"
    )
    assert target_dev_cabling.device == router
    # May hit port or device body; both should offer CLI / Cabling hints
    assert "[E] Open CLI" in target_dev_cabling.hint_text


def test_interaction_panel_install_and_remove_flow():
    inventory = Inventory()
    cable_manager = CableManager()
    net_engine = NetworkEngine()
    rack = Rack("Rack A", position=(0.0, 0.0, -3.0))

    panel = InteractionPanel(
        inventory=inventory,
        cable_manager=cable_manager,
        network_engine=net_engine,
        on_open_cli=lambda d: None,
        on_close=lambda: None
    )

    initial_routers = inventory.get_count(ItemType.ROUTER)

    # 1. Open Install modal for empty U5
    target_slot = InteractionTarget(
        target_type="RACK",
        rack=rack,
        targeted_u=5
    )
    panel.open_for_target(target_slot)
    panel._set_device_type("Router")

    # Perform install
    panel._handle_install_device()

    installed_dev = rack.get_device_at_u(5)
    assert installed_dev is not None
    assert installed_dev.device_type == "Router"
    assert inventory.get_count(ItemType.ROUTER) == initial_routers - 1
    assert installed_dev.device_id in net_engine.devices

    # 2. Open Remove modal for installed device
    target_dev = InteractionTarget(
        target_type="DEVICE",
        rack=rack,
        device=installed_dev,
        targeted_u=5
    )
    panel.open_for_target(target_dev)

    # Perform remove
    panel._handle_remove_device()
    assert rack.get_device_at_u(5) is None
    assert inventory.get_count(ItemType.ROUTER) == initial_routers
    assert installed_dev.device_id not in net_engine.devices


def test_cabling_flow_connect_and_unplug():
    cable_mgr = CableManager()
    r1 = DeviceFactory.create_device("Router", "R1")
    sw1 = DeviceFactory.create_device("Switch", "SW1")

    p1 = r1.get_port("Gi0/0")
    p2 = sw1.get_port("Gi0/1")
    assert p1 is not None and p2 is not None
    assert p1.connected_port is None

    # Connect
    ok, cable, msg = cable_mgr.connect_ports(p1, p2)
    assert ok is True
    assert p1.connected_port == p2
    assert p2.connected_port == p1
    assert len(cable_mgr.get_all_cables()) == 1

    # Unplug via cable_manager
    cable_mgr.remove_cable(cable.cable_id)
    assert p1.connected_port is None
    assert p2.connected_port is None
    assert len(cable_mgr.get_all_cables()) == 0

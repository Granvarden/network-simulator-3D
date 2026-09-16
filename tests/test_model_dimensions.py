"""Tests verifying standardized dimensions, depth alignment, and port coordinates across Router, Switch, and PC."""

import pytest
from devices.device_factory import DeviceFactory
from world.rack import Rack


def test_standardized_device_ports_and_faceplate_depth():
    router = DeviceFactory.create_device("Router", "R1")
    switch = DeviceFactory.create_device("Switch", "SW1")
    pc = DeviceFactory.create_device("PC", "PC1")

    # All devices must place their ports on the standardized front faceplate (z = 0.252)
    for p in router.ports.values():
        assert abs(p.local_slot_pos[2] - 0.252) < 1e-4, f"Router port {p.port_name} Z is not 0.252"

    for p in switch.ports.values():
        assert abs(p.local_slot_pos[2] - 0.252) < 1e-4, f"Switch port {p.port_name} Z is not 0.252"

    for p in pc.ports.values():
        assert abs(p.local_slot_pos[2] - 0.252) < 1e-4, f"PC port {p.port_name} Z is not 0.252"


def test_rack_installation_mount_depth_alignment():
    rack = Rack("Rack A", position=(0.0, 0.0, -3.0))
    router = DeviceFactory.create_device("Router", "R1")
    switch = DeviceFactory.create_device("Switch", "SW1")
    pc = DeviceFactory.create_device("PC", "PC1")

    rack.install_device(router, 1)
    rack.install_device(switch, 4)
    rack.install_device(pc, 6)

    # All installed devices must have position centered at rack.position[2] + 0.15
    for dev in (router, switch, pc):
        assert dev.position is not None
        assert abs(dev.position[2] - (-3.0 + 0.15)) < 1e-4
        assert abs(dev.position[0] - 0.0) < 1e-4

        # Verify front faceplate of all devices is exactly aligned at Z = -3.0 + 0.402
        for port in dev.ports.values():
            port_world_z = dev.position[2] + port.local_slot_pos[2]
            assert abs(port_world_z - (-3.0 + 0.402)) < 1e-4

"""Integration test simulating SandboxScene user interactions for Cabling and Hardware modes."""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
import pytest
from core.service_container import ServiceContainer
from core.event_bus import EventBus
from core.time_manager import TimeManager
from core.input_manager import InputManager
from core.game_state import GameStateManager, GameState
from scenes.sandbox_scene import SandboxScene
from player.interaction import InteractionTarget


def setup_test_sandbox():
    pygame.init()
    pygame.font.init()
    # Create headless dummy display
    pygame.display.set_mode((1280, 720))

    services = ServiceContainer()
    event_bus = EventBus()
    services.register("event_bus", event_bus)
    services.register("time_manager", TimeManager())
    services.register("input_manager", InputManager())
    state_mgr = GameStateManager()
    services.register("state_manager", state_mgr)

    scene = SandboxScene(services)
    scene.on_enter()
    return scene


def test_sandbox_cabling_and_cli_flow():
    scene = setup_test_sandbox()

    # Initial mode should be CABLING_CLI
    assert scene.interaction_mode == "CABLING_CLI"
    assert scene.active_modal is None

    # 1. Point camera towards Rack A (where R1 is installed at U1)
    # Rack A is at (0, 0, -3.0)
    scene.player.controller.x = 0.0
    scene.player.controller.y = 0.4
    scene.player.controller.z = -1.8
    scene.player.camera.x = 0.0
    scene.player.camera.y = 0.4 + 1.7
    scene.player.camera.z = -1.8
    scene.player.camera.yaw = -90.0  # Face towards -Z
    scene.player.camera.pitch = -30.0

    # Run one update frame
    input_mgr = scene.services.get("input_manager")
    scene.update(0.016)

    target = scene.player.current_target
    assert target.target_type in ("PORT", "DEVICE", "RACK")

    # 2. Test Pressing E directly opens CLI on device in CABLING_CLI mode
    if target.device:
        e_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)
        handled = scene.handle_event(e_event)
        assert handled is True
        assert scene.active_modal == "CLI"
        assert scene.cli_engine.current_device == target.device

        # Close terminal
        scene._close_terminal()
        assert scene.active_modal is None

    # 3. Test Pressing R toggles to HARDWARE_MGMT mode
    r_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r)
    handled = scene.handle_event(r_event)
    assert handled is True
    assert scene.interaction_mode == "HARDWARE_MGMT"
    assert "HARDWARE" in scene.mode_notification

    # 4. In HARDWARE_MGMT mode, pressing E on device opens Remove modal
    if target.device:
        e_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)
        handled = scene.handle_event(e_event)
        assert handled is True
        assert scene.active_modal == "INTERACTION"
        assert scene.interaction_panel.target_device == target.device

        # Close modal
        scene._close_modal()
        assert scene.active_modal is None

    # 5. Toggle back to CABLING_CLI mode
    scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r))
    assert scene.interaction_mode == "CABLING_CLI"

    # 6. Test Cabling Flow with F key
    r1 = scene.world.racks["Rack A"].get_device_at_u(1)
    assert r1 is not None
    port_g1 = r1.get_port("Gi0/1")  # currently empty port

    # Simulate targeting port_g1
    scene.player.current_target.target_type = "PORT"
    scene.player.current_target.device = r1
    scene.player.current_target.port = port_g1

    # Press F to pick up cable
    f_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_f)
    scene.handle_event(f_event)
    assert scene.held_cable_port == port_g1
    assert "Cabling: Selected" in scene.sens_notification

    # Press ESC to cancel held cable
    esc_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
    scene.handle_event(esc_event)
    assert scene.held_cable_port is None
    assert "Cabling cancelled" in scene.sens_notification


def test_overview_hud_rendering():
    from unittest.mock import MagicMock
    scene = setup_test_sandbox()
    ui = MagicMock()

    # 1. Test render when targeting a device
    r1 = scene.world.racks["Rack A"].get_device_at_u(1)
    target = InteractionTarget(
        target_type="DEVICE",
        rack=scene.world.racks["Rack A"],
        device=r1,
        targeted_u=1
    )
    scene.overview_hud.render(ui, target, mode="CABLING_CLI", held_cable_port=None)
    assert ui.draw_rect.called
    assert ui.draw_text.called

    ui.reset_mock()
    scene.hud.render(ui, fps=60.0, target=target, mode="CABLING_CLI", held_cable_port=None)
    assert ui.draw_rect.called
    assert ui.draw_text.called

    # 2. Test render when targeting an empty rack slot
    ui.reset_mock()
    target_slot = InteractionTarget(
        target_type="RACK",
        rack=scene.world.racks["Rack A"],
        targeted_u=12
    )
    scene.overview_hud.render(ui, target_slot, mode="HARDWARE_MGMT", held_cable_port=None)
    assert ui.draw_rect.called
    assert ui.draw_text.called

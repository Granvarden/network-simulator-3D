"""3D First-Person Sandbox Network Lab Scene."""

import pygame
from typing import Optional
from core.game_state import GameState, GameStateManager
from core.service_container import ServiceContainer
from core.input_manager import InputManager
from rendering.renderer import Renderer
from rendering.ui_renderer import UIRenderer
from rendering.lighting import Lighting
from world.world import World
from player.player import Player
from inventory.inventory import Inventory
from cables.cable_manager import CableManager
from cables.cable_renderer import CableRenderer
from network.network_engine import NetworkEngine
from cli.cli_engine import CLIEngine
from ui.hud import HUD
from ui.interaction_panel import InteractionPanel
from ui.terminal import TerminalUI
from ui.inventory_ui import InventoryUI
from ui.debug_overlay import DebugOverlay
from devices.device import Device
from devices.device_factory import DeviceFactory
from .scene import Scene


class SandboxScene(Scene):
    """The main 3D First-Person Data Center & Network Lab gameplay scene."""

    def __init__(self, services: ServiceContainer):
        super().__init__(services)

        # Simulation Subsystems
        self.world: World = World()
        self.player: Player = Player(initial_pos=(0.0, 0.0, 1.5))
        self.inventory: Inventory = Inventory()
        self.network_engine: NetworkEngine = NetworkEngine()
        self.cable_manager: CableManager = CableManager(services.get("event_bus"))
        self.cable_renderer: CableRenderer = CableRenderer()
        self.cli_engine: CLIEngine = CLIEngine(self.network_engine)

        # UI Overlays
        self.hud: HUD = HUD()
        self.debug_overlay: DebugOverlay = DebugOverlay()

        self.interaction_panel = InteractionPanel(
            inventory=self.inventory,
            cable_manager=self.cable_manager,
            on_open_cli=self._open_cli,
            on_close=self._close_modal
        )

        self.terminal_ui = TerminalUI(
            cli_engine=self.cli_engine,
            on_close=self._close_terminal
        )

        self.inventory_ui = InventoryUI(
            inventory=self.inventory,
            on_close=self._close_modal
        )

        # Active sub-mode states
        self.active_modal: Optional[str] = None  # None, "INTERACTION", "INVENTORY", "CLI"

        # Initialize default lab devices for immediate playability
        self._setup_initial_lab_devices()

    def _setup_initial_lab_devices(self) -> None:
        """Mount initial sample devices into Rack A for immediate demonstration."""
        rack_a = self.world.racks.get("Rack A")
        if rack_a:
            # Mount a 2U Router at U1
            router = DeviceFactory.create_device("Router", "R1")
            rack_a.install_device(router, 1)
            self.network_engine.register_device(router)

            # Mount a 1U Switch at U4
            switch = DeviceFactory.create_device("Switch", "SW1")
            rack_a.install_device(switch, 4)
            self.network_engine.register_device(switch)

            # Mount a PC Workstation at U6
            pc = DeviceFactory.create_device("PC", "PC1")
            rack_a.install_device(pc, 6)
            self.network_engine.register_device(pc)

            # Auto-patch: Connect R1 Gi0/0 <-> SW1 Gi0/1
            r1_g0 = router.get_port("Gi0/0")
            sw_g1 = switch.get_port("Gi0/1")
            if r1_g0 and sw_g1:
                self.cable_manager.connect_ports(r1_g0, sw_g1)

            # Connect PC1 eth0 <-> SW1 Gi0/2
            pc_eth0 = pc.get_port("eth0")
            sw_g2 = switch.get_port("Gi0/2")
            if pc_eth0 and sw_g2:
                self.cable_manager.connect_ports(pc_eth0, sw_g2)

            # Bring up Router Gi0/0 interface with IP
            from devices.port import AdminStatus
            r1_g0.set_admin_status(AdminStatus.UP)
            r1_g0.ip_address = "192.168.1.1"
            r1_g0.subnet_mask = "255.255.255.0"

            # Set PC1 IP configuration
            pc.set_ip_config("192.168.1.10", "255.255.255.0", "192.168.1.1")

            self.network_engine.update_links()

    def on_enter(self) -> None:
        """Lock mouse cursor for first-person exploration."""
        input_mgr: InputManager = self.services.get("input_manager")
        input_mgr.set_mouse_locked(True)
        self.active_modal = None

    def on_exit(self) -> None:
        input_mgr: InputManager = self.services.get("input_manager")
        input_mgr.set_mouse_locked(False)

    def _open_cli(self, device: Device) -> None:
        self.cli_engine.attach_device(device)
        self.active_modal = "CLI"
        input_mgr: InputManager = self.services.get("input_manager")
        input_mgr.set_mouse_locked(False)

    def _close_cli(self) -> None:
        self.active_modal = None
        input_mgr: InputManager = self.services.get("input_manager")
        input_mgr.set_mouse_locked(True)

    def _close_terminal(self) -> None:
        self._close_cli()

    def _close_modal(self) -> None:
        self.active_modal = None
        input_mgr: InputManager = self.services.get("input_manager")
        input_mgr.set_mouse_locked(True)

    def handle_event(self, event: pygame.event.Event) -> bool:
        input_mgr: InputManager = self.services.get("input_manager")

        # 1. Route to Active Modals if open
        if self.active_modal == "CLI":
            return self.terminal_ui.handle_event(event)

        elif self.active_modal == "INTERACTION":
            return self.interaction_panel.handle_event(event)

        elif self.active_modal == "INVENTORY":
            return self.inventory_ui.handle_event(event)

        # 2. Key Toggles in Free-look Sandbox Mode
        if event.type == pygame.KEYDOWN:
            # F3: Toggle Debug Overlay
            if event.key == pygame.K_F3:
                self.debug_overlay.toggle()
                return True

            # TAB: Open Inventory
            elif event.key == pygame.K_TAB:
                self.active_modal = "INVENTORY"
                input_mgr.set_mouse_locked(False)
                return True

            # ESC: Return to Main Menu or Pause
            elif event.key == pygame.K_ESCAPE:
                state_mgr: GameStateManager = self.services.get("state_manager")
                state_mgr.change_state(GameState.MAIN_MENU)
                return True

            # E: Interact with targeted Rack / Device / Desk
            elif event.key == pygame.K_e:
                target = self.player.current_target
                if target.target_type == "DESK":
                    # Open Workstation CLI attached to PC1 or first available host
                    all_devs = self.world.get_all_devices()
                    pcs = [d for d in all_devs if d.device_type == "PC"]
                    chosen = pcs[0] if pcs else (all_devs[0] if all_devs else None)
                    if chosen:
                        self._open_cli(chosen)
                    return True

                elif target.target_type in ("RACK", "DEVICE"):
                    self.interaction_panel.open_for_target(target)
                    self.active_modal = "INTERACTION"
                    input_mgr.set_mouse_locked(False)
                    return True

        return False

    def update(self, dt: float) -> None:
        input_mgr: InputManager = self.services.get("input_manager")

        # Only update player physics when no modal is intercepting input
        if self.active_modal is None:
            self.player.update(dt, input_mgr, self.world)

        # Update modal animations / timers
        if self.active_modal == "CLI":
            self.terminal_ui.update(dt)

        # Sync network links
        self.network_engine.update_links()

    def resize(self, width: int, height: int) -> None:
        """Propagate resize to all UI overlays."""
        self.hud.resize(width, height)
        self.terminal_ui.resize(width, height)
        self.interaction_panel.resize(width, height)
        self.inventory_ui.resize(width, height)

    def render(self, renderer: Renderer, ui: UIRenderer) -> None:
        # Pass 1: 3D Scene Rendering
        renderer.clear()
        renderer.begin_3d()
        self.player.camera.apply_view()
        Lighting.setup_lights()

        # Render 3D World (Room, 42U Racks, Installed Hardware, Engineer Workstation)
        self.world.render()

        # Render 3D Cables
        self.cable_renderer.render_cables(self.cable_manager.get_all_cables())

        # Pass 2: 2D HUD & UI Overlays
        renderer.begin_2d()

        # In-game HUD
        time_mgr = self.services.get("time_manager")
        self.hud.render(
            ui=ui,
            fps=time_mgr.fps,
            target=self.player.current_target,
            network_status="ONLINE"
        )

        # Render active modal dialog
        if self.active_modal == "INTERACTION":
            self.interaction_panel.render(ui)

        elif self.active_modal == "INVENTORY":
            self.inventory_ui.render(ui)

        elif self.active_modal == "CLI":
            self.terminal_ui.render(ui)

        # Debug Overlay (F3)
        devs = self.world.get_all_devices()
        op_links = sum(1 for c in self.cable_manager.get_all_cables() if c.connected and c.endpoint_a and c.endpoint_a.is_operational)
        self.debug_overlay.render(
            ui=ui,
            fps=time_mgr.fps,
            player_pos=self.player.position,
            device_count=len(devs),
            cable_count=len(self.cable_manager.get_all_cables()),
            current_target_info=self.player.current_target.hint_text,
            operational_links_count=op_links
        )

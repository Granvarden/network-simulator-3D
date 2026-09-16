"""3D First-Person Sandbox Network Lab Scene."""

import pygame
from typing import Optional
from core.game_state import GameState, GameStateManager
from core.service_container import ServiceContainer
from core.input_manager import InputManager
from rendering.renderer import Renderer
from rendering.ui_renderer import UIRenderer
from rendering.lighting import Lighting
from rendering.primitives import draw_wire_box, draw_line_3d
from world.world import World
from player.player import Player
from inventory.inventory import Inventory
from cables.cable_manager import CableManager
from cables.cable_renderer import CableRenderer
from network.network_engine import NetworkEngine
from cli.cli_engine import CLIEngine
from ui.hud import HUD
from ui.overview_hud import OverviewHUD
from ui.interaction_panel import InteractionPanel
from ui.terminal import TerminalUI
from ui.inventory_ui import InventoryUI
from ui.debug_overlay import DebugOverlay
from devices.device import Device
from devices.device_factory import DeviceFactory
from devices.port import Port
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
        self.overview_hud: OverviewHUD = OverviewHUD()
        self.debug_overlay: DebugOverlay = DebugOverlay()

        self.interaction_panel = InteractionPanel(
            inventory=self.inventory,
            cable_manager=self.cable_manager,
            network_engine=self.network_engine,
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

        # Active Interaction Mode: "CABLING_CLI" or "HARDWARE_MGMT" (Toggled with R)
        self.interaction_mode: str = "CABLING_CLI"
        self.held_cable_port: Optional[Port] = None

        # Modal and notification states
        self.active_modal: Optional[str] = None  # None, "INTERACTION", "INVENTORY", "CLI"
        self.sens_notification: str = ""
        self.sens_timer: float = 0.0
        self.mode_notification: str = ""
        self.mode_notif_timer: float = 0.0

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
        self.held_cable_port = None

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

        # 2. Right Click: Cancel Held Cable
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            if self.held_cable_port is not None:
                self.held_cable_port = None
                self.sens_notification = "Cabling cancelled"
                self.sens_timer = 1.5
                return True

        # 3. Key Toggles in Free-look Sandbox Mode
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

            # ESC: Cancel held cable or Return to Main Menu
            elif event.key == pygame.K_ESCAPE:
                if self.held_cable_port is not None:
                    self.held_cable_port = None
                    self.sens_notification = "Cabling cancelled"
                    self.sens_timer = 1.5
                    return True
                state_mgr: GameStateManager = self.services.get("state_manager")
                state_mgr.change_state(GameState.MAIN_MENU)
                return True

            # R: Toggle Interaction Mode (Cabling/CLI vs Hardware Management)
            elif event.key == pygame.K_r:
                if self.interaction_mode == "CABLING_CLI":
                    self.interaction_mode = "HARDWARE_MGMT"
                    self.mode_notification = "MODE: HARDWARE MANAGEMENT (Install / Remove Device)"
                else:
                    self.interaction_mode = "CABLING_CLI"
                    self.mode_notification = "MODE: CABLING & CLI CONSOLE ([E] CLI, [F] Cable)"
                self.mode_notif_timer = 2.2
                self.held_cable_port = None  # Reset held cable on mode switch
                return True

            # E: Mode-specific Action
            elif event.key == pygame.K_e:
                target = self.player.current_target

                # If targeted desk, open engineer workstation CLI
                if target.target_type == "DESK":
                    all_devs = self.world.get_all_devices()
                    pcs = [d for d in all_devs if d.device_type == "PC"]
                    chosen = pcs[0] if pcs else (all_devs[0] if all_devs else None)
                    if chosen:
                        self._open_cli(chosen)
                    return True

                # Mode 1: Cabling & CLI Mode -> E opens CLI directly on targeted device
                if self.interaction_mode == "CABLING_CLI":
                    if target.device:
                        self._open_cli(target.device)
                        return True
                    elif target.target_type == "RACK":
                        # Hint to user that slot is empty
                        self.sens_notification = "Slot is empty. Press [R] for Hardware Mode to install."
                        self.sens_timer = 2.0
                        return True

                # Mode 2: Hardware Management Mode -> E opens Install or Remove modal
                elif self.interaction_mode == "HARDWARE_MGMT":
                    if target.target_type in ("RACK", "DEVICE"):
                        self.interaction_panel.open_for_target(target)
                        self.active_modal = "INTERACTION"
                        input_mgr.set_mouse_locked(False)
                        return True

            # F: Cabling Action (Plug / Unplug / Connect)
            elif event.key == pygame.K_f:
                if self.interaction_mode == "CABLING_CLI":
                    target = self.player.current_target

                    # State A: Not holding any cable
                    if self.held_cable_port is None:
                        if target.target_type == "PORT" and target.port:
                            p = target.port
                            # If port already has cable -> unplug it
                            if p.connected_port:
                                cable = self.cable_manager.get_cable_for_port(p)
                                if cable:
                                    self.cable_manager.remove_cable(cable.cable_id)
                                    self.network_engine.update_links()
                                    self.sens_notification = f"Unplugged cable from {p.port_name}"
                                    self.sens_timer = 2.0
                            else:
                                # Start cabling from this port
                                self.held_cable_port = p
                                d_name = target.device.hostname if target.device else "Device"
                                self.sens_notification = f"Cabling: Selected {d_name}:{p.port_name} -> Aim at partner port"
                                self.sens_timer = 3.0
                            return True
                        elif target.device:
                            self.sens_notification = "Aim crosshair directly at an RJ45 port to plug cable"
                            self.sens_timer = 2.0
                            return True

                    # State B: Already holding cable from Port A
                    else:
                        if target.target_type == "PORT" and target.port:
                            dest_port = target.port
                            if dest_port == self.held_cable_port:
                                self.held_cable_port = None
                                self.sens_notification = "Cabling cancelled"
                                self.sens_timer = 1.5
                            else:
                                ok, cable, msg = self.cable_manager.connect_ports(self.held_cable_port, dest_port)
                                if ok:
                                    src_dev = getattr(self.held_cable_port, "device_ref", None)
                                    src_h = src_dev.hostname if src_dev else "Src"
                                    dst_dev = getattr(dest_port, "device_ref", None)
                                    dst_h = dst_dev.hostname if dst_dev else "Dst"
                                    self.sens_notification = f"Connected {src_h}:{self.held_cable_port.port_name} <-> {dst_h}:{dest_port.port_name}"
                                    self.sens_timer = 2.8
                                    self.held_cable_port = None
                                    self.network_engine.update_links()
                                else:
                                    self.sens_notification = f"Failed: {msg}"
                                    self.sens_timer = 2.5
                            return True
                        else:
                            # Pressed F in empty space -> Cancel held cable
                            self.held_cable_port = None
                            self.sens_notification = "Cabling cancelled"
                            self.sens_timer = 1.5
                            return True

                else:
                    self.sens_notification = "Press [R] to switch to Cabling & CLI Mode first"
                    self.sens_timer = 2.0
                    return True

            # Quick Mouse Sensitivity adjustment: [ / ] or - / =
            elif event.key in (pygame.K_LEFTBRACKET, pygame.K_MINUS):
                self.player.controller.sensitivity = max(0.05, round(self.player.controller.sensitivity - 0.05, 2))
                self.sens_notification = f"Sensitivity: {self.player.controller.sensitivity:.2f}"
                self.sens_timer = 2.0
                return True

            elif event.key in (pygame.K_RIGHTBRACKET, pygame.K_EQUALS):
                self.player.controller.sensitivity = min(1.50, round(self.player.controller.sensitivity + 0.05, 2))
                self.sens_notification = f"Sensitivity: {self.player.controller.sensitivity:.2f}"
                self.sens_timer = 2.0
                return True

        return False

    def update(self, dt: float) -> None:
        input_mgr: InputManager = self.services.get("input_manager")

        # Only update player physics and raycasts when no modal is intercepting input
        if self.active_modal is None:
            self.player.update(
                dt=dt,
                input_mgr=input_mgr,
                world=self.world,
                mode=self.interaction_mode,
                has_held_cable=(self.held_cable_port is not None)
            )

        # Update modal animations / timers
        if self.active_modal == "CLI":
            self.terminal_ui.update(dt)

        # Update sensitivity notification timer
        if self.sens_timer > 0.0:
            self.sens_timer -= dt
            if self.sens_timer <= 0.0:
                self.sens_notification = ""

        # Update mode notification timer
        if self.mode_notif_timer > 0.0:
            self.mode_notif_timer -= dt
            if self.mode_notif_timer <= 0.0:
                self.mode_notification = ""

        # Sync network links
        self.network_engine.update_links()

    def resize(self, width: int, height: int) -> None:
        """Propagate resize to all UI overlays."""
        self.hud.resize(width, height)
        self.overview_hud.resize(width, height)
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

        # Render 3D Crosshair Target Highlights
        target = self.player.current_target

        # 1. Highlight targeted Device (Cyan wireframe bounding box)
        if target.device and target.device_world_pos:
            cx, cy, cz = target.device_world_pos
            sy = target.device.u_height * 0.04445
            box_col = (0.22, 0.74, 0.97) if self.interaction_mode == "CABLING_CLI" else (0.96, 0.62, 0.05)
            draw_wire_box(cx, cy, cz, 0.49, sy, 0.45, box_col, line_width=2.0)

        # 2. Highlight targeted Port (Glowing amber wireframe box)
        if target.port and target.port_world_pos:
            px, py, pz = target.port_world_pos
            draw_wire_box(px, py, pz, 0.032, 0.024, 0.035, (0.98, 0.75, 0.12), line_width=2.5)

        # 3. Highlight targeted empty U-slot in Hardware Management mode
        if target.target_type == "RACK" and target.targeted_u and target.rack and self.interaction_mode == "HARDWARE_MGMT":
            slot_sy = 0.04445
            slot_cy = target.rack.get_world_y_for_u(target.targeted_u) + slot_sy / 2.0
            draw_wire_box(
                target.rack.position[0], slot_cy, target.rack.position[2] + 0.12,
                0.49, slot_sy, 0.45,
                (0.96, 0.62, 0.05), line_width=2.0
            )

        # 4. Render active held cable in 3D from Source Port to Crosshair / Destination Port
        if self.held_cable_port:
            p1 = CableRenderer.get_port_world_coords(self.held_cable_port)
            if p1:
                if target.port and target.port_world_pos:
                    p2 = target.port_world_pos
                else:
                    cam = self.player.camera
                    fwd = cam.get_forward_vector()
                    p2 = (cam.x + fwd[0] * 1.5, cam.y + fwd[1] * 1.5, cam.z + fwd[2] * 1.5)
                draw_line_3d(p1[0], p1[1], p1[2], p2[0], p2[1], p2[2], (0.98, 0.80, 0.08), line_width=3.0)

        # Pass 2: 2D HUD & UI Overlays
        renderer.begin_2d()

        # Top & Bottom In-game HUD
        time_mgr = self.services.get("time_manager")
        self.hud.render(
            ui=ui,
            fps=time_mgr.fps,
            target=self.player.current_target,
            network_status="ONLINE",
            mode=self.interaction_mode,
            held_cable_port=self.held_cable_port
        )

        # Bottom-Right Real-Time Overview HUD Card
        if self.active_modal is None:
            self.overview_hud.render(
                ui=ui,
                target=self.player.current_target,
                mode=self.interaction_mode,
                held_cable_port=self.held_cable_port
            )

        # Mode switch notification pill
        if self.mode_notification:
            mode_accent = (56, 189, 248) if self.interaction_mode == "CABLING_CLI" else (245, 158, 11)
            pill_w = max(340, len(self.mode_notification) * 8 + 36)
            pill_h = 34
            pill_x = self.hud.screen_w / 2.0 - pill_w / 2.0
            pill_y = 54
            ui.draw_rect(pill_x, pill_y, pill_w, pill_h, (15, 23, 42), alpha=0.94, corner_radius=17.0)
            ui.draw_rect_outline(pill_x, pill_y, pill_w, pill_h, mode_accent, line_width=1.5)
            ui.draw_text(self.mode_notification, self.hud.screen_w / 2.0, pill_y + pill_h / 2.0, font_size=13, color=mode_accent, center_x=True, center_y=True)

        # Sensitivity / Action notification pill
        elif self.sens_notification:
            pill_w = max(220, len(self.sens_notification) * 8 + 36)
            pill_h = 32
            pill_x = self.hud.screen_w / 2.0 - pill_w / 2.0
            pill_y = 54
            ui.draw_rect(pill_x, pill_y, pill_w, pill_h, (15, 23, 42), alpha=0.92, corner_radius=16.0)
            ui.draw_rect_outline(pill_x, pill_y, pill_w, pill_h, (56, 189, 248), line_width=1.5)
            ui.draw_text(self.sens_notification, self.hud.screen_w / 2.0, pill_y + pill_h / 2.0, font_size=13, color=(56, 189, 248), center_x=True, center_y=True)

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

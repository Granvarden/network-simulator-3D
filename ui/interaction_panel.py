"""Hardware Management Modal dialogs for Installing and Removing rack equipment."""

from typing import Callable, List, Optional
import pygame
from config.game_config import GameConfig
from config.graphics_config import GraphicsConfig
from rendering.ui_renderer import UIRenderer
from world.rack import Rack
from devices.device import Device
from devices.device_factory import DeviceFactory
from inventory.inventory import Inventory
from inventory.item import ItemType
from cables.cable_manager import CableManager
from network.network_engine import NetworkEngine
from player.interaction import InteractionTarget
from .widgets.button import Button
from .widgets.panel import Panel


class InteractionPanel:
    """Dedicated modal for Hardware Management: Install Device or Remove Device."""

    def __init__(
        self,
        inventory: Inventory,
        cable_manager: CableManager,
        network_engine: Optional[NetworkEngine],
        on_open_cli: Callable[[Device], None],
        on_close: Callable[[], None],
        screen_w: int = GameConfig.WINDOW_WIDTH,
        screen_h: int = GameConfig.WINDOW_HEIGHT
    ):
        self.inventory: Inventory = inventory
        self.cable_manager: CableManager = cable_manager
        self.network_engine: Optional[NetworkEngine] = network_engine
        self.on_open_cli: Callable[[Device], None] = on_open_cli
        self.on_close: Callable[[], None] = on_close
        self.screen_w = screen_w
        self.screen_h = screen_h

        # Active target state
        self.target: Optional[InteractionTarget] = None
        self.target_rack: Optional[Rack] = None
        self.target_device: Optional[Device] = None
        self.selected_u: int = 1
        self.selected_device_type: str = "Router"

        # Feedback status
        self.status_message: str = ""
        self.status_is_error: bool = False

        # Panel Geometry
        self.w = 560
        self.h = 420
        self.x = (screen_w - self.w) / 2.0
        self.y = (screen_h - self.h) / 2.0
        self.panel = Panel(self.x, self.y, self.w, self.h, corner_radius=14.0)

        self.buttons: List[Button] = []
        self._rebuild_buttons()

    def resize(self, width: int, height: int) -> None:
        self.screen_w = width
        self.screen_h = height
        self.x = (width - self.w) / 2.0
        self.y = (height - self.h) / 2.0
        self.panel.x = self.x
        self.panel.y = self.y
        self._rebuild_buttons()

    def open_for_target(self, target: InteractionTarget) -> None:
        """Configure modal for either Install or Remove action based on target."""
        self.target = target
        self.target_rack = target.rack
        self.target_device = target.device
        self.selected_u = target.targeted_u or 1
        self.status_message = ""
        self.status_is_error = False
        self._rebuild_buttons()

    def _rebuild_buttons(self) -> None:
        self.buttons.clear()

        # Cancel / Close button at bottom left
        self.cancel_btn = Button(
            self.x + 30, self.y + self.h - 56, 120, 38,
            "Cancel",
            on_click=self.on_close
        )
        self.buttons.append(self.cancel_btn)

        # 1. REMOVE DEVICE MODAL
        if self.target_device:
            self.remove_confirm_btn = Button(
                self.x + 170, self.y + self.h - 56, self.w - 200, 38,
                f"Remove {self.target_device.hostname} & Reclaim",
                on_click=self._handle_remove_device,
                is_primary=True
            )
            self.buttons.append(self.remove_confirm_btn)

        # 2. INSTALL DEVICE MODAL
        elif self.target_rack:
            # Device type selection buttons
            dev_types = [("Router", "Router (2U)"), ("Switch", "Switch (1U)"), ("PC", "PC Host (2U)")]
            bx = self.x + 30
            for dt, label in dev_types:
                is_sel = (self.selected_device_type == dt)
                btn = Button(
                    bx, self.y + 115, 155, 38,
                    label,
                    on_click=lambda t=dt: self._set_device_type(t),
                    is_primary=is_sel
                )
                self.buttons.append(btn)
                bx += 172

            # U slot selector buttons
            self.u_minus_btn = Button(
                self.x + 200, self.y + 175, 42, 34, "-",
                on_click=self._decrement_u
            )
            self.u_plus_btn = Button(
                self.x + 320, self.y + 175, 42, 34, "+",
                on_click=self._increment_u
            )
            self.buttons.append(self.u_minus_btn)
            self.buttons.append(self.u_plus_btn)

            # Primary Install button
            self.install_btn = Button(
                self.x + 170, self.y + self.h - 56, self.w - 200, 38,
                f"Install {self.selected_device_type} into Slot U{self.selected_u}",
                on_click=self._handle_install_device,
                is_primary=True
            )
            self.buttons.append(self.install_btn)

    def _set_device_type(self, dev_type: str) -> None:
        self.selected_device_type = dev_type
        self.status_message = ""
        self._rebuild_buttons()

    def _decrement_u(self) -> None:
        if self.selected_u > 1:
            self.selected_u -= 1
            self.status_message = ""
            self._rebuild_buttons()

    def _increment_u(self) -> None:
        if self.selected_u < 42:
            self.selected_u += 1
            self.status_message = ""
            self._rebuild_buttons()

    def _handle_install_device(self) -> None:
        if not self.target_rack:
            return

        item_map = {
            "Router": ItemType.ROUTER,
            "Switch": ItemType.SWITCH,
            "PC": ItemType.PC,
        }
        item_type = item_map.get(self.selected_device_type)
        if not item_type or not self.inventory.has_item(item_type):
            self.status_message = f"Cannot install: No {self.selected_device_type} left in inventory!"
            self.status_is_error = True
            return

        new_dev = DeviceFactory.create_device(self.selected_device_type)
        success, msg = self.target_rack.install_device(new_dev, self.selected_u)
        if success:
            self.inventory.remove_item(item_type, 1)
            if self.network_engine:
                self.network_engine.register_device(new_dev)
            self.on_close()
        else:
            self.status_message = f"Cannot install: {msg}"
            self.status_is_error = True

    def _handle_remove_device(self) -> None:
        if not self.target_rack or not self.target_device:
            return

        dev = self.target_device
        # Disconnect any attached cables from CableManager
        for port in list(dev.ports.values()):
            cable = self.cable_manager.get_cable_for_port(port)
            if cable:
                self.cable_manager.remove_cable(cable.cable_id)

        # Unregister from NetworkEngine
        if self.network_engine:
            self.network_engine.unregister_device(dev)

        # Remove from rack
        success, msg = self.target_rack.remove_device(dev)
        if success:
            item_map = {
                "Router": ItemType.ROUTER,
                "Switch": ItemType.SWITCH,
                "PC": ItemType.PC,
            }
            item_type = item_map.get(dev.device_type)
            if item_type:
                self.inventory.add_item(item_type, 1)
            self.on_close()
        else:
            self.status_message = f"Error: {msg}"
            self.status_is_error = True

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.on_close()
            return True

        for btn in self.buttons:
            if btn.handle_event(event):
                return True

        return False

    def render(self, ui: UIRenderer) -> None:
        # Dim backdrop
        ui.draw_rect(0, 0, self.screen_w, self.screen_h, (15, 23, 42), alpha=0.6)

        # Main Card Panel
        self.panel.render(ui)

        # 1. REMOVE DEVICE MODAL VIEW
        if self.target_device:
            dev = self.target_device
            rack_name = self.target_rack.rack_id if self.target_rack else "Rack"
            u_range = f"U{dev.start_u}-U{dev.start_u + dev.u_height - 1}" if dev.start_u else ""

            # Title
            ui.draw_text("Hardware Management: Remove Device", self.x + 30, self.y + 32, font_size=20, color=GraphicsConfig.COLOR_TEXT_PRIMARY)
            ui.draw_text(f"Confirm hardware removal from {rack_name}", self.x + 30, self.y + 60, font_size=13, color=GraphicsConfig.COLOR_TEXT_MUTED)

            # Warning / Summary Box
            card_y = self.y + 90
            ui.draw_rect(self.x + 30, card_y, self.w - 60, 180, (254, 242, 242), alpha=1.0, corner_radius=8.0)
            ui.draw_rect_outline(self.x + 30, card_y, self.w - 60, 180, (252, 165, 165), line_width=1.0)

            ui.draw_text(f"Device: {dev.hostname} ({dev.device_type})", self.x + 48, card_y + 24, font_size=16, color=(153, 27, 27))
            ui.draw_text(f"Location: {rack_name} [{u_range}]", self.x + 48, card_y + 50, font_size=13, color=(185, 28, 28))

            # Count connected cables
            connected_cables = sum(1 for p in dev.ports.values() if p.connected_port is not None)
            ui.draw_text(f"Connected Cables: {connected_cables} patch cables", self.x + 48, card_y + 76, font_size=13, color=(185, 28, 28))

            ui.draw_text(
                "Warning: Detaching this device will immediately unplug all connected",
                self.x + 48, card_y + 112,
                font_size=12,
                color=(127, 29, 29)
            )
            ui.draw_text(
                "cables and safely return the equipment to your inventory.",
                self.x + 48, card_y + 130,
                font_size=12,
                color=(127, 29, 29)
            )

        # 2. INSTALL DEVICE MODAL VIEW
        elif self.target_rack:
            rack_name = self.target_rack.rack_id

            # Title
            ui.draw_text("Hardware Management: Install Device", self.x + 30, self.y + 32, font_size=20, color=GraphicsConfig.COLOR_TEXT_PRIMARY)
            ui.draw_text(f"Mount new network equipment into {rack_name}", self.x + 30, self.y + 60, font_size=13, color=GraphicsConfig.COLOR_TEXT_MUTED)

            # Section 1: Equipment Selection
            ui.draw_text("1. Select Equipment Type:", self.x + 30, self.y + 92, font_size=13, color=GraphicsConfig.COLOR_TEXT_PRIMARY)

            # Section 2: Unit Slot Selection
            ui.draw_text("2. Target Rack Slot (U1 - U42):", self.x + 30, self.y + 165, font_size=13, color=GraphicsConfig.COLOR_TEXT_PRIMARY)
            ui.draw_text(f"U{self.selected_u}", self.x + 281, self.y + 192, font_size=18, color=GraphicsConfig.COLOR_PRIMARY_BLUE, center_x=True, center_y=True)

            # Inventory Stock summary
            r_stock = self.inventory.get_count(ItemType.ROUTER)
            sw_stock = self.inventory.get_count(ItemType.SWITCH)
            pc_stock = self.inventory.get_count(ItemType.PC)
            stock_info = f"Available Inventory:   Routers: {r_stock}   |   Switches: {sw_stock}   |   PCs: {pc_stock}"
            ui.draw_rect(self.x + 30, self.y + 225, self.w - 60, 42, (241, 245, 249), alpha=1.0, corner_radius=6.0)
            ui.draw_text(stock_info, self.x + 45, self.y + 246, font_size=13, color=GraphicsConfig.COLOR_TEXT_MUTED, center_y=True)

        # Status or error message
        if self.status_message:
            msg_col = GraphicsConfig.COLOR_DANGER_RED if self.status_is_error else GraphicsConfig.COLOR_SUCCESS_GREEN
            ui.draw_text(self.status_message, self.x + 30, self.y + self.h - 85, font_size=13, color=msg_col)

        # Render all buttons
        for btn in self.buttons:
            btn.render(ui)

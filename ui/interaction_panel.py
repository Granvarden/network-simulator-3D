"""Interactive Rack and Device modal panel for Install, Remove, CLI, and Cabling."""

from typing import Callable, List, Optional, Tuple
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
from player.interaction import InteractionTarget
from .widgets.button import Button
from .widgets.panel import Panel


class InteractionPanel:
    """Modal interaction dialog for managing racks, installing/removing hardware, and cables."""

    def __init__(
        self,
        inventory: Inventory,
        cable_manager: CableManager,
        on_open_cli: Callable[[Device], None],
        on_close: Callable[[], None],
        screen_w: int = GameConfig.WINDOW_WIDTH,
        screen_h: int = GameConfig.WINDOW_HEIGHT
    ):
        self.inventory: Inventory = inventory
        self.cable_manager: CableManager = cable_manager
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

        # Cabling sub-selection
        self.selected_port_name: Optional[str] = None
        self.selected_remote_device_id: Optional[str] = None
        self.selected_remote_port_name: Optional[str] = None

        # Feedback message & status
        self.status_message: str = ""
        self.status_is_error: bool = False

        # Panel Geometry
        self.w = 640
        self.h = 560
        self.x = (screen_w - self.w) / 2.0
        self.y = (screen_h - self.h) / 2.0
        self.panel = Panel(self.x, self.y, self.w, self.h, corner_radius=14.0)

        # Interactive Buttons
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
        """Configure modal for the specific target."""
        self.target = target
        self.target_rack = target.rack
        self.target_device = target.device
        self.selected_u = target.targeted_u or 1
        self.status_message = ""
        self.status_is_error = False
        self.selected_port_name = None
        self._rebuild_buttons()

    def _rebuild_buttons(self) -> None:
        self.buttons.clear()

        # Close button at bottom right
        self.close_btn = Button(
            self.x + self.w - 140, self.y + self.h - 52, 120, 38,
            "Done",
            on_click=self.on_close,
            is_primary=True
        )
        self.buttons.append(self.close_btn)

        if self.target_device:
            # Device is selected: Open CLI, Remove Device
            btn_w = 260
            self.cli_btn = Button(
                self.x + 30, self.y + 110, btn_w, 42,
                "Open CLI Console",
                on_click=self._handle_open_cli,
                is_primary=True
            )
            self.buttons.append(self.cli_btn)

            self.remove_btn = Button(
                self.x + 310, self.y + 110, btn_w, 42,
                "Remove from Rack",
                on_click=self._handle_remove_device
            )
            self.buttons.append(self.remove_btn)

        elif self.target_rack:
            # Empty rack slot selected: Install options
            # Equipment selector buttons
            dev_types = [("Router", "Router (2U)"), ("Switch", "Switch (1U)"), ("PC", "PC Host (2U)")]
            bx = self.x + 30
            for dt, label in dev_types:
                is_sel = (self.selected_device_type == dt)
                btn = Button(
                    bx, self.y + 130, 180, 40,
                    label,
                    on_click=lambda t=dt: self._set_device_type(t),
                    is_primary=is_sel
                )
                self.buttons.append(btn)
                bx += 195

            # U selector buttons (- and +)
            self.u_minus_btn = Button(
                self.x + 220, self.y + 200, 44, 36, "-",
                on_click=self._decrement_u
            )
            self.u_plus_btn = Button(
                self.x + 360, self.y + 200, 44, 36, "+",
                on_click=self._increment_u
            )
            self.buttons.append(self.u_minus_btn)
            self.buttons.append(self.u_plus_btn)

            # Install button
            self.install_btn = Button(
                self.x + 30, self.y + 265, self.w - 60, 46,
                f"Install {self.selected_device_type} into {self.target_rack.rack_id} [Slot U{self.selected_u}]",
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

    def _handle_open_cli(self) -> None:
        if self.target_device:
            self.on_open_cli(self.target_device)

    def _handle_install_device(self) -> None:
        if not self.target_rack:
            return

        # 1. Check Inventory
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

        # 2. Instantiate Device
        new_dev = DeviceFactory.create_device(self.selected_device_type)

        # 3. Check Rack Occupancy
        success, msg = self.target_rack.install_device(new_dev, self.selected_u)
        if success:
            self.inventory.remove_item(item_type, 1)
            self.target_device = new_dev
            self.status_message = msg
            self.status_is_error = False
            self._rebuild_buttons()
        else:
            self.status_message = f"Cannot install: {msg}"
            self.status_is_error = True

    def _handle_remove_device(self) -> None:
        if not self.target_rack or not self.target_device:
            return

        dev = self.target_device
        # Remove and reclaim inventory
        item_map = {
            "Router": ItemType.ROUTER,
            "Switch": ItemType.SWITCH,
            "PC": ItemType.PC,
        }
        item_type = item_map.get(dev.device_type)

        success, msg = self.target_rack.remove_device(dev)
        if success:
            if item_type:
                self.inventory.add_item(item_type, 1)
            self.target_device = None
            self.status_message = f"Device removed. Returned to Inventory."
            self.status_is_error = False
            self._rebuild_buttons()
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
        ui.draw_rect(0, 0, self.screen_w, self.screen_h, (15, 23, 42), alpha=0.55)

        # Panel Card
        self.panel.render(ui)

        # Title
        title_text = f"Rack Manager - {self.target_rack.rack_id}" if self.target_rack else "Hardware Manager"
        ui.draw_text(title_text, self.x + 30, self.y + 35, font_size=22, color=GraphicsConfig.COLOR_TEXT_PRIMARY)

        # Subtitle
        if self.target_device:
            sub = f"Target Device: {self.target_device.hostname} ({self.target_device.device_type}) at U{self.target_device.start_u}-U{self.target_device.start_u + self.target_device.u_height - 1}"
        else:
            sub = f"Target Position: Slot U{self.selected_u} (Available)"
        ui.draw_text(sub, self.x + 30, self.y + 70, font_size=14, color=GraphicsConfig.COLOR_TEXT_MUTED)

        # Render status message if any
        if self.status_message:
            msg_color = GraphicsConfig.COLOR_DANGER_RED if self.status_is_error else GraphicsConfig.COLOR_SUCCESS_GREEN
            ui.draw_text(self.status_message, self.x + 30, self.y + self.h - 40, font_size=13, color=msg_color)

        if not self.target_device and self.target_rack:
            # Installation Instructions & U-position display
            ui.draw_text("1. Choose Equipment Type:", self.x + 30, self.y + 105, font_size=14, color=GraphicsConfig.COLOR_TEXT_PRIMARY)
            ui.draw_text("2. Select Target U Position (1 - 42):", self.x + 30, self.y + 185, font_size=14, color=GraphicsConfig.COLOR_TEXT_PRIMARY)

            # Center slot display between - and + buttons
            ui.draw_text(f"U{self.selected_u}", self.x + 312, self.y + 218, font_size=18, color=GraphicsConfig.COLOR_PRIMARY_BLUE, center_x=True, center_y=True)

            # Available stock summary
            r_stock = self.inventory.get_count(ItemType.ROUTER)
            sw_stock = self.inventory.get_count(ItemType.SWITCH)
            pc_stock = self.inventory.get_count(ItemType.PC)
            stock_info = f"Inventory Stock:  Routers: {r_stock}   Switches: {sw_stock}   PCs: {pc_stock}"
            ui.draw_text(stock_info, self.x + 30, self.y + 330, font_size=13, color=GraphicsConfig.COLOR_TEXT_MUTED)

        elif self.target_device:
            # Device Status Summary Card inside modal
            dev_card_y = self.y + 180
            ui.draw_rect(self.x + 30, dev_card_y, self.w - 60, 180, (248, 250, 252), alpha=1.0, corner_radius=8.0)
            ui.draw_rect_outline(self.x + 30, dev_card_y, self.w - 60, 180, GraphicsConfig.COLOR_CARD_BORDER, line_width=1.0)

            ui.draw_text("Hardware Status & Port Overview:", self.x + 45, dev_card_y + 20, font_size=14, color=GraphicsConfig.COLOR_TEXT_PRIMARY)
            ui.draw_text(f"Power State: {'POWER ON' if self.target_device.power_state else 'OFF'}", self.x + 45, dev_card_y + 45, font_size=13, color=GraphicsConfig.COLOR_SUCCESS_GREEN)

            # Port summary
            port_y = dev_card_y + 75
            shown_ports = list(self.target_device.ports.values())[:6]
            for p in shown_ports:
                c_str = f"Connected to {p.connected_port.device_ref.hostname}:{p.connected_port.port_name}" if p.connected_port and p.connected_port.device_ref else "No Cable"
                p_info = f"{p.port_name:<8} [Admin: {p.admin_status.value.upper()} | Link: {p.link_status.value.upper()}] - {c_str}"
                p_color = GraphicsConfig.COLOR_SUCCESS_GREEN if p.is_operational else (140, 150, 165)
                ui.draw_text(p_info, self.x + 45, port_y, font_size=12, color=p_color)
                port_y += 20

            if len(self.target_device.ports) > 6:
                ui.draw_text(f"... and {len(self.target_device.ports) - 6} more ports (manage in CLI)", self.x + 45, port_y + 4, font_size=11, color=GraphicsConfig.COLOR_TEXT_MUTED)

        # Render all action buttons
        for btn in self.buttons:
            btn.render(ui)

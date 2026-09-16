"""Inventory UI Overlay modal."""

from typing import Callable
import pygame
from config.game_config import GameConfig
from config.graphics_config import GraphicsConfig
from rendering.ui_renderer import UIRenderer
from inventory.inventory import Inventory
from inventory.item import ItemType
from .widgets.panel import Panel
from .widgets.button import Button


class InventoryUI:
    """Displays equipment stock when engineer presses TAB."""

    def __init__(
        self,
        inventory: Inventory,
        on_close: Callable[[], None],
        screen_w: int = GameConfig.WINDOW_WIDTH,
        screen_h: int = GameConfig.WINDOW_HEIGHT
    ):
        self.inventory: Inventory = inventory
        self.on_close: Callable[[], None] = on_close
        self.screen_w = screen_w
        self.screen_h = screen_h

        self.w = 540
        self.h = 420
        self.x = (screen_w - self.w) / 2.0
        self.y = (screen_h - self.h) / 2.0

        self.panel = Panel(self.x, self.y, self.w, self.h, corner_radius=14.0)
        self.close_btn = Button(
            self.x + self.w - 140, self.y + self.h - 50, 110, 36,
            "Close",
            on_click=self.on_close,
            is_primary=True
        )

    def resize(self, width: int, height: int) -> None:
        self.screen_w = width
        self.screen_h = height
        self.x = (width - self.w) / 2.0
        self.y = (height - self.h) / 2.0
        self.panel.x = self.x
        self.panel.y = self.y
        self.close_btn.x = self.x + self.w - 140
        self.close_btn.y = self.y + self.h - 50

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN and (event.key == pygame.K_TAB or event.key == pygame.K_ESCAPE):
            self.on_close()
            return True

        return self.close_btn.handle_event(event)

    def render(self, ui: UIRenderer) -> None:
        # Dim background
        ui.draw_rect(0, 0, self.screen_w, self.screen_h, (15, 23, 42), alpha=0.5)

        self.panel.render(ui)

        # Header
        ui.draw_text("Engineer Equipment Inventory", self.x + 30, self.y + 35, font_size=20, color=GraphicsConfig.COLOR_TEXT_PRIMARY)
        ui.draw_text("Hardware stock available for rack mounting and patching", self.x + 30, self.y + 65, font_size=13, color=GraphicsConfig.COLOR_TEXT_MUTED)

        # Items List
        items = [
            (ItemType.ROUTER, "Modular Enterprise Router (2U)", "Dual Gigabit interfaces, Cisco IOS capable"),
            (ItemType.SWITCH, "Managed Access Switch (1U)", "24 Gigabit ports, dynamic MAC table & VLANs"),
            (ItemType.PC, "Workstation PC Host (2U)", "Network station with NIC, Windows CMD prompt"),
            (ItemType.ETHERNET_CABLE, "Cat6 Ethernet Patch Cables", "High-speed UTP patch cables with RJ45 plugs"),
        ]

        curr_y = self.y + 110
        for itype, title, desc in items:
            count = self.inventory.get_count(itype)

            # Item row card
            ui.draw_rect(self.x + 30, curr_y, self.w - 60, 52, (248, 250, 252), alpha=1.0, corner_radius=8.0)
            ui.draw_rect_outline(self.x + 30, curr_y, self.w - 60, 52, GraphicsConfig.COLOR_CARD_BORDER, line_width=1.0)

            # Item name & desc
            ui.draw_text(title, self.x + 45, curr_y + 16, font_size=14, color=GraphicsConfig.COLOR_TEXT_PRIMARY)
            ui.draw_text(desc, self.x + 45, curr_y + 34, font_size=11, color=GraphicsConfig.COLOR_TEXT_MUTED)

            # Stock quantity badge
            badge_w, badge_h = 60, 26
            bx = self.x + self.w - 105
            by = curr_y + (52 - badge_h) / 2.0
            ui.draw_rect(bx, by, badge_w, badge_h, (238, 242, 255), alpha=1.0, corner_radius=6.0)
            ui.draw_rect_outline(bx, by, badge_w, badge_h, (199, 210, 254), line_width=1.0)
            ui.draw_text(f"x {count}", bx + badge_w / 2.0, by + badge_h / 2.0, font_size=13, color=GraphicsConfig.COLOR_PRIMARY_BLUE, center_x=True, center_y=True)

            curr_y += 62

        self.close_btn.render(ui)

"""Modern Light Theme Main Menu."""

from typing import Callable, List, Optional
import pygame
from config.game_config import GameConfig
from config.graphics_config import GraphicsConfig
from rendering.ui_renderer import UIRenderer
from .widgets.button import Button
from .widgets.panel import Panel
from .widgets.slider import Slider


class MainMenuUI:
    """Modern Light Theme Main Menu interface."""

    def __init__(
        self,
        on_start_sandbox: Callable[[], None],
        on_exit: Callable[[], None]
    ):
        self.on_start_sandbox = on_start_sandbox
        self.on_exit = on_exit

        self.screen_w = GameConfig.WINDOW_WIDTH
        self.screen_h = GameConfig.WINDOW_HEIGHT

        # Modal settings toggle
        self.show_settings: bool = False

        self._build_ui()

    def _build_ui(self) -> None:
        """Create panels and buttons with responsive centering."""
        card_w, card_h = 480, 520
        card_x = (self.screen_w - card_w) / 2.0
        card_y = (self.screen_h - card_h) / 2.0 + 30

        self.panel = Panel(card_x, card_y, card_w, card_h, corner_radius=16.0)

        # Buttons inside the card
        btn_w, btn_h = 400, 52
        btn_x = card_x + (card_w - btn_w) / 2.0
        start_y = card_y + 130
        spacing = 68

        self.buttons: List[Button] = [
            Button(
                btn_x, start_y, btn_w, btn_h,
                "SANDBOX MODE",
                on_click=self.on_start_sandbox,
                is_primary=True
            ),
            Button(
                btn_x, start_y + spacing, btn_w, btn_h,
                "TUTORIAL",
                on_click=None,
                badge_text="Coming Soon",
                enabled=False
            ),
            Button(
                btn_x, start_y + spacing * 2, btn_w, btn_h,
                "CHALLENGES",
                on_click=None,
                badge_text="Coming Soon",
                enabled=False
            ),
            Button(
                btn_x, start_y + spacing * 3, btn_w, btn_h,
                "SETTINGS",
                on_click=self._toggle_settings
            ),
            Button(
                btn_x, start_y + spacing * 4, btn_w, btn_h,
                "EXIT GAME",
                on_click=self.on_exit
            ),
        ]

        # Sensitivity adjustment state
        self.mouse_sensitivity: float = GameConfig.MOUSE_SENSITIVITY

        # Settings Close Button
        self.settings_close_btn = Button(
            (self.screen_w - 180) / 2.0, (self.screen_h / 2.0) + 125, 180, 42,
            "Save & Close",
            on_click=self._toggle_settings,
            is_primary=True
        )

        # Sensitivity Scroll Slider widget
        slider_w = 270
        slider_x = (self.screen_w - 440) / 2.0 + 35
        slider_y = (self.screen_h / 2.0) + 20
        self.sens_slider = Slider(
            x=slider_x,
            y=slider_y,
            w=slider_w,
            h=32,
            min_val=0.05,
            max_val=1.20,
            initial_val=self.mouse_sensitivity,
            step=0.01,
            label="Mouse Sensitivity",
            on_change=self._set_sensitivity
        )

    def resize(self, w: int, h: int) -> None:
        """Handle screen resize."""
        self.screen_w = w
        self.screen_h = h
        self._build_ui()

    def _set_sensitivity(self, val: float) -> None:
        self.mouse_sensitivity = val

    def _toggle_settings(self) -> None:
        self.show_settings = not self.show_settings

    def handle_event(self, event: pygame.event.Event) -> bool:
        if self.show_settings:
            if self.settings_close_btn.handle_event(event):
                return True
            if self.sens_slider.handle_event(event):
                return True
            return False

        for btn in self.buttons:
            if btn.handle_event(event):
                return True
        return False

    def render(self, ui: UIRenderer) -> None:
        # 1. Fullscreen Modern Light Background
        ui.draw_rect(0, 0, self.screen_w, self.screen_h, GraphicsConfig.COLOR_BG_LIGHT, alpha=1.0)

        # Subtle decorative accent bar at very top
        ui.draw_rect(0, 0, self.screen_w, 4, GraphicsConfig.COLOR_PRIMARY_BLUE, alpha=1.0)

        # 2. Main Title & Subtitle Above Card
        ui.draw_text(
            "NETWORK ENGINEER SIMULATOR",
            self.screen_w / 2.0, 75,
            font_size=32,
            color=GraphicsConfig.COLOR_TEXT_PRIMARY,
            center_x=True,
            center_y=True
        )
        ui.draw_text(
            "3D First-Person Network Engineering & Data Center Lab",
            self.screen_w / 2.0, 110,
            font_size=15,
            color=GraphicsConfig.COLOR_TEXT_MUTED,
            center_x=True,
            center_y=True
        )

        # 3. Card Panel
        self.panel.render(ui)

        # Card Header
        ui.draw_text(
            "Select Game Mode",
            self.screen_w / 2.0, self.panel.y + 55,
            font_size=20,
            color=GraphicsConfig.COLOR_TEXT_PRIMARY,
            center_x=True,
            center_y=True
        )
        ui.draw_text(
            "Design, cable, and configure production hardware in Sandbox",
            self.screen_w / 2.0, self.panel.y + 85,
            font_size=13,
            color=GraphicsConfig.COLOR_TEXT_MUTED,
            center_x=True,
            center_y=True
        )

        # 4. Buttons
        for btn in self.buttons:
            btn.render(ui)

        # Version tag in bottom right
        ui.draw_text(
            "v1.0.0 (Phase 1 & Phase 2 Sandbox) | Pygame + PyOpenGL",
            self.screen_w - 20, self.screen_h - 20,
            font_size=12,
            color=(160, 174, 192),
            center_x=False,
            center_y=True
        )

        # 5. Settings Modal Dialog
        if self.show_settings:
            # Dim backdrop
            ui.draw_rect(0, 0, self.screen_w, self.screen_h, (15, 23, 42), alpha=0.45)

            sw, sh = 440, 360
            sx = (self.screen_w - sw) / 2.0
            sy = (self.screen_h - sh) / 2.0
            settings_panel = Panel(sx, sy, sw, sh, corner_radius=12.0)
            settings_panel.render(ui)

            ui.draw_text("Settings", sx + sw / 2.0, sy + 30, font_size=20, color=GraphicsConfig.COLOR_TEXT_PRIMARY, center_x=True)
            ui.draw_text("Display Mode: Maximized Window (Taskbar Visible)", sx + 30, sy + 65, font_size=13, color=GraphicsConfig.COLOR_TEXT_PRIMARY)
            ui.draw_text(f"Resolution: {self.screen_w}x{self.screen_h} (60 FPS VSync)", sx + 30, sy + 90, font_size=13, color=GraphicsConfig.COLOR_TEXT_PRIMARY)
            ui.draw_text(f"Mouse Look Sensitivity: {self.mouse_sensitivity:.2f}", sx + 30, sy + 125, font_size=14, color=GraphicsConfig.COLOR_PRIMARY_BLUE)
            ui.draw_text("Scroll mouse wheel or drag slider to adjust:", sx + 30, sy + 150, font_size=12, color=GraphicsConfig.COLOR_TEXT_MUTED)

            self.sens_slider.render(ui)
            self.settings_close_btn.render(ui)

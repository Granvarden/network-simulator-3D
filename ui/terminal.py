"""Dark theme Terminal UI overlay for CLI interaction."""

import pygame
from typing import Callable, Optional
from config.game_config import GameConfig
from config.graphics_config import GraphicsConfig
from rendering.ui_renderer import UIRenderer
from cli.cli_engine import CLIEngine


class TerminalUI:
    """Renders the Dark Theme Terminal window over the 3D lab."""

    def __init__(
        self,
        cli_engine: CLIEngine,
        on_close: Callable[[], None],
        screen_w: int = GameConfig.WINDOW_WIDTH,
        screen_h: int = GameConfig.WINDOW_HEIGHT
    ):
        self.cli_engine: CLIEngine = cli_engine
        self.on_close: Callable[[], None] = on_close
        self.screen_w = screen_w
        self.screen_h = screen_h

        # Window geometry
        self.w = 980
        self.h = 560
        self.x = (screen_w - self.w) / 2.0
        self.y = (screen_h - self.h) / 2.0

        # Close button rect (top right of titlebar)
        self.close_btn_rect = pygame.Rect(int(self.x + self.w - 36), int(self.y + 6), 28, 24)

    def resize(self, width: int, height: int) -> None:
        self.screen_w = width
        self.screen_h = height
        self.x = (width - self.w) / 2.0
        self.y = (height - self.h) / 2.0
        self.close_btn_rect = pygame.Rect(int(self.x + self.w - 36), int(self.y + 6), 28, 24)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse clicks on close button, ESC to exit, and forward keys to CLIEngine."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.on_close()
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.close_btn_rect.collidepoint(event.pos):
                self.on_close()
                return True

        # Delegate input to CLI Engine
        handled = self.cli_engine.handle_event(event)
        # Check if user typed exit and got disconnected
        if self.cli_engine.scrollback and "% Disconnected" in self.cli_engine.scrollback[-1]:
            self.on_close()
            return True
        return handled

    def update(self, dt: float) -> None:
        self.cli_engine.update(dt)

    def render(self, ui: UIRenderer) -> None:
        # 1. Dark Backdrop Dimmer
        ui.draw_rect(0, 0, self.screen_w, self.screen_h, (10, 15, 25), alpha=0.65)

        # 2. Main Terminal Window Frame (Drop shadow + rounded card)
        ui.draw_rect(self.x + 4, self.y + 8, self.w, self.h, (0, 0, 0), alpha=0.35, corner_radius=10.0)
        ui.draw_rect(self.x, self.y, self.w, self.h, GraphicsConfig.COLOR_TERM_BG, alpha=0.98, corner_radius=10.0)
        ui.draw_rect_outline(self.x, self.y, self.w, self.h, GraphicsConfig.COLOR_TERM_BORDER, line_width=1.5)

        # 3. Terminal Titlebar
        title_h = 36
        ui.draw_rect(self.x, self.y, self.w, title_h, (28, 33, 45), alpha=1.0, corner_radius=10.0)
        # Flatten bottom corners of titlebar
        ui.draw_rect(self.x, self.y + title_h - 4, self.w, 4, (28, 33, 45), alpha=1.0)
        ui.draw_rect_outline(self.x, self.y, self.w, title_h, GraphicsConfig.COLOR_TERM_BORDER, line_width=1.0)

        # Title Text
        dev_name = self.cli_engine.active_device.hostname if self.cli_engine.active_device else "Console"
        dev_type = self.cli_engine.active_device.device_type if self.cli_engine.active_device else "Serial"
        title_str = f"Console Session - [{dev_name}] ({dev_type} Virtual Terminal)"
        ui.draw_text(title_str, self.x + 16, self.y + title_h / 2.0, font_size=14, color=(200, 215, 230), center_y=True)

        # Close Button [X]
        cb = self.close_btn_rect
        ui.draw_rect(cb.x, cb.y, cb.w, cb.h, (220, 50, 50), alpha=0.85, corner_radius=4.0)
        ui.draw_text("X", cb.x + cb.w / 2.0, cb.y + cb.h / 2.0, font_size=13, color=(255, 255, 255), center_x=True, center_y=True)

        # 4. Scrollback Lines
        line_height = 20
        content_x = self.x + 16
        content_y = self.y + title_h + 12
        max_visible_lines = int((self.h - title_h - 48) / line_height)

        visible_lines = self.cli_engine.scrollback[-max_visible_lines:] if len(self.cli_engine.scrollback) > max_visible_lines else self.cli_engine.scrollback

        curr_y = content_y
        for line in visible_lines:
            # Color coding output lines
            if line.startswith("%"):
                color = GraphicsConfig.COLOR_TERM_ERROR
            elif "Reply from" in line:
                color = GraphicsConfig.COLOR_TERM_SUCCESS
            elif line.startswith("!"):
                color = (120, 140, 160)
            else:
                color = GraphicsConfig.COLOR_TERM_TEXT

            ui.draw_text(line, content_x, curr_y, font_size=14, color=color)
            curr_y += line_height

        # 5. Active Command Input Line with Prompt and Blinking Cursor
        prompt = self.cli_engine.get_prompt()
        prompt_w, _ = ui.draw_text(prompt, content_x, curr_y, font_size=14, color=GraphicsConfig.COLOR_TERM_PROMPT)

        inp_text = self.cli_engine.input_buffer
        text_before_cursor = inp_text[:self.cli_engine.cursor_pos]
        tb_w, _ = ui.draw_text(inp_text, content_x + prompt_w + 6, curr_y, font_size=14, color=GraphicsConfig.COLOR_TERM_TEXT)

        # Blinking Cursor
        if self.cli_engine.cursor_visible:
            cursor_x = content_x + prompt_w + 6 + len(text_before_cursor) * 8.2
            ui.draw_rect(cursor_x, curr_y + 2, 8, 15, (56, 189, 248), alpha=0.9)

"""In-Game Heads-Up Display (HUD) overlay."""

from typing import Optional
from config.game_config import GameConfig
from config.graphics_config import GraphicsConfig
from rendering.ui_renderer import UIRenderer
from player.interaction import InteractionTarget


class HUD:
    """Renders top status bar, crosshair, interaction hints, and control badges."""

    def __init__(self, screen_w: int = GameConfig.WINDOW_WIDTH, screen_h: int = GameConfig.WINDOW_HEIGHT):
        self.screen_w = screen_w
        self.screen_h = screen_h

    def resize(self, width: int, height: int) -> None:
        self.screen_w = width
        self.screen_h = height

    def render(
        self,
        ui: UIRenderer,
        fps: float,
        target: InteractionTarget,
        network_status: str = "ONLINE"
    ) -> None:
        # 1. Top Modern Status Bar
        bar_h = 44
        ui.draw_rect(0, 0, self.screen_w, bar_h, (255, 255, 255), alpha=0.92)
        ui.draw_rect_outline(0, 0, self.screen_w, bar_h, GraphicsConfig.COLOR_CARD_BORDER, line_width=1.0)
        ui.draw_rect(0, bar_h - 2, self.screen_w, 2, GraphicsConfig.COLOR_PRIMARY_BLUE, alpha=1.0)

        # Left Badges: Mode & Lab status
        ui.draw_text("MODE: SANDBOX", 24, bar_h / 2.0, font_size=14, color=GraphicsConfig.COLOR_PRIMARY_BLUE, center_y=True)
        ui.draw_text("|", 155, bar_h / 2.0, font_size=14, color=GraphicsConfig.COLOR_CARD_BORDER, center_y=True)
        ui.draw_text("LOCATION: DATA CENTER LAB 01", 175, bar_h / 2.0, font_size=14, color=GraphicsConfig.COLOR_TEXT_MUTED, center_y=True)

        # Center: Looking target summary
        if target.target_type != "NONE":
            target_text = f"TARGET: {target.interactable.name if target.interactable else 'None'}"
            if target.targeted_u:
                target_text += f" [U{target.targeted_u}]"
            ui.draw_text(target_text, self.screen_w / 2.0, bar_h / 2.0, font_size=14, color=GraphicsConfig.COLOR_TEXT_PRIMARY, center_x=True, center_y=True)

        # Right: Network Status & FPS
        fps_str = f"FPS: {int(fps)}"
        ui.draw_text(f"NET: {network_status}", self.screen_w - 150, bar_h / 2.0, font_size=14, color=GraphicsConfig.COLOR_SUCCESS_GREEN, center_y=True)
        ui.draw_text(fps_str, self.screen_w - 70, bar_h / 2.0, font_size=14, color=GraphicsConfig.COLOR_TEXT_MUTED, center_y=True)

        # 2. Crosshair in Screen Center
        cx = self.screen_w / 2.0
        cy = self.screen_h / 2.0
        ch_size = 6.0
        ch_color = (37, 99, 235) if target.target_type != "NONE" else (160, 174, 192)
        # Horizontal & Vertical lines
        ui.draw_rect(cx - ch_size, cy - 1, ch_size * 2 + 1, 2, ch_color, alpha=0.9)
        ui.draw_rect(cx - 1, cy - ch_size, 2, ch_size * 2 + 1, ch_color, alpha=0.9)

        # 3. Dynamic Interaction Tooltip below Crosshair
        if target.target_type != "NONE" and target.hint_text:
            hint_w = max(260, len(target.hint_text) * 8 + 40)
            hint_h = 36
            hx = cx - hint_w / 2.0
            hy = cy + 30
            # Modern floating pill tooltip
            ui.draw_rect(hx, hy, hint_w, hint_h, (255, 255, 255), alpha=0.96, corner_radius=18.0)
            ui.draw_rect_outline(hx, hy, hint_w, hint_h, GraphicsConfig.COLOR_PRIMARY_BLUE, line_width=1.5)
            ui.draw_text(target.hint_text, cx, hy + hint_h / 2.0, font_size=14, color=GraphicsConfig.COLOR_PRIMARY_BLUE, center_x=True, center_y=True)

        # 4. Bottom Controls Bar
        bot_h = 32
        bot_y = self.screen_h - bot_h
        ui.draw_rect(0, bot_y, self.screen_w, bot_h, (255, 255, 255), alpha=0.88)
        ui.draw_rect_outline(0, bot_y, self.screen_w, bot_h, GraphicsConfig.COLOR_CARD_BORDER, line_width=1.0)

        hints = "[WASD] Move   [SHIFT] Sprint   [SPACE] Jump   [E] Interact / Rack Actions   [TAB] Inventory   [F3] Debug   [ESC] Menu"
        ui.draw_text(hints, self.screen_w / 2.0, bot_y + bot_h / 2.0, font_size=13, color=GraphicsConfig.COLOR_TEXT_PRIMARY, center_x=True, center_y=True)

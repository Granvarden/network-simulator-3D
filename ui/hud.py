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
        network_status: str = "ONLINE",
        mode: str = "CABLING_CLI",
        held_cable_port: Optional[object] = None
    ) -> None:
        # 1. Top Modern Status Bar
        bar_h = 44
        ui.draw_rect(0, 0, self.screen_w, bar_h, (255, 255, 255), alpha=0.92)
        ui.draw_rect_outline(0, 0, self.screen_w, bar_h, GraphicsConfig.COLOR_CARD_BORDER, line_width=1.0)
        mode_accent = GraphicsConfig.COLOR_PRIMARY_BLUE if mode == "CABLING_CLI" else (217, 119, 6)
        ui.draw_rect(0, bar_h - 2, self.screen_w, 2, mode_accent, alpha=1.0)

        # Left Badges: Mode & Lab status
        mode_text = "[R] MODE: CABLING & CLI" if mode == "CABLING_CLI" else "[R] MODE: HARDWARE (ADD/DEL)"
        ui.draw_text(mode_text, 24, bar_h / 2.0, font_size=13, color=mode_accent, center_y=True)
        ui.draw_text("|", 240, bar_h / 2.0, font_size=14, color=GraphicsConfig.COLOR_CARD_BORDER, center_y=True)
        ui.draw_text("LOCATION: DATA CENTER LAB 01", 255, bar_h / 2.0, font_size=13, color=GraphicsConfig.COLOR_TEXT_MUTED, center_y=True)

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

        # Active Held Cable Floating Banner
        if held_cable_port is not None:
            c_dev = getattr(held_cable_port, "device_ref", None)
            c_dev_name = c_dev.hostname if c_dev else "Device"
            c_port_name = getattr(held_cable_port, "port_name", "Port")
            cable_banner = f"Connecting Cable from {c_dev_name}:{c_port_name} -> Aim at target port and press [F] | [ESC] Cancel"
            cb_w = max(380, len(cable_banner) * 8 + 30)
            cb_h = 32
            cb_x = self.screen_w / 2.0 - cb_w / 2.0
            cb_y = bar_h + 10
            ui.draw_rect(cb_x, cb_y, cb_w, cb_h, (15, 23, 42), alpha=0.92, corner_radius=16.0)
            ui.draw_rect_outline(cb_x, cb_y, cb_w, cb_h, (250, 204, 21), line_width=1.5)
            ui.draw_text(cable_banner, self.screen_w / 2.0, cb_y + cb_h / 2.0, font_size=12, color=(250, 204, 21), center_x=True, center_y=True)

        # 2. Crosshair in Screen Center
        cx = self.screen_w / 2.0
        cy = self.screen_h / 2.0
        ch_size = 6.0
        if target.target_type == "PORT":
            ch_color = (245, 158, 11)  # Amber for targeted RJ45 port
        elif target.target_type != "NONE":
            ch_color = (37, 99, 235)  # Blue for targeted device
        else:
            ch_color = (160, 174, 192)
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
            ui.draw_rect_outline(hx, hy, hint_w, hint_h, mode_accent, line_width=1.5)
            ui.draw_text(target.hint_text, cx, hy + hint_h / 2.0, font_size=14, color=mode_accent, center_x=True, center_y=True)

        # 4. Bottom Controls Bar
        bot_h = 32
        bot_y = self.screen_h - bot_h
        ui.draw_rect(0, bot_y, self.screen_w, bot_h, (255, 255, 255), alpha=0.88)
        ui.draw_rect_outline(0, bot_y, self.screen_w, bot_h, GraphicsConfig.COLOR_CARD_BORDER, line_width=1.0)

        if mode == "CABLING_CLI":
            hints = "[WASD] Move   [R] Switch to Hardware Mode   [E] Open CLI   [F] Plug/Unplug Cable   [TAB] Inventory   [ESC] Menu"
        else:
            hints = "[WASD] Move   [R] Switch to Cabling Mode   [E] Install / Remove Device   [TAB] Inventory   [ESC] Menu"

        ui.draw_text(hints, self.screen_w / 2.0, bot_y + bot_h / 2.0, font_size=13, color=GraphicsConfig.COLOR_TEXT_PRIMARY, center_x=True, center_y=True)

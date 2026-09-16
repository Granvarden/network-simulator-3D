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
        bar_h = 50
        ui.draw_rect(0, 0, self.screen_w, bar_h, (255, 255, 255), alpha=0.94)
        ui.draw_rect_outline(0, 0, self.screen_w, bar_h, GraphicsConfig.COLOR_CARD_BORDER, line_width=1.0)
        mode_accent = GraphicsConfig.COLOR_PRIMARY_BLUE if mode == "CABLING_CLI" else (217, 119, 6)
        ui.draw_rect(0, bar_h - 2, self.screen_w, 2, mode_accent, alpha=1.0)

        # Left Badges: Mode & Lab status
        mode_text = "[R] MODE: CABLING & CLI" if mode == "CABLING_CLI" else "[R] MODE: HARDWARE (ADD/DEL)"
        ui.draw_text(mode_text, 24, bar_h / 2.0, font_size=15, color=mode_accent, center_y=True)
        ui.draw_text("|", 260, bar_h / 2.0, font_size=15, color=GraphicsConfig.COLOR_CARD_BORDER, center_y=True)
        ui.draw_text("LOCATION: DATA CENTER LAB 01", 275, bar_h / 2.0, font_size=14, color=GraphicsConfig.COLOR_TEXT_MUTED, center_y=True)

        # Center: Looking target summary
        if target.target_type != "NONE":
            target_text = f"TARGET: {target.interactable.name if target.interactable else 'None'}"
            if target.targeted_u:
                target_text += f" [U{target.targeted_u}]"
            ui.draw_text(target_text, self.screen_w / 2.0, bar_h / 2.0, font_size=16, color=GraphicsConfig.COLOR_TEXT_PRIMARY, center_x=True, center_y=True)

        # Right: Network Status & FPS
        fps_str = f"FPS: {int(fps)}"
        ui.draw_text(f"NET: {network_status}", self.screen_w - 170, bar_h / 2.0, font_size=15, color=GraphicsConfig.COLOR_SUCCESS_GREEN, center_y=True)
        ui.draw_text(fps_str, self.screen_w - 80, bar_h / 2.0, font_size=15, color=GraphicsConfig.COLOR_TEXT_MUTED, center_y=True)

        # Active Held Cable Floating Banner
        if held_cable_port is not None:
            c_dev = getattr(held_cable_port, "device_ref", None)
            c_dev_name = c_dev.hostname if c_dev else "Device"
            c_port_name = getattr(held_cable_port, "port_name", "Port")
            cable_banner = f"Connecting Cable from {c_dev_name}:{c_port_name} -> Aim at target port and press [F] | [ESC] Cancel"
            cb_w = max(420, len(cable_banner) * 9 + 40)
            cb_h = 36
            cb_x = self.screen_w / 2.0 - cb_w / 2.0
            cb_y = bar_h + 12
            ui.draw_rect(cb_x, cb_y, cb_w, cb_h, (15, 23, 42), alpha=0.94, corner_radius=18.0)
            ui.draw_rect_outline(cb_x, cb_y, cb_w, cb_h, (250, 204, 21), line_width=1.5)
            ui.draw_text(cable_banner, self.screen_w / 2.0, cb_y + cb_h / 2.0, font_size=14, color=(250, 204, 21), center_x=True, center_y=True)

        # 2. Modern Tactical Corner-Bracket Reticle in Screen Center (Matching User Design)
        cx = round(self.screen_w / 2.0)
        cy = round(self.screen_h / 2.0)
        box_r = 14.0  # half size of 28x28 square frame
        arm = 6.0     # bracket arm length
        th = 2.0      # line thickness

        if target.target_type == "PORT":
            ret_col = (245, 158, 11)   # Glowing amber for RJ45 port
            alpha = 1.0
        elif target.target_type != "NONE":
            ret_col = (37, 99, 235)    # Vibrant Royal Blue for targeted device
            alpha = 1.0
        else:
            ret_col = (59, 130, 246)   # Tactical blue matching reference image
            alpha = 0.85

        # Top-Left Bracket ┌
        ui.draw_rect(cx - box_r, cy - box_r, arm, th, ret_col, alpha=alpha)
        ui.draw_rect(cx - box_r, cy - box_r, th, arm, ret_col, alpha=alpha)

        # Top-Right Bracket ┐
        ui.draw_rect(cx + box_r - arm, cy - box_r, arm, th, ret_col, alpha=alpha)
        ui.draw_rect(cx + box_r - th, cy - box_r, th, arm, ret_col, alpha=alpha)

        # Bottom-Left Bracket └
        ui.draw_rect(cx - box_r, cy + box_r - th, arm, th, ret_col, alpha=alpha)
        ui.draw_rect(cx - box_r, cy + box_r - arm, th, arm, ret_col, alpha=alpha)

        # Bottom-Right Bracket ┘
        ui.draw_rect(cx + box_r - arm, cy + box_r - th, arm, th, ret_col, alpha=alpha)
        ui.draw_rect(cx + box_r - th, cy + box_r - arm, th, arm, ret_col, alpha=alpha)

        # Center Reticle Plus / Diamond (+)
        ui.draw_rect(cx - 2.5, cy - 1.0, 5.0, 2.0, ret_col, alpha=alpha)
        ui.draw_rect(cx - 1.0, cy - 2.5, 2.0, 5.0, ret_col, alpha=alpha)

        # 3. Dynamic Interaction Tooltip below Crosshair
        if target.target_type != "NONE" and target.hint_text:
            hint_w = max(280, len(target.hint_text) * 9 + 44)
            hint_h = 42
            hx = cx - hint_w / 2.0
            hy = cy + 34
            # Modern floating pill tooltip
            ui.draw_rect(hx, hy, hint_w, hint_h, (255, 255, 255), alpha=0.96, corner_radius=21.0)
            ui.draw_rect_outline(hx, hy, hint_w, hint_h, mode_accent, line_width=1.5)
            ui.draw_text(target.hint_text, cx, hy + hint_h / 2.0, font_size=16, color=mode_accent, center_x=True, center_y=True)

        # 4. Bottom Controls Bar
        bot_h = 36
        bot_y = self.screen_h - bot_h
        ui.draw_rect(0, bot_y, self.screen_w, bot_h, (255, 255, 255), alpha=0.92)
        ui.draw_rect_outline(0, bot_y, self.screen_w, bot_h, GraphicsConfig.COLOR_CARD_BORDER, line_width=1.0)

        if mode == "CABLING_CLI":
            hints = "[WASD] Move   [R] Switch to Hardware Mode   [E] Open CLI   [F] Plug/Unplug Cable   [TAB] Inventory   [ESC] Menu"
        else:
            hints = "[WASD] Move   [R] Switch to Cabling Mode   [E] Install / Remove Device   [TAB] Inventory   [ESC] Menu"

        ui.draw_text(hints, self.screen_w / 2.0, bot_y + bot_h / 2.0, font_size=15, color=GraphicsConfig.COLOR_TEXT_PRIMARY, center_x=True, center_y=True)

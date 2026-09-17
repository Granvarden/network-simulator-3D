"""In-Game Heads-Up Display (HUD) overlay."""

from typing import Optional, Tuple
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
        held_cable_port: Optional[object] = None,
        held_cable_color_name: Optional[str] = None,
        held_cable_color_rgb: Optional[Tuple[float, float, float]] = None
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
            col_label = f" [Color: {held_cable_color_name or 'Blue'} | Scroll to change]"
            cable_banner = f"Cabling from {c_dev_name}:{c_port_name}{col_label} -> [F] Connect | [R-Click] Cancel"
            cb_w = max(480, len(cable_banner) * 8.5 + 40)
            cb_h = 36
            cb_x = self.screen_w / 2.0 - cb_w / 2.0
            cb_y = bar_h + 12
            ui.draw_rect(cb_x, cb_y, cb_w, cb_h, (15, 23, 42), alpha=0.94, corner_radius=18.0)
            border_col = (
                (int(held_cable_color_rgb[0] * 255), int(held_cable_color_rgb[1] * 255), int(held_cable_color_rgb[2] * 255))
                if held_cable_color_rgb else (56, 189, 248)
            )
            ui.draw_rect_outline(cb_x, cb_y, cb_w, cb_h, border_col, line_width=2.0)
            ui.draw_text(cable_banner, self.screen_w / 2.0, cb_y + cb_h / 2.0, font_size=14, color=(241, 245, 249), center_x=True, center_y=True)


        # 2. Sleek Tactical Corner-Bracket Reticle in Screen Center (Matching User Reference Image)
        cx = round(self.screen_w / 2.0)
        cy = round(self.screen_h / 2.0)
        box_r = 11.0  # compact 22x22 square frame
        arm = 5.0     # elegant bracket arm length
        th = 1.8      # crisp, sleek line thickness

        if target.target_type == "PORT":
            ret_col = (245, 158, 11)   # Radiant Amber for RJ45 port
        elif target.target_type != "NONE":
            ret_col = (37, 99, 235)    # Vibrant Royal Blue for targeted device
        else:
            ret_col = (56, 189, 248)   # Crisp Tactical Sky Blue matching reference image

        # Clean subtle drop shadow for readability against white walls/lights without bulkiness
        shadow_col = (15, 23, 42)
        shadow_alpha = 0.40

        def draw_bracket_bar(bx: float, by: float, bw: float, bh: float):
            ui.draw_rect(bx + 0.8, by + 0.8, bw, bh, shadow_col, alpha=shadow_alpha)
            ui.draw_rect(bx, by, bw, bh, ret_col, alpha=0.95)

        # Top-Left Bracket ┌
        draw_bracket_bar(cx - box_r, cy - box_r, arm, th)
        draw_bracket_bar(cx - box_r, cy - box_r, th, arm)

        # Top-Right Bracket ┐
        draw_bracket_bar(cx + box_r - arm, cy - box_r, arm, th)
        draw_bracket_bar(cx + box_r - th, cy - box_r, th, arm)

        # Bottom-Left Bracket └
        draw_bracket_bar(cx - box_r, cy + box_r - th, arm, th)
        draw_bracket_bar(cx - box_r, cy + box_r - arm, th, arm)

        # Bottom-Right Bracket ┘
        draw_bracket_bar(cx + box_r - arm, cy + box_r - th, arm, th)
        draw_bracket_bar(cx + box_r - th, cy + box_r - arm, th, arm)

        # Center Aiming Reticle Diamond (✦) - The EXACT focal point of the raycast
        draw_bracket_bar(cx - 2.5, cy - 0.75, 5.0, 1.5)
        draw_bracket_bar(cx - 0.75, cy - 2.5, 1.5, 5.0)
        draw_bracket_bar(cx - 1.0, cy - 1.0, 2.0, 2.0)

        # 3. Bottom Controls Bar
        bot_h = 36
        bot_y = self.screen_h - bot_h
        ui.draw_rect(0, bot_y, self.screen_w, bot_h, (255, 255, 255), alpha=0.92)
        ui.draw_rect_outline(0, bot_y, self.screen_w, bot_h, GraphicsConfig.COLOR_CARD_BORDER, line_width=1.0)

        if mode == "CABLING_CLI":
            hints = "[WASD] Move   [R] Switch to Hardware Mode   [E] Open CLI   [F] Plug/Unplug Cable   [TAB] Inventory   [ESC] Menu"
        else:
            hints = "[WASD] Move   [R] Switch to Cabling Mode   [E] Install / Remove Device   [TAB] Inventory   [ESC] Menu"

        ui.draw_text(hints, self.screen_w / 2.0, bot_y + bot_h / 2.0, font_size=15, color=GraphicsConfig.COLOR_TEXT_PRIMARY, center_x=True, center_y=True)

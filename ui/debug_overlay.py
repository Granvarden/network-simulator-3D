"""Developer Debug HUD Overlay toggled with F3."""

from typing import Any, List
from config.graphics_config import GraphicsConfig
from rendering.ui_renderer import UIRenderer


class DebugOverlay:
    """Displays real-time developer metrics and network link states."""

    def __init__(self):
        self.enabled: bool = False

    def toggle(self) -> None:
        self.enabled = not self.enabled

    def render(
        self,
        ui: UIRenderer,
        fps: float,
        player_pos: tuple,
        device_count: int,
        cable_count: int,
        current_target_info: str,
        operational_links_count: int
    ) -> None:
        if not self.enabled:
            return

        dw, dh = 340, 220
        dx, dy = 16, 56

        # Semi-transparent dark overlay
        ui.draw_rect(dx, dy, dw, dh, (15, 23, 42), alpha=0.88, corner_radius=8.0)
        ui.draw_rect_outline(dx, dy, dw, dh, (56, 189, 248), line_width=1.5)

        ui.draw_text("[F3] ENGINE DEBUG STATS", dx + 12, dy + 18, font_size=13, color=(56, 189, 248))

        px, py, pz = player_pos
        lines = [
            f"FPS: {fps:.1f}",
            f"Player Position: X:{px:.2f} Y:{py:.2f} Z:{pz:.2f}",
            f"Installed Devices: {device_count}",
            f"Active Cables: {cable_count}",
            f"Operational Links: {operational_links_count}",
            f"Target: {current_target_info or 'None'}",
            f"Renderer: Pygame + PyOpenGL 3.1.10",
        ]

        curr_y = dy + 42
        for line in lines:
            ui.draw_text(line, dx + 12, curr_y, font_size=12, color=(241, 245, 249))
            curr_y += 22

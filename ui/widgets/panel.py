"""Modern Card Panel container widget."""

from typing import Tuple
from config.graphics_config import GraphicsConfig
from rendering.ui_renderer import UIRenderer


class Panel:
    """Modern card panel for dialogues and modal containers."""

    def __init__(
        self,
        x: float, y: float, w: float, h: float,
        bg_color: Tuple[int, int, int] = GraphicsConfig.COLOR_CARD_LIGHT,
        border_color: Tuple[int, int, int] = GraphicsConfig.COLOR_CARD_BORDER,
        corner_radius: float = 12.0,
        has_shadow: bool = True
    ):
        self.x: float = x
        self.y: float = y
        self.w: float = w
        self.h: float = h
        self.bg_color: Tuple[int, int, int] = bg_color
        self.border_color: Tuple[int, int, int] = border_color
        self.corner_radius: float = corner_radius
        self.has_shadow: bool = has_shadow

    def render(self, ui: UIRenderer) -> None:
        if self.has_shadow:
            # Drop shadow layers
            ui.draw_rect(self.x + 3, self.y + 6, self.w, self.h, (0, 0, 0), alpha=0.08, corner_radius=self.corner_radius)
            ui.draw_rect(self.x + 1, self.y + 2, self.w, self.h, (0, 0, 0), alpha=0.05, corner_radius=self.corner_radius)

        # Main panel surface
        ui.draw_rect(self.x, self.y, self.w, self.h, self.bg_color, alpha=0.98, corner_radius=self.corner_radius)
        # Border outline
        ui.draw_rect_outline(self.x, self.y, self.w, self.h, self.border_color, line_width=1.0)

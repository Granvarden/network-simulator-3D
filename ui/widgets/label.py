"""Typography Label widget."""

from typing import Tuple
from config.graphics_config import GraphicsConfig
from rendering.ui_renderer import UIRenderer


class Label:
    """Styled text label."""

    def __init__(
        self,
        x: float, y: float,
        text: str,
        font_size: int = 16,
        color: Tuple[int, int, int] = GraphicsConfig.COLOR_TEXT_PRIMARY,
        center_x: bool = False,
        center_y: bool = False
    ):
        self.x: float = x
        self.y: float = y
        self.text: str = text
        self.font_size: int = font_size
        self.color: Tuple[int, int, int] = color
        self.center_x: bool = center_x
        self.center_y: bool = center_y

    def render(self, ui: UIRenderer) -> Tuple[int, int]:
        return ui.draw_text(
            self.text, self.x, self.y,
            font_size=self.font_size,
            color=self.color,
            center_x=self.center_x,
            center_y=self.center_y
        )

"""Network Engineer Workstation Desk, Monitor, and Terminal interactable."""

from typing import Tuple
from OpenGL.GL import *
from rendering.primitives import draw_box, draw_cylinder
from .interactable import Interactable


class Desk(Interactable):
    """Engineer workstation desk equipped with terminal monitor and keyboard."""

    def __init__(self, position: Tuple[float, float, float] = (0.0, 0.0, 3.5)):
        super().__init__(name="Engineer Workstation", position=position)
        self.width: float = 1.6
        self.depth: float = 0.8
        self.height: float = 0.75

    def get_interaction_hint(self) -> str:
        return "[E] Engineer Workstation Terminal"

    def get_bounding_box(self) -> Tuple[float, float, float, float, float, float]:
        cx, cy, cz = self.position
        hw = self.width / 2.0
        hd = self.depth / 2.0
        return (cx - hw, cy, cz - hd, cx + hw, cy + self.height + 0.5, cz + hd)

    def render(self) -> None:
        cx, cy, cz = self.position

        # Desk Top Surface (Light birch / industrial gray top)
        top_color = (0.78, 0.80, 0.82)
        top_y = cy + self.height
        draw_box(cx, top_y, cz, self.width, 0.04, self.depth, top_color)

        # 4 Metal Legs
        leg_color = (0.22, 0.24, 0.26)
        hw = self.width / 2.0 - 0.06
        hd = self.depth / 2.0 - 0.06
        leg_h = self.height - 0.02
        leg_y = cy + leg_h / 2.0
        draw_box(cx - hw, leg_y, cz - hd, 0.04, leg_h, 0.04, leg_color)
        draw_box(cx + hw, leg_y, cz - hd, 0.04, leg_h, 0.04, leg_color)
        draw_box(cx - hw, leg_y, cz + hd, 0.04, leg_h, 0.04, leg_color)
        draw_box(cx + hw, leg_y, cz + hd, 0.04, leg_h, 0.04, leg_color)

        # Monitor Stand
        stand_color = (0.15, 0.16, 0.18)
        draw_box(cx, top_y + 0.04, cz - 0.15, 0.22, 0.015, 0.18, stand_color)
        draw_box(cx, top_y + 0.16, cz - 0.15, 0.04, 0.24, 0.03, stand_color)

        # Monitor Screen (Bezel + glowing cyan/green terminal screen facing player)
        bezel_color = (0.10, 0.11, 0.12)
        draw_box(cx, top_y + 0.32, cz - 0.15, 0.62, 0.38, 0.03, bezel_color)
        screen_color = (0.05, 0.18, 0.15)  # CRT/Terminal dark green hue
        draw_box(cx, top_y + 0.32, cz - 0.133, 0.58, 0.34, 0.005, screen_color)

        # Keyboard
        kb_color = (0.18, 0.20, 0.22)
        draw_box(cx, top_y + 0.025, cz + 0.12, 0.44, 0.012, 0.14, kb_color)

        # Mouse
        mouse_color = (0.15, 0.16, 0.18)
        draw_box(cx + 0.30, top_y + 0.025, cz + 0.12, 0.07, 0.018, 0.11, mouse_color)

        # Office Chair
        chair_color = (0.20, 0.22, 0.25)
        chair_z = cz + 0.65
        draw_box(cx, cy + 0.45, chair_z, 0.48, 0.08, 0.48, chair_color)
        draw_box(cx, cy + 0.75, chair_z + 0.20, 0.46, 0.50, 0.06, chair_color)
        draw_box(cx, cy + 0.22, chair_z, 0.05, 0.44, 0.05, leg_color)
        # Chair base star
        draw_box(cx, cy + 0.03, chair_z, 0.50, 0.03, 0.50, leg_color)

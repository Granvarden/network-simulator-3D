"""Data Center / Network Lab Room geometry and bounds."""

from typing import List, Tuple
from OpenGL.GL import *
from rendering.primitives import draw_box, draw_grid_plane
from config.game_config import GameConfig
from config.graphics_config import GraphicsConfig


class Room:
    """20m x 15m server room environment."""

    def __init__(self):
        self.width: float = GameConfig.ROOM_WIDTH    # 20.0m (-10.0 to +10.0)
        self.depth: float = GameConfig.ROOM_DEPTH    # 15.0m (-7.5 to +7.5)
        self.height: float = GameConfig.ROOM_HEIGHT  # 4.0m (0.0 to 4.0)

    def render(self) -> None:
        hw = self.width / 2.0
        hd = self.depth / 2.0

        # Raised Floor with 1m x 1m Server Room Grid Tiles
        draw_grid_plane(
            width=self.width,
            depth=self.depth,
            tile_size=1.0,
            y_pos=0.0,
            color_plane=GraphicsConfig.COLOR_FLOOR_TILE,
            color_grid=GraphicsConfig.COLOR_FLOOR_GRID
        )

        # Ceiling
        draw_box(0.0, self.height + 0.05, 0.0, self.width, 0.1, self.depth, GraphicsConfig.COLOR_CEILING)

        # Fluorescent Overhead Light Fixtures (Glowing long white bars)
        light_color = (0.95, 0.98, 1.0)
        for z_light in [-4.0, 0.0, 4.0]:
            for x_light in [-5.0, 0.0, 5.0]:
                draw_box(x_light, self.height - 0.06, z_light, 2.4, 0.08, 0.4, (0.3, 0.32, 0.35))
                draw_box(x_light, self.height - 0.11, z_light, 2.2, 0.02, 0.3, light_color)

        # Cable Trays (Yellow/steel ladder trays running overhead above racks)
        tray_color = (0.85, 0.70, 0.15)
        draw_box(0.0, 3.2, -3.0, self.width - 2.0, 0.04, 0.5, tray_color)
        draw_box(0.0, 3.2, 3.5, self.width - 2.0, 0.04, 0.5, tray_color)

        # 4 Boundary Walls
        wall_color = GraphicsConfig.COLOR_WALL
        trim_color = GraphicsConfig.COLOR_WALL_TRIM

        # North Wall (Z = -hd)
        draw_box(0.0, self.height / 2.0, -hd - 0.05, self.width, self.height, 0.1, wall_color)
        draw_box(0.0, 0.1, -hd + 0.02, self.width, 0.2, 0.04, trim_color)

        # South Wall (Z = +hd)
        draw_box(0.0, self.height / 2.0, hd + 0.05, self.width, self.height, 0.1, wall_color)
        draw_box(0.0, 0.1, hd - 0.02, self.width, 0.2, 0.04, trim_color)

        # West Wall (X = -hw)
        draw_box(-hw - 0.05, self.height / 2.0, 0.0, 0.1, self.height, self.depth, wall_color)
        draw_box(-hw + 0.02, 0.1, 0.0, 0.04, 0.2, self.depth, trim_color)

        # East Wall (X = +hw)
        draw_box(hw + 0.05, self.height / 2.0, 0.0, 0.1, self.height, self.depth, wall_color)
        draw_box(hw - 0.02, 0.1, 0.0, 0.04, 0.2, self.depth, trim_color)

    def get_wall_boxes(self) -> List[Tuple[float, float, float, float, float, float]]:
        """Returns AABBs for boundary walls: (min_x, min_y, min_z, max_x, max_y, max_z)."""
        hw = self.width / 2.0
        hd = self.depth / 2.0
        h = self.height
        return [
            (-hw - 1.0, 0.0, -hd - 1.0, hw + 1.0, h, -hd),       # North Wall
            (-hw - 1.0, 0.0, hd, hw + 1.0, h, hd + 1.0),         # South Wall
            (-hw - 1.0, 0.0, -hd - 1.0, -hw, h, hd + 1.0),       # West Wall
            (hw, 0.0, -hd - 1.0, hw + 1.0, h, hd + 1.0),         # East Wall
        ]

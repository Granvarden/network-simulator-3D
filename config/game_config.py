"""Game configuration constants and settings."""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class GameConfig:
    # Window & Display
    WINDOW_TITLE: str = "Network Engineer Simulator 3D"
    WINDOW_WIDTH: int = 1280
    WINDOW_HEIGHT: int = 720
    TARGET_FPS: int = 60
    VSYNC: bool = True

    # Player Controller Physics
    PLAYER_EYE_HEIGHT: float = 1.7
    PLAYER_HEIGHT: float = 1.8
    PLAYER_RADIUS: float = 0.35
    WALK_SPEED: float = 4.0
    SPRINT_SPEED: float = 7.0
    JUMP_VELOCITY: float = 4.5
    GRAVITY: float = 12.0
    MOUSE_SENSITIVITY: float = 0.35
    MAX_PITCH: float = 89.0

    # Interaction
    INTERACT_MAX_DISTANCE: float = 2.8

    # Room Dimensions (20m x 15m x 4m)
    ROOM_WIDTH: float = 20.0
    ROOM_DEPTH: float = 15.0
    ROOM_HEIGHT: float = 4.0

    # Rack Specifications (Standard 42U Server Rack)
    RACK_U_COUNT: int = 42
    RACK_U_HEIGHT_METERS: float = 0.04445  # 1.75 inches
    RACK_WIDTH_METERS: float = 0.60
    RACK_DEPTH_METERS: float = 0.90
    RACK_TOTAL_HEIGHT_METERS: float = 42 * 0.04445  # ~1.87m + frame ~2.0m
    RACK_BASE_OFFSET_Y: float = 0.10

    # Starting Inventory
    INITIAL_ROUTERS: int = 2
    INITIAL_SWITCHES: int = 4
    INITIAL_PCS: int = 4
    INITIAL_CABLES: int = 20

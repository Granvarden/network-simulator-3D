"""Graphics and color palette configuration."""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class GraphicsConfig:
    # Camera
    FOV: float = 65.0
    NEAR_CLIP: float = 0.1
    FAR_CLIP: float = 120.0

    # Modern Light Theme UI Palette (RGB in 0-255 for 2D / 0.0-1.0 for GL)
    COLOR_BG_LIGHT: Tuple[int, int, int] = (245, 247, 250)         # Soft clean light gray #F5F7FA
    COLOR_CARD_LIGHT: Tuple[int, int, int] = (255, 255, 255)       # Pure white card
    COLOR_CARD_BORDER: Tuple[int, int, int] = (226, 232, 240)      # Border #E2E8F0
    COLOR_TEXT_PRIMARY: Tuple[int, int, int] = (15, 23, 42)        # Slate 900 #0F172A
    COLOR_TEXT_MUTED: Tuple[int, int, int] = (100, 116, 139)       # Slate 500 #64748B
    COLOR_PRIMARY_BLUE: Tuple[int, int, int] = (37, 99, 235)       # Royal Blue #2563EB
    COLOR_PRIMARY_HOVER: Tuple[int, int, int] = (29, 78, 216)      # Darker Blue #1D4ED8
    COLOR_ACCENT_TEAL: Tuple[int, int, int] = (14, 165, 233)       # Sky/Teal #0EA5E9
    COLOR_SUCCESS_GREEN: Tuple[int, int, int] = (34, 197, 94)      # Emerald #22C55E
    COLOR_WARNING_AMBER: Tuple[int, int, int] = (245, 158, 11)     # Amber #F59E0B
    COLOR_DANGER_RED: Tuple[int, int, int] = (239, 68, 68)         # Red #EF4444

    # Terminal UI Dark Theme (RGB)
    COLOR_TERM_BG: Tuple[int, int, int] = (20, 24, 34)             # Deep Dark Navy #141822
    COLOR_TERM_BORDER: Tuple[int, int, int] = (45, 55, 72)         # Border
    COLOR_TERM_TEXT: Tuple[int, int, int] = (226, 232, 240)        # Soft white
    COLOR_TERM_PROMPT: Tuple[int, int, int] = (56, 189, 248)       # Cyan prompt
    COLOR_TERM_SUCCESS: Tuple[int, int, int] = (74, 222, 128)      # Green output
    COLOR_TERM_ERROR: Tuple[int, int, int] = (248, 113, 113)       # Red error output

    # 3D World Materials & Colors (Normalized 0.0 - 1.0)
    COLOR_FLOOR_TILE: Tuple[float, float, float] = (0.75, 0.77, 0.80)
    COLOR_FLOOR_GRID: Tuple[float, float, float] = (0.60, 0.62, 0.65)
    COLOR_WALL: Tuple[float, float, float] = (0.85, 0.87, 0.90)
    COLOR_WALL_TRIM: Tuple[float, float, float] = (0.35, 0.38, 0.42)
    COLOR_CEILING: Tuple[float, float, float] = (0.90, 0.92, 0.94)

    # Equipment Colors
    COLOR_RACK_FRAME: Tuple[float, float, float] = (0.15, 0.16, 0.18)
    COLOR_RACK_RAILS: Tuple[float, float, float] = (0.30, 0.32, 0.35)
    COLOR_ROUTER_CHASSIS: Tuple[float, float, float] = (0.18, 0.22, 0.28) # Cisco dark teal/gray
    COLOR_SWITCH_CHASSIS: Tuple[float, float, float] = (0.12, 0.15, 0.20) # Charcoal switch
    COLOR_PC_CHASSIS: Tuple[float, float, float] = (0.22, 0.24, 0.26)
    COLOR_PORT_METAL: Tuple[float, float, float] = (0.70, 0.72, 0.75)
    COLOR_LED_GREEN: Tuple[float, float, float] = (0.1, 0.95, 0.2)
    COLOR_LED_AMBER: Tuple[float, float, float] = (0.95, 0.72, 0.05)
    COLOR_LED_RED: Tuple[float, float, float] = (0.95, 0.18, 0.18)
    COLOR_LED_OFF: Tuple[float, float, float] = (0.12, 0.16, 0.12)
    COLOR_CABLE_BLUE: Tuple[float, float, float] = (0.15, 0.45, 0.95)
    COLOR_CABLE_YELLOW: Tuple[float, float, float] = (0.95, 0.85, 0.15)

"""Modern rounded UI button widget with hover effects and optional badge."""

from typing import Callable, Optional, Tuple
import pygame
from config.graphics_config import GraphicsConfig
from rendering.ui_renderer import UIRenderer


class Button:
    """Modern rounded button with interactive hover feedback."""

    def __init__(
        self,
        x: float, y: float, w: float, h: float,
        text: str,
        on_click: Optional[Callable[[], None]] = None,
        is_primary: bool = False,
        badge_text: Optional[str] = None,
        enabled: bool = True
    ):
        self.x: float = x
        self.y: float = y
        self.w: float = w
        self.h: float = h
        self.text: str = text
        self.on_click: Optional[Callable[[], None]] = on_click
        self.is_primary: bool = is_primary
        self.badge_text: Optional[str] = badge_text
        self.enabled: bool = enabled
        self.is_hovered: bool = False

    def is_inside(self, px: int, py: int) -> bool:
        return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse movement and click events. Returns True if clicked."""
        if not self.enabled:
            return False

        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.is_inside(event.pos[0], event.pos[1])

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_inside(event.pos[0], event.pos[1]):
                if self.on_click:
                    self.on_click()
                return True

        return False

    def render(self, ui: UIRenderer) -> None:
        """Render the button with rounded corners and modern styling."""
        radius = 8.0

        if not self.enabled:
            # Disabled styling
            bg_color = (241, 245, 249)
            text_color = (148, 163, 184)
            ui.draw_rect(self.x, self.y, self.w, self.h, bg_color, alpha=0.9, corner_radius=radius)
            ui.draw_rect_outline(self.x, self.y, self.w, self.h, (226, 232, 240), line_width=1.0)
        elif self.is_primary:
            # Primary Royal Blue Button
            bg_color = GraphicsConfig.COLOR_PRIMARY_HOVER if self.is_hovered else GraphicsConfig.COLOR_PRIMARY_BLUE
            text_color = (255, 255, 255)
            # Subtle drop shadow when hovered
            if self.is_hovered:
                ui.draw_rect(self.x + 2, self.y + 3, self.w, self.h, (20, 30, 60), alpha=0.15, corner_radius=radius)
            ui.draw_rect(self.x, self.y, self.w, self.h, bg_color, alpha=1.0, corner_radius=radius)
        else:
            # Secondary White Card Button
            bg_color = (248, 250, 252) if self.is_hovered else GraphicsConfig.COLOR_CARD_LIGHT
            text_color = GraphicsConfig.COLOR_PRIMARY_BLUE if self.is_hovered else GraphicsConfig.COLOR_TEXT_PRIMARY
            border_color = GraphicsConfig.COLOR_PRIMARY_BLUE if self.is_hovered else GraphicsConfig.COLOR_CARD_BORDER

            if self.is_hovered:
                ui.draw_rect(self.x + 1, self.y + 2, self.w, self.h, (0, 0, 0), alpha=0.06, corner_radius=radius)
            ui.draw_rect(self.x, self.y, self.w, self.h, bg_color, alpha=1.0, corner_radius=radius)
            ui.draw_rect_outline(self.x, self.y, self.w, self.h, border_color, line_width=1.5 if self.is_hovered else 1.0)

        # Draw main text centered
        cx = self.x + self.w / 2.0
        cy = self.y + self.h / 2.0
        ui.draw_text(self.text, cx, cy, font_size=18, color=text_color, center_x=True, center_y=True)

        # Draw Badge (e.g. "Coming Soon") on right side if provided
        if self.badge_text:
            badge_font_size = 12
            badge_w, badge_h = 90, 20
            bx = self.x + self.w - badge_w - 12
            by = self.y + (self.h - badge_h) / 2.0
            ui.draw_rect(bx, by, badge_w, badge_h, (241, 245, 249), alpha=1.0, corner_radius=4.0)
            ui.draw_rect_outline(bx, by, badge_w, badge_h, (203, 213, 225), line_width=1.0)
            ui.draw_text(self.badge_text, bx + badge_w / 2.0, by + badge_h / 2.0, font_size=badge_font_size, color=(100, 116, 139), center_x=True, center_y=True)

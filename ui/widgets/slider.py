"""Interactive Modern UI Slider widget with dragging and mouse wheel scroll support."""

from typing import Callable, Optional, Tuple
import pygame
from config.graphics_config import GraphicsConfig
from rendering.ui_renderer import UIRenderer


class Slider:
    """Modern horizontal slider widget supporting mouse dragging, clicking, and mouse wheel scrolling."""

    def __init__(
        self,
        x: float, y: float, w: float, h: float,
        min_val: float = 0.05,
        max_val: float = 1.00,
        initial_val: float = 0.35,
        step: float = 0.01,
        label: str = "Sensitivity",
        on_change: Optional[Callable[[float], None]] = None
    ):
        self.x: float = x
        self.y: float = y
        self.w: float = w
        self.h: float = h
        self.min_val: float = min_val
        self.max_val: float = max_val
        self.value: float = initial_val
        self.step: float = step
        self.label: str = label
        self.on_change: Optional[Callable[[float], None]] = on_change

        self.is_dragging: bool = False
        self.is_hovered: bool = False
        self.track_height: float = 8.0
        self.handle_radius: float = 11.0

    @property
    def normalized(self) -> float:
        """Normalized 0.0 - 1.0 position along slider range."""
        return max(0.0, min(1.0, (self.value - self.min_val) / (self.max_val - self.min_val)))

    def is_inside(self, px: int, py: int) -> bool:
        """Check if mouse point is within active area of slider."""
        pad = 12
        return (self.x - pad <= px <= self.x + self.w + pad) and (self.y - pad <= py <= self.y + self.h + pad)

    def set_value(self, new_val: float) -> None:
        """Update value clamped to min/max and notify callback."""
        clamped = max(self.min_val, min(self.max_val, new_val))
        # Round to step
        if self.step > 0:
            clamped = round(clamped / self.step) * self.step
        clamped = round(clamped, 2)

        if abs(clamped - self.value) > 1e-4:
            self.value = clamped
            if self.on_change:
                self.on_change(self.value)

    def _update_from_mouse_x(self, mouse_x: float) -> None:
        """Calculate value from mouse X position along track."""
        ratio = max(0.0, min(1.0, (mouse_x - self.x) / self.w))
        new_val = self.min_val + ratio * (self.max_val - self.min_val)
        self.set_value(new_val)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse clicks, drag, and mouse wheel scrolling."""
        # 1. Mouse motion
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.is_inside(event.pos[0], event.pos[1])
            if self.is_dragging:
                self._update_from_mouse_x(event.pos[0])
                return True

        # 2. Mouse button down
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Left click: start drag / jump to position
            if event.button == 1:
                if self.is_inside(event.pos[0], event.pos[1]):
                    self.is_dragging = True
                    self._update_from_mouse_x(event.pos[0])
                    return True

            # Mouse wheel scroll up (button 4 or MOUSEWHEEL)
            elif event.button == 4:
                if self.is_hovered:
                    self.set_value(self.value + 0.05)
                    return True

            # Mouse wheel scroll down (button 5)
            elif event.button == 5:
                if self.is_hovered:
                    self.set_value(self.value - 0.05)
                    return True

        # 3. Mouse button up
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if self.is_dragging:
                    self.is_dragging = False
                    return True

        # 4. Pygame 2.0+ MOUSEWHEEL event
        elif event.type == pygame.MOUSEWHEEL:
            if self.is_hovered:
                # event.y > 0 is scroll up, < 0 is scroll down
                delta = event.y * 0.05
                self.set_value(self.value + delta)
                return True

        return False

    def render(self, ui: UIRenderer) -> None:
        """Render track, filled progress, thumb handle, and value label."""
        track_y = self.y + (self.h - self.track_height) / 2.0

        # Background track (soft light gray with rounded corners)
        ui.draw_rect(self.x, track_y, self.w, self.track_height, (226, 232, 240), alpha=1.0, corner_radius=4.0)

        # Filled active track (Royal blue)
        fill_w = self.normalized * self.w
        if fill_w > 0.0:
            ui.draw_rect(self.x, track_y, fill_w, self.track_height, GraphicsConfig.COLOR_PRIMARY_BLUE, alpha=1.0, corner_radius=4.0)

        # Handle thumb X coordinate
        handle_x = self.x + fill_w
        handle_y = track_y + self.track_height / 2.0

        # Thumb drop shadow
        ui.draw_rect(handle_x - self.handle_radius + 1, handle_y - self.handle_radius + 2, self.handle_radius * 2, self.handle_radius * 2, (0, 0, 0), alpha=0.15, corner_radius=self.handle_radius)

        # Thumb outer body (Pure white)
        ui.draw_rect(handle_x - self.handle_radius, handle_y - self.handle_radius, self.handle_radius * 2, self.handle_radius * 2, (255, 255, 255), alpha=1.0, corner_radius=self.handle_radius)

        # Thumb outline (Royal blue when hovered/dragging, slate border when idle)
        border_c = GraphicsConfig.COLOR_PRIMARY_BLUE if (self.is_hovered or self.is_dragging) else (148, 163, 184)
        ui.draw_rect_outline(handle_x - self.handle_radius, handle_y - self.handle_radius, self.handle_radius * 2, self.handle_radius * 2, border_c, line_width=2.0 if (self.is_hovered or self.is_dragging) else 1.5)

        # Thumb inner blue dot
        ui.draw_rect(handle_x - 3, handle_y - 3, 6, 6, GraphicsConfig.COLOR_PRIMARY_BLUE, alpha=1.0, corner_radius=3.0)

        # Live value badge on right side
        val_str = f"{self.value:.2f}"
        badge_w, badge_h = 56, 24
        bx = self.x + self.w + 16
        by = self.y + (self.h - badge_h) / 2.0
        ui.draw_rect(bx, by, badge_w, badge_h, (238, 242, 255), alpha=1.0, corner_radius=6.0)
        ui.draw_rect_outline(bx, by, badge_w, badge_h, (199, 210, 254), line_width=1.0)
        ui.draw_text(val_str, bx + badge_w / 2.0, by + badge_h / 2.0, font_size=13, color=GraphicsConfig.COLOR_PRIMARY_BLUE, center_x=True, center_y=True)

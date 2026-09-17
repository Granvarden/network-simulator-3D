"""2D UI Renderer over OpenGL using immediate geometry and cached text textures."""

import math
from typing import Dict, Tuple
import pygame
from OpenGL.GL import *


class UIRenderer:
    """Renders 2D modern cards, rounded buttons, and crisp typography over OpenGL."""

    def __init__(self):
        self._text_cache: Dict[Tuple[str, int, Tuple[int, int, int], bool], Tuple[int, int, int]] = {}
        self._fonts: Dict[int, pygame.font.Font] = {}
        self._mono_fonts: Dict[int, pygame.font.Font] = {}

    def get_font(self, size: int) -> pygame.font.Font:
        """Get or create cached pygame font."""
        if size not in self._fonts:
            try:
                # Try Segoe UI or Arial or fallback to default
                self._fonts[size] = pygame.font.SysFont("Segoe UI", size)
            except Exception:
                self._fonts[size] = pygame.font.Font(None, size)
        return self._fonts[size]

    def get_mono_font(self, size: int) -> pygame.font.Font:
        """Get or create cached monospaced font for terminals and tabular alignments."""
        if size not in self._mono_fonts:
            for fname in ("Consolas", "Courier New", "Cascadia Mono", "Lucida Console", "monospace"):
                try:
                    f = pygame.font.SysFont(fname, size)
                    if f:
                        self._mono_fonts[size] = f
                        break
                except Exception:
                    continue
            if size not in self._mono_fonts:
                self._mono_fonts[size] = pygame.font.Font(None, size)
        return self._mono_fonts[size]

    def measure_text(self, text: str, font_size: int = 18, mono: bool = False) -> Tuple[int, int]:
        """Measure exact pixel width and height of text without creating textures."""
        if not text:
            return 0, 0
        font = self.get_mono_font(font_size) if mono else self.get_font(font_size)
        return font.size(text)

    def draw_rect(
        self,
        x: float, y: float, w: float, h: float,
        color: Tuple[int, int, int],
        alpha: float = 1.0,
        corner_radius: float = 0.0
    ) -> None:
        """Draw filled rectangle with optional rounded corners and alpha."""
        r, g, b = color[0] / 255.0, color[1] / 255.0, color[2] / 255.0
        glColor4f(r, g, b, alpha)

        if corner_radius <= 1.0:
            glBegin(GL_QUADS)
            glVertex2f(x, y + h)
            glVertex2f(x + w, y + h)
            glVertex2f(x + w, y)
            glVertex2f(x, y)
            glEnd()
            return

        rad = min(corner_radius, w / 2.0, h / 2.0)
        # Center box + side extensions + 4 corner arcs
        glBegin(GL_POLYGON)
        # Top-right corner
        for angle in range(0, 91, 15):
            rad_ang = math.radians(angle)
            glVertex2f(x + w - rad + math.cos(rad_ang) * rad, y + rad - math.sin(rad_ang) * rad)
        # Top-left corner
        for angle in range(90, 181, 15):
            rad_ang = math.radians(angle)
            glVertex2f(x + rad + math.cos(rad_ang) * rad, y + rad - math.sin(rad_ang) * rad)
        # Bottom-left corner
        for angle in range(180, 271, 15):
            rad_ang = math.radians(angle)
            glVertex2f(x + rad + math.cos(rad_ang) * rad, y + h - rad - math.sin(rad_ang) * rad)
        # Bottom-right corner
        for angle in range(270, 361, 15):
            rad_ang = math.radians(angle)
            glVertex2f(x + w - rad + math.cos(rad_ang) * rad, y + h - rad - math.sin(rad_ang) * rad)
        glEnd()

    def draw_rect_outline(
        self,
        x: float, y: float, w: float, h: float,
        color: Tuple[int, int, int],
        alpha: float = 1.0,
        line_width: float = 1.0
    ) -> None:
        """Draw rectangle border outline."""
        r, g, b = color[0] / 255.0, color[1] / 255.0, color[2] / 255.0
        glLineWidth(line_width)
        glColor4f(r, g, b, alpha)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x, y)
        glVertex2f(x + w, y)
        glVertex2f(x + w, y + h)
        glVertex2f(x, y + h)
        glEnd()

    def draw_text(
        self,
        text: str,
        x: float, y: float,
        font_size: int = 18,
        color: Tuple[int, int, int] = (15, 23, 42),
        center_x: bool = False,
        center_y: bool = False,
        mono: bool = False
    ) -> Tuple[int, int]:
        """Render cached texture text with crisp anti-aliasing."""
        if not text:
            return 0, 0

        cache_key = (text, font_size, color, mono)
        if cache_key in self._text_cache:
            tex_id, tw, th = self._text_cache[cache_key]
        else:
            font = self.get_mono_font(font_size) if mono else self.get_font(font_size)
            surface = font.render(text, True, color)
            tw, th = surface.get_width(), surface.get_height()
            tex_data = pygame.image.tostring(surface, "RGBA", True)

            tex_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, tw, th, 0, GL_RGBA, GL_UNSIGNED_BYTE, tex_data)

            # Cap cache size
            if len(self._text_cache) > 600:
                old_key, (old_tex, _, _) = next(iter(self._text_cache.items()))
                try:
                    glDeleteTextures(1, [old_tex])
                except Exception:
                    pass
                del self._text_cache[old_key]

            self._text_cache[cache_key] = (tex_id, tw, th)

        draw_x = round(x - (tw / 2.0 if center_x else 0.0))
        draw_y = round(y - (th / 2.0 if center_y else 0.0))

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glColor4f(1.0, 1.0, 1.0, 1.0)

        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex2f(draw_x, draw_y + th)
        glTexCoord2f(1.0, 0.0); glVertex2f(draw_x + tw, draw_y + th)
        glTexCoord2f(1.0, 1.0); glVertex2f(draw_x + tw, draw_y)
        glTexCoord2f(0.0, 1.0); glVertex2f(draw_x, draw_y)
        glEnd()

        glDisable(GL_TEXTURE_2D)
        return tw, th

    def clear_cache(self) -> None:
        """Clear all cached textures."""
        for tex_id, _, _ in self._text_cache.values():
            try:
                glDeleteTextures(1, [tex_id])
            except Exception:
                pass
        self._text_cache.clear()

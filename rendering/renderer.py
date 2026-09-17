"""Core 3D & 2D OpenGL Renderer."""

import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
from config.graphics_config import GraphicsConfig


class Renderer:
    """Manages OpenGL viewport, 3D perspective setup, and 2D overlay passes."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self._init_gl()

    def _init_gl(self) -> None:
        """Initialize OpenGL states."""
        glViewport(0, 0, self.width, self.height)
        glClearColor(0.12, 0.14, 0.17, 1.0)
        glClearDepth(1.0)
        glDepthRange(0.0, 1.0)

        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)

        glShadeModel(GL_SMOOTH)
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
        glEnable(GL_NORMALIZE)

        # Alpha blending for clean modern UI
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def resize(self, width: int, height: int) -> None:
        """Update viewport dimensions."""
        self.width = max(1, width)
        self.height = max(1, height)
        glViewport(0, 0, self.width, self.height)

    def clear(self) -> None:
        """Clear color and depth buffers."""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def begin_3d(self) -> None:
        """Setup 3D perspective projection."""
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_CULL_FACE)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = self.width / float(self.height)
        gluPerspective(GraphicsConfig.FOV, aspect, GraphicsConfig.NEAR_CLIP, GraphicsConfig.FAR_CLIP)

    def begin_2d(self) -> None:
        """Switch to 2D orthographic projection for pixel-perfect UI rendering."""
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glDisable(GL_CULL_FACE)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0.0, float(self.width), float(self.height), 0.0, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def present(self) -> None:
        """Swap front and back buffers."""
        pygame.display.flip()

"""OpenGL lighting configuration."""

from OpenGL.GL import *
from typing import Tuple


class Lighting:
    """Configures industrial data center lighting."""

    @staticmethod
    def setup_lights():
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        # Ambient light
        ambient_light = [0.35, 0.36, 0.38, 1.0]
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, ambient_light)

        # Overhead light 1 (Above racks)
        light0_pos = [0.0, 3.8, -2.0, 1.0]
        light0_diff = [0.85, 0.88, 0.92, 1.0]
        light0_spec = [0.3, 0.3, 0.3, 1.0]
        glLightfv(GL_LIGHT0, GL_POSITION, light0_pos)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, light0_diff)
        glLightfv(GL_LIGHT0, GL_SPECULAR, light0_spec)

        # Overhead light 2 (Above engineer desk)
        light1_pos = [0.0, 3.8, 3.0, 1.0]
        light1_diff = [0.75, 0.78, 0.82, 1.0]
        glLightfv(GL_LIGHT1, GL_POSITION, light1_pos)
        glLightfv(GL_LIGHT1, GL_DIFFUSE, light1_diff)

        # Material shininess
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.4, 0.4, 0.4, 1.0])
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 32.0)

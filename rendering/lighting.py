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
        glEnable(GL_NORMALIZE)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        # Ambient light: Cleanroom diffuse lighting reflecting from white ceiling & light walls
        ambient_light = [0.44, 0.46, 0.48, 1.0]
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, ambient_light)

        # Overhead light 0: Cold aisle troffer luminaire directly above racks (Racks at Z = -7.05)
        # Positioned at Z = -5.8, Y = 3.6 shining down and onto front faceplates and patch cables at ~45°
        light0_pos = [0.0, 3.6, -5.8, 1.0]
        light0_diff = [0.90, 0.92, 0.96, 1.0]
        light0_spec = [0.35, 0.35, 0.35, 1.0]
        glLightfv(GL_LIGHT0, GL_POSITION, light0_pos)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, light0_diff)
        glLightfv(GL_LIGHT0, GL_SPECULAR, light0_spec)

        # Overhead light 1: Central datacenter troffer luminaire
        light1_pos = [0.0, 3.6, 0.0, 1.0]
        light1_diff = [0.75, 0.78, 0.82, 1.0]
        glLightfv(GL_LIGHT1, GL_POSITION, light1_pos)
        glLightfv(GL_LIGHT1, GL_DIFFUSE, light1_diff)

        # Material shininess
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.4, 0.4, 0.4, 1.0])
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 32.0)

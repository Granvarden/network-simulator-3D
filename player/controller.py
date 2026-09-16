"""First-person character controller."""

import pygame
from typing import List, Tuple
from config.game_config import GameConfig
from core.input_manager import InputManager
from rendering.camera import Camera
from .collision import resolve_player_collision


class PlayerController:
    """Handles first-person player physics, movement, and orientation."""

    def __init__(self, camera: Camera):
        self.camera: Camera = camera
        self.x: float = camera.x
        self.y: float = 0.0  # Feet level
        self.z: float = camera.z

        self.velocity_y: float = 0.0
        self.is_grounded: bool = True

        self.walk_speed: float = GameConfig.WALK_SPEED
        self.sprint_speed: float = GameConfig.SPRINT_SPEED
        self.jump_velocity: float = GameConfig.JUMP_VELOCITY
        self.gravity: float = GameConfig.GRAVITY
        self.radius: float = GameConfig.PLAYER_RADIUS
        self.height: float = GameConfig.PLAYER_HEIGHT
        self.eye_height: float = GameConfig.PLAYER_EYE_HEIGHT
        self.sensitivity: float = GameConfig.MOUSE_SENSITIVITY

    def update(
        self,
        dt: float,
        input_mgr: InputManager,
        collision_boxes: List[Tuple[float, float, float, float, float, float]]
    ) -> None:
        """Update orientation from mouse and position from keyboard + collision."""
        # 1. Mouse Look
        if input_mgr.is_mouse_locked:
            dx, dy = input_mgr.mouse_rel
            self.camera.rotate(dx * self.sensitivity, -dy * self.sensitivity, GameConfig.MAX_PITCH)

        # 2. Movement Input Vector
        move_x = 0.0
        move_z = 0.0

        if input_mgr.is_key_down(pygame.K_w):
            move_z += 1.0
        if input_mgr.is_key_down(pygame.K_s):
            move_z -= 1.0
        if input_mgr.is_key_down(pygame.K_d):
            move_x += 1.0
        if input_mgr.is_key_down(pygame.K_a):
            move_x -= 1.0

        # Determine movement speed
        is_sprinting = input_mgr.is_key_down(pygame.K_LSHIFT) or input_mgr.is_key_down(pygame.K_RSHIFT)
        current_speed = self.sprint_speed if is_sprinting else self.walk_speed

        # Convert local input to world X/Z
        fx, fz = self.camera.get_horizontal_forward()
        rx, rz = self.camera.get_horizontal_right()

        world_vx = (fx * move_z + rx * move_x) * current_speed
        world_vz = (fz * move_z + rz * move_x) * current_speed

        # 3. Jump and Gravity
        if self.is_grounded and input_mgr.is_key_just_pressed(pygame.K_SPACE):
            self.velocity_y = self.jump_velocity
            self.is_grounded = False

        self.velocity_y -= self.gravity * dt
        self.y += self.velocity_y * dt

        # Floor collision
        if self.y <= 0.0:
            self.y = 0.0
            self.velocity_y = 0.0
            self.is_grounded = True

        # 4. Resolve Horizontal Obstacle Collision
        target_x = self.x + world_vx * dt
        target_z = self.z + world_vz * dt

        resolved_x, resolved_z = resolve_player_collision(
            self.x, self.z,
            target_x, target_z,
            self.y, self.radius, self.height,
            collision_boxes
        )
        self.x = resolved_x
        self.z = resolved_z

        # 5. Sync Camera position
        self.camera.x = self.x
        self.camera.y = self.y + self.eye_height
        self.camera.z = self.z

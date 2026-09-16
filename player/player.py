"""Player entity combining camera, controller, and interaction detection."""

from typing import Optional, Tuple
from core.input_manager import InputManager
from rendering.camera import Camera
from world.world import World
from .controller import PlayerController
from .interaction import InteractionDetector, InteractionTarget


class Player:
    """Player entity in the 3D Network Lab."""

    def __init__(self, initial_pos: Tuple[float, float, float] = (0.0, 0.0, 1.5)):
        self.camera: Camera = Camera(initial_pos[0], initial_pos[1] + 1.7, initial_pos[2])
        self.controller: PlayerController = PlayerController(self.camera)
        self.interaction_detector: InteractionDetector = InteractionDetector()
        self.current_target: InteractionTarget = InteractionTarget(target_type="NONE")

    @property
    def position(self) -> Tuple[float, float, float]:
        return (self.controller.x, self.controller.y, self.controller.z)

    @property
    def eye_position(self) -> Tuple[float, float, float]:
        return (self.camera.x, self.camera.y, self.camera.z)

    def update(self, dt: float, input_mgr: InputManager, world: World) -> None:
        """Update physics, camera, and crosshair raycast targeting."""
        collision_boxes = world.get_collision_boxes()
        self.controller.update(dt, input_mgr, collision_boxes)

        # Update raycast interaction target
        eye_pos = self.eye_position
        fwd = self.camera.get_forward_vector()
        self.current_target = self.interaction_detector.find_target(
            eye_pos=eye_pos,
            forward=fwd,
            interactables=world.get_all_interactables()
        )

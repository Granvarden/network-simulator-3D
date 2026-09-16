"""Time and frame rate management."""

import time
import pygame


class TimeManager:
    """Calculates delta time, frame rates, and game clock."""

    def __init__(self, target_fps: int = 60):
        self._target_fps = target_fps
        self._clock = pygame.time.Clock()
        self._delta_time: float = 0.0
        self._total_time: float = 0.0
        self._current_fps: float = 0.0
        self._frame_count: int = 0
        self._last_time = time.perf_counter()

    @property
    def delta_time(self) -> float:
        return self._delta_time

    @property
    def total_time(self) -> float:
        return self._total_time

    @property
    def fps(self) -> float:
        return self._current_fps

    def tick(self) -> float:
        """Call once per frame. Returns delta time in seconds clamped to max 0.1s."""
        self._clock.tick(self._target_fps)
        now = time.perf_counter()
        dt = now - self._last_time
        self._last_time = now

        # Clamp dt to prevent physics explosion during lag or window dragging
        self._delta_time = min(dt, 0.1)
        self._total_time += self._delta_time
        self._frame_count += 1
        self._current_fps = self._clock.get_fps()
        return self._delta_time

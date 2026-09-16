"""Input abstraction and mouse control."""

from typing import Dict, Set, Tuple
import pygame


class InputManager:
    """Manages raw keyboard/mouse events and provides action queries."""

    def __init__(self):
        self._keys_down: Set[int] = set()
        self._keys_pressed_this_frame: Set[int] = set()
        self._keys_released_this_frame: Set[int] = set()
        self._mouse_buttons_down: Set[int] = set()
        self._mouse_buttons_pressed: Set[int] = set()
        self._mouse_rel: Tuple[int, int] = (0, 0)
        self._mouse_pos: Tuple[int, int] = (0, 0)
        self._mouse_locked: bool = False

    @property
    def mouse_rel(self) -> Tuple[int, int]:
        return self._mouse_rel

    @property
    def mouse_pos(self) -> Tuple[int, int]:
        return self._mouse_pos

    @property
    def is_mouse_locked(self) -> bool:
        return self._mouse_locked

    def set_mouse_locked(self, locked: bool) -> None:
        """Lock/unlock the mouse cursor for first-person navigation."""
        self._mouse_locked = locked
        pygame.mouse.set_visible(not locked)
        pygame.event.set_grab(locked)
        if locked:
            # Clear initial jerk
            pygame.mouse.get_rel()
            self._mouse_rel = (0, 0)

    def process_event(self, event: pygame.event.Event) -> None:
        """Feed a Pygame event into the manager."""
        if event.type == pygame.KEYDOWN:
            self._keys_down.add(event.key)
            self._keys_pressed_this_frame.add(event.key)
        elif event.type == pygame.KEYUP:
            self._keys_down.discard(event.key)
            self._keys_released_this_frame.add(event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self._mouse_buttons_down.add(event.button)
            self._mouse_buttons_pressed.add(event.button)
        elif event.type == pygame.MOUSEBUTTONUP:
            self._mouse_buttons_down.discard(event.button)
        elif event.type == pygame.MOUSEMOTION:
            self._mouse_pos = event.pos

    def begin_frame(self) -> None:
        """Clear single-frame trigger buffers and query hardware mouse delta."""
        self._keys_pressed_this_frame.clear()
        self._keys_released_this_frame.clear()
        self._mouse_buttons_pressed.clear()
        if self._mouse_locked:
            self._mouse_rel = pygame.mouse.get_rel()
        else:
            self._mouse_rel = (0, 0)

    def is_key_down(self, key: int) -> bool:
        return key in self._keys_down

    def is_key_just_pressed(self, key: int) -> bool:
        return key in self._keys_pressed_this_frame

    def is_mouse_button_down(self, button: int = 1) -> bool:
        return button in self._mouse_buttons_down

    def is_mouse_button_just_pressed(self, button: int = 1) -> bool:
        return button in self._mouse_buttons_pressed

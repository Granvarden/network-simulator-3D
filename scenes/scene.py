"""Base Scene interface."""

from abc import ABC, abstractmethod
import pygame
from core.service_container import ServiceContainer
from rendering.renderer import Renderer
from rendering.ui_renderer import UIRenderer


class Scene(ABC):
    """Abstract game scene."""

    def __init__(self, services: ServiceContainer):
        self.services = services

    @abstractmethod
    def on_enter(self) -> None:
        """Called when this scene becomes active."""
        pass

    @abstractmethod
    def on_exit(self) -> None:
        """Called when transitioning away from this scene."""
        pass

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle raw input events. Returns True if consumed."""
        pass

    @abstractmethod
    def update(self, dt: float) -> None:
        """Update simulation and logic."""
        pass

    @abstractmethod
    def render(self, renderer: Renderer, ui: UIRenderer) -> None:
        """Render 3D and 2D elements."""
        pass

    def resize(self, width: int, height: int) -> None:
        """Handle window resize."""
        pass

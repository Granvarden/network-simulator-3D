"""Main Menu Scene."""

import sys
import pygame
from core.game_state import GameState, GameStateManager
from core.service_container import ServiceContainer
from core.input_manager import InputManager
from rendering.renderer import Renderer
from rendering.ui_renderer import UIRenderer
from ui.main_menu import MainMenuUI
from .scene import Scene


class MainMenuScene(Scene):
    """Main Menu scene with Modern Light Theme UI."""

    def __init__(self, services: ServiceContainer):
        super().__init__(services)
        self.menu_ui = MainMenuUI(
            on_start_sandbox=self._start_sandbox,
            on_exit=self._exit_game
        )

    def on_enter(self) -> None:
        input_mgr: InputManager = self.services.get("input_manager")
        input_mgr.set_mouse_locked(False)

    def on_exit(self) -> None:
        pass

    def _start_sandbox(self) -> None:
        state_mgr: GameStateManager = self.services.get("state_manager")
        state_mgr.change_state(GameState.SANDBOX)

    def _exit_game(self) -> None:
        pygame.quit()
        sys.exit(0)

    def handle_event(self, event: pygame.event.Event) -> bool:
        return self.menu_ui.handle_event(event)

    def update(self, dt: float) -> None:
        pass

    def resize(self, width: int, height: int) -> None:
        self.menu_ui.resize(width, height)

    def render(self, renderer: Renderer, ui: UIRenderer) -> None:
        renderer.clear()
        renderer.begin_2d()
        self.menu_ui.render(ui)

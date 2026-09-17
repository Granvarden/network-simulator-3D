"""Core Game application coordinator and main loop."""

import sys
import pygame
from config.game_config import GameConfig
from .game_state import GameState, GameStateManager
from .event_bus import EventBus
from .time_manager import TimeManager
from .input_manager import InputManager
from .service_container import ServiceContainer
from rendering.renderer import Renderer
from rendering.ui_renderer import UIRenderer
from scenes.main_menu_scene import MainMenuScene
from scenes.sandbox_scene import SandboxScene


class Game:
    """Master game engine loop and lifecycle manager."""

    def __init__(self):
        # 1. Initialize Pygame Video & OpenGL
        pygame.init()
        pygame.font.init()

        # OpenGL Context Attributes
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 4)
        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)

        # Create window with RESIZABLE flag
        self.width = GameConfig.WINDOW_WIDTH
        self.height = GameConfig.WINDOW_HEIGHT

        self.screen = pygame.display.set_mode(
            (self.width, self.height),
            pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE
        )
        pygame.display.set_caption(GameConfig.WINDOW_TITLE)

        # Auto-maximize window on Windows while keeping taskbar visible
        if sys.platform.startswith("win"):
            try:
                import ctypes
                from ctypes import wintypes
                hwnd = pygame.display.get_wm_info().get("window")
                if hwnd:
                    # SW_MAXIMIZE = 3 (maximizes window within desktop work area, taskbar stays visible)
                    ctypes.windll.user32.ShowWindow(hwnd, 3)
                    pygame.event.pump()
                    rect = wintypes.RECT()
                    ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(rect))
                    self.width = max(640, rect.right - rect.left)
                    self.height = max(480, rect.bottom - rect.top)
            except Exception as e:
                print(f"[Window Maximize Warning]: {e}")

        # 2. Core Service Container
        self.services = ServiceContainer()
        self.event_bus = EventBus()
        self.time_manager = TimeManager(target_fps=GameConfig.TARGET_FPS)
        self.input_manager = InputManager()
        self.state_manager = GameStateManager(initial_state=GameState.MAIN_MENU)

        self.services.register("event_bus", self.event_bus)
        self.services.register("time_manager", self.time_manager)
        self.services.register("input_manager", self.input_manager)
        self.services.register("state_manager", self.state_manager)

        # 3. Graphics Subsystems
        self.renderer = Renderer(self.width, self.height)
        self.ui_renderer = UIRenderer()

        # 4. Instantiate Scenes
        self.scenes = {
            GameState.MAIN_MENU: MainMenuScene(self.services),
            GameState.SANDBOX: SandboxScene(self.services),
        }
        for scene in self.scenes.values():
            scene.resize(self.width, self.height)

        self.current_scene = self.scenes[GameState.MAIN_MENU]
        self.current_scene.on_enter()

        # 5. Listen for State Changes
        self.state_manager.add_listener(self._on_state_changed)

        self.is_running: bool = True

    def on_resize(self, width: int, height: int) -> None:
        """Handle window resizing dynamically."""
        self.width = max(640, width)
        self.height = max(480, height)
        self.renderer.resize(self.width, self.height)
        for scene in self.scenes.values():
            scene.resize(self.width, self.height)

    def _on_state_changed(self, old_state: GameState, new_state: GameState) -> None:
        """Handle scene transitions."""
        if old_state in self.scenes:
            self.scenes[old_state].on_exit()

        if new_state in self.scenes:
            # Sync sensitivity from Menu Settings to Sandbox Player
            if new_state == GameState.SANDBOX and GameState.MAIN_MENU in self.scenes:
                menu_scene = self.scenes[GameState.MAIN_MENU]
                sandbox_scene = self.scenes[GameState.SANDBOX]
                if hasattr(menu_scene, "menu_ui") and hasattr(sandbox_scene, "player"):
                    sens = getattr(menu_scene.menu_ui, "mouse_sensitivity", GameConfig.MOUSE_SENSITIVITY)
                    sandbox_scene.player.controller.sensitivity = sens

            self.current_scene = self.scenes[new_state]
            self.current_scene.resize(self.width, self.height)
            self.current_scene.on_enter()

    def run(self) -> None:
        """Master execution loop."""
        while self.is_running:
            # A. Begin Frame Input Reset
            self.input_manager.begin_frame()

            # B. Event Pump
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_running = False
                    break

                elif event.type == pygame.VIDEORESIZE:
                    self.on_resize(event.w, event.h)

                self.input_manager.process_event(event)
                # Pass event to current scene
                self.current_scene.handle_event(event)

            # C. Frame Timing
            dt = self.time_manager.tick()

            # D. Simulation Update
            self.current_scene.update(dt)

            # E. Render Frame
            self.current_scene.render(self.renderer, self.ui_renderer)

            # F. Swap Buffers
            self.renderer.present()

        # Cleanup
        pygame.quit()
        sys.exit(0)

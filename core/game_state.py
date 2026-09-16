"""Game state management."""

from enum import Enum, auto
from typing import Callable, List, Optional


class GameState(Enum):
    MAIN_MENU = auto()
    SANDBOX = auto()
    TUTORIAL = auto()
    CHALLENGE = auto()
    PAUSE = auto()
    CLI_ACTIVE = auto()
    INVENTORY_ACTIVE = auto()
    INTERACTION_ACTIVE = auto()


class GameStateManager:
    """Manages the current state of the game and handles state transitions."""

    def __init__(self, initial_state: GameState = GameState.MAIN_MENU):
        self._current_state = initial_state
        self._previous_state: Optional[GameState] = None
        self._listeners: List[Callable[[GameState, GameState], None]] = []

    @property
    def current_state(self) -> GameState:
        return self._current_state

    @property
    def previous_state(self) -> Optional[GameState]:
        return self._previous_state

    def add_listener(self, listener: Callable[[GameState, GameState], None]) -> None:
        """Register a callback for state changes (old_state, new_state)."""
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[GameState, GameState], None]) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    def change_state(self, new_state: GameState) -> None:
        """Transition to a new game state and notify listeners."""
        if new_state == self._current_state:
            return
        old_state = self._current_state
        self._previous_state = old_state
        self._current_state = new_state
        for listener in self._listeners:
            listener(old_state, new_state)

    def revert_to_previous(self) -> None:
        """Revert back to the previous state if available."""
        if self._previous_state is not None:
            self.change_state(self._previous_state)

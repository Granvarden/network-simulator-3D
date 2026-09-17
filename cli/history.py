"""Bounded CLI command history with navigation and deduplication."""

from typing import List, Optional


class CLIHistory:
    """Manages command history per session with up/down arrow indexing."""

    def __init__(self, max_size: int = 100):
        self.max_size: int = max_size
        self.entries: List[str] = []
        self.index: int = -1

    def append(self, cmd: str) -> None:
        """Add command to history, avoiding duplicate consecutive commands."""
        clean = cmd.strip()
        if not clean:
            return
        if self.entries and self.entries[-1] == clean:
            self.index = -1
            return

        self.entries.append(clean)
        if len(self.entries) > self.max_size:
            self.entries.pop(0)
        self.index = -1

    def previous(self) -> Optional[str]:
        """Navigate backwards in history (Up Arrow)."""
        if not self.entries:
            return None
        if self.index == -1:
            self.index = len(self.entries) - 1
        else:
            self.index = max(0, self.index - 1)
        return self.entries[self.index]

    def next(self) -> Optional[str]:
        """Navigate forwards in history (Down Arrow)."""
        if not self.entries or self.index == -1:
            return None
        self.index += 1
        if self.index >= len(self.entries):
            self.index = -1
            return ""
        return self.entries[self.index]

    def reset_index(self) -> None:
        """Reset history navigation pointer."""
        self.index = -1

"""Save and load disk manager."""

import json
import os
from typing import Any, Dict, Optional


class SaveManager:
    """Manages reading and writing save game state to disk."""

    def __init__(self, saves_dir: str = "saves"):
        self.saves_dir = saves_dir
        os.makedirs(self.saves_dir, exist_ok=True)

    def save_to_file(self, data: Dict[str, Any], filename: str = "sandbox_save.json") -> bool:
        """Write simulation state dictionary to JSON file."""
        filepath = os.path.join(self.saves_dir, filename)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"[SaveManager Error] Failed to write save: {e}")
            return False

    def load_from_file(self, filename: str = "sandbox_save.json") -> Optional[Dict[str, Any]]:
        """Read simulation state dictionary from JSON file."""
        filepath = os.path.join(self.saves_dir, filename)
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[SaveManager Error] Failed to load save: {e}")
            return None

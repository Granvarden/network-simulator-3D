"""Command line tokenization and argument parser."""

import shlex
from typing import List


def parse_command_tokens(command_line: str) -> List[str]:
    """Tokenize a command string respecting quoted arguments."""
    clean = command_line.strip()
    if not clean:
        return []
    try:
        return shlex.split(clean)
    except ValueError:
        # Fallback to simple split if unclosed quote
        return clean.split()

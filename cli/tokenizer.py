"""CLI Lexer and Tokenizer with quote handling, token spans, and pipe filter extraction."""

import re
import shlex
from typing import List, Optional, Tuple


class CLITokenizer:
    """Tokenizes CLI command input while preserving token character indices for error markers."""

    @classmethod
    def tokenize(cls, line: str) -> List[str]:
        """
        Tokenize command line respecting quoted arguments.
        Falls back to regex splitting if an unclosed quote is encountered.
        """
        clean = line.strip()
        if not clean:
            return []
        try:
            return shlex.split(clean)
        except ValueError:
            # Handle unclosed quotes gracefully
            tokens = []
            for token, _, _ in cls.tokenize_with_spans(clean):
                tokens.append(token)
            return tokens

    @classmethod
    def tokenize_with_spans(cls, line: str) -> List[Tuple[str, int, int]]:
        """
        Tokenize command line and return list of (token_value, start_index, end_index).
        Respects quoted strings.
        """
        results: List[Tuple[str, int, int]] = []
        n = len(line)
        i = 0

        while i < n:
            # Skip whitespace
            while i < n and line[i].isspace():
                i += 1
            if i >= n:
                break

            start = i
            # Check for quoted token
            if line[i] in ('"', "'"):
                quote_char = line[i]
                i += 1
                token_chars = []
                while i < n and line[i] != quote_char:
                    token_chars.append(line[i])
                    i += 1
                if i < n and line[i] == quote_char:
                    i += 1  # consume closing quote
                results.append(("".join(token_chars), start, i))
            else:
                # Regular unquoted token
                while i < n and not line[i].isspace():
                    i += 1
                results.append((line[start:i], start, i))

        return results

    @classmethod
    def extract_pipe_filter(cls, line: str) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Extract Cisco output filtering pipe: e.g. 'show run | include interface'.
        Returns (base_command, filter_type, filter_pattern).
        Supported filter_types: 'include', 'exclude', 'begin', 'section'.
        """
        if "|" not in line:
            return line.strip(), None, None

        parts = line.split("|", 1)
        base_cmd = parts[0].strip()
        pipe_expr = parts[1].strip()

        pipe_tokens = pipe_expr.split(None, 1)
        if not pipe_tokens:
            return base_cmd, None, None

        ftype = pipe_tokens[0].lower()
        fpattern = pipe_tokens[1].strip() if len(pipe_tokens) > 1 else ""

        if ftype in ("include", "inc", "i"):
            return base_cmd, "include", fpattern
        elif ftype in ("exclude", "exc", "e"):
            return base_cmd, "exclude", fpattern
        elif ftype in ("begin", "beg", "b"):
            return base_cmd, "begin", fpattern
        elif ftype in ("section", "sec", "s"):
            return base_cmd, "section", fpattern

        return base_cmd, ftype, fpattern

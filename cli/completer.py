"""Context-sensitive CLI Tab Completer."""

from typing import Any, List, Optional, Tuple
from .tokenizer import CLITokenizer


class CLICompleter:
    """Provides command line tab auto-completion against active CommandRegistry."""

    @staticmethod
    def complete(input_line: str, handler: Any) -> Tuple[Optional[str], List[str]]:
        """
        Evaluate tab completion for current input buffer.
        
        Returns:
            (replacement_line, candidate_matches)
            - replacement_line: If single unique completion, new complete line. Else None.
            - candidate_matches: List of matches if multiple or informative.
        """
        clean = input_line
        if not clean:
            return None, []

        registry = getattr(handler, "registry", None)
        context = getattr(handler, "context", None)
        if not registry or not context:
            return None, []

        tokens = clean.split()
        if not tokens:
            return None, []

        # If user input ended with a space, user is asking for the next token
        if clean.endswith(" "):
            tokens.append("")

        matches = registry.get_completions(tokens, context.mode)

        if len(matches) == 1:
            matched_kw = matches[0]
            # Replace last token with matched keyword
            if clean.endswith(" "):
                new_line = clean + matched_kw + " "
            else:
                last_space = clean.rfind(" ")
                if last_space == -1:
                    new_line = matched_kw + " "
                else:
                    new_line = clean[:last_space + 1] + matched_kw + " "
            return new_line, matches
        elif len(matches) > 1:
            return None, matches

        return None, []

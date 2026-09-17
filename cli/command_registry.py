"""Command Registry supporting prefix matching, ambiguity detection, and help generation."""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from .prompts.mode import CLIMode
from .command_result import CommandResult
from .command_error import CommandError


@dataclass
class CommandDefinition:
    """Specification for a CLI command or subcommand."""
    tokens: List[str]                   # Canonical tokens, e.g. ["show", "ip", "interface", "brief"]
    handler: Callable[..., CommandResult] # Function receiving (device, context, args)
    modes: Set[CLIMode]                 # Valid operating modes
    help_summary: str                   # Single line help description
    min_args: int = 0                   # Minimum additional parameters
    max_args: Optional[int] = None      # Maximum additional parameters (None = unlimited)


class CommandRegistry:
    """Registry and dispatcher for hierarchical Cisco IOS commands."""

    def __init__(self):
        self._commands: List[CommandDefinition] = []

    def register(
        self,
        tokens: List[str],
        handler: Callable[..., CommandResult],
        modes: Set[CLIMode],
        help_summary: str,
        min_args: int = 0,
        max_args: Optional[int] = None
    ) -> None:
        """Register a command definition."""
        self._commands.append(CommandDefinition(
            tokens=[t.lower() for t in tokens],
            handler=handler,
            modes=modes,
            help_summary=help_summary,
            min_args=min_args,
            max_args=max_args
        ))

    def get_available_commands(self, mode: CLIMode) -> List[CommandDefinition]:
        """List all commands available in a given CLI mode."""
        return [cmd for cmd in self._commands if mode in cmd.modes]

    def match(
        self, input_tokens: List[str], mode: CLIMode
    ) -> Tuple[Optional[CommandDefinition], List[str], Optional[List[str]], Optional[int]]:
        """
        Match token stream against registered commands for current mode.
        
        Returns:
            (matched_definition, remaining_args, error_lines, error_token_idx)
        """
        if not input_tokens:
            return None, [], None, None

        # Filter commands valid in this mode
        candidates = self.get_available_commands(mode)
        if not candidates:
            return None, [], CommandError.unknown_command(input_tokens[0]), 0

        # Step through tokens to match command prefix
        curr_candidates = candidates
        matched_tokens_count = 0

        for tok_idx, user_tok in enumerate(input_tokens):
            user_lower = user_tok.lower()

            # Find candidates that have a token at this position
            pos_candidates = [c for c in curr_candidates if len(c.tokens) > tok_idx]
            if not pos_candidates:
                # We've matched the longest prefix command, rest are arguments
                break

            # Check for matches at position tok_idx
            matches_at_pos: Dict[str, List[CommandDefinition]] = {}
            for c in pos_candidates:
                cmd_tok = c.tokens[tok_idx]
                if cmd_tok.startswith(user_lower):
                    matches_at_pos.setdefault(cmd_tok, []).append(c)

            if not matches_at_pos:
                # If we haven't matched even 1 command token, it's an unknown command
                if tok_idx == 0:
                    return None, [], CommandError.invalid_input(" ".join(input_tokens), 0), 0
                # Otherwise, this token might be an argument to a partially matched command
                break

            # If multiple different canonical command tokens match this user abbreviation
            if len(matches_at_pos) > 1:
                return None, [], CommandError.ambiguous_command(user_tok), tok_idx

            # Single unambiguous keyword match at this position
            matched_canonical_token = list(matches_at_pos.keys())[0]
            curr_candidates = matches_at_pos[matched_canonical_token]
            matched_tokens_count = tok_idx + 1

        if not curr_candidates or matched_tokens_count == 0:
            return None, [], CommandError.invalid_input(" ".join(input_tokens), 0), 0

        # Look for exact or best matching definition among remaining candidates
        # Prefer candidate where len(tokens) == matched_tokens_count
        exact_matches = [c for c in curr_candidates if len(c.tokens) == matched_tokens_count]
        if not exact_matches:
            # User gave partial command without completing required subcommands (e.g. 'show ip')
            return None, [], CommandError.incomplete_command(), matched_tokens_count

        best_cmd = exact_matches[0]
        args = input_tokens[matched_tokens_count:]

        # Validate argument counts
        if len(args) < best_cmd.min_args:
            return None, [], CommandError.incomplete_command(), len(input_tokens)

        if best_cmd.max_args is not None and len(args) > best_cmd.max_args:
            return None, [], CommandError.unknown_command(args[best_cmd.max_args]), matched_tokens_count + best_cmd.max_args

        return best_cmd, args, None, None

    def get_completions(self, input_tokens: List[str], mode: CLIMode) -> List[str]:
        """Provide keyword auto-completions for current input tokens."""
        candidates = self.get_available_commands(mode)
        tok_idx = len(input_tokens) - 1 if input_tokens else 0
        current_token = input_tokens[-1].lower() if input_tokens else ""

        # Filter candidates matching prior tokens
        for idx in range(tok_idx):
            prior = input_tokens[idx].lower()
            candidates = [c for c in candidates if len(c.tokens) > idx and c.tokens[idx].startswith(prior)]

        # Find unique keyword candidates at tok_idx
        completions = set()
        for c in candidates:
            if len(c.tokens) > tok_idx:
                keyword = c.tokens[tok_idx]
                if keyword.startswith(current_token):
                    completions.add(keyword)

        return sorted(completions)

    def get_help(self, input_tokens: List[str], mode: CLIMode) -> List[str]:
        """Generate context-sensitive help lines for '?' query."""
        candidates = self.get_available_commands(mode)
        tok_idx = len(input_tokens)

        # Filter by prior tokens if provided
        for idx, t in enumerate(input_tokens):
            t_low = t.lower()
            candidates = [c for c in candidates if len(c.tokens) > idx and c.tokens[idx].startswith(t_low)]

        help_dict: Dict[str, str] = {}
        for c in candidates:
            if len(c.tokens) > tok_idx:
                kw = c.tokens[tok_idx]
                help_dict[kw] = c.help_summary
            elif len(c.tokens) == tok_idx:
                help_dict["<cr>"] = c.help_summary

        lines = []
        for kw, summary in sorted(help_dict.items()):
            lines.append(f"  {kw:<18} {summary}")
        return lines

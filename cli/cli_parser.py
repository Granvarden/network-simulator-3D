"""CLI Command Parser integrating tokenizer, registry lookup, and pipe filtering."""

from typing import Any, List, Optional, Tuple
from .tokenizer import CLITokenizer
from .command_registry import CommandRegistry
from .command_result import CommandResult
from .command_error import CommandError
from .cli_context import CLIContext


def parse_command_tokens(command_line: str) -> List[str]:
    """Tokenize a command string respecting quoted arguments (Backwards compatible helper)."""
    return CLITokenizer.tokenize(command_line)


class CLIParser:
    """Parses, dispatches, and executes CLI input lines against a CommandRegistry."""

    def __init__(self, registry: CommandRegistry):
        self.registry = registry

    def execute(self, line: str, device: Any, context: CLIContext) -> CommandResult:
        """Parse and execute a line of input."""
        clean = line.strip()
        if not clean:
            return CommandResult.ok()

        # Check for context-sensitive help query '?'
        if clean.endswith("?") or clean == "?":
            query_line = clean[:-1].rstrip()
            tokens = CLITokenizer.tokenize(query_line)
            help_lines = self.registry.get_help(tokens, context.mode)
            return CommandResult.ok(output=help_lines if help_lines else ["% No matching commands found."])

        # Extract Cisco output filter pipe (e.g. '| include Gi0')
        base_cmd, filter_type, filter_pattern = CLITokenizer.extract_pipe_filter(clean)

        # Tokenize with character span tracking for exact error positioning
        token_spans = CLITokenizer.tokenize_with_spans(base_cmd)
        tokens = [t[0] for t in token_spans]
        if not tokens:
            return CommandResult.ok()

        # Handle 'do' prefix in configuration modes (executes privileged exec commands)
        is_do = False
        saved_mode = context.mode
        if tokens[0].lower() == "do" and len(tokens) > 1:
            if context.mode not in (context.mode.USER_EXEC, context.mode.PRIVILEGED_EXEC, context.mode.PC_PROMPT):
                is_do = True
                tokens = tokens[1:]
                token_spans = token_spans[1:]
                context.mode = context.mode.PRIVILEGED_EXEC

        # Match against command registry
        cmd_def, args, error_lines, error_idx = self.registry.match(tokens, context.mode)

        if error_lines:
            if is_do:
                context.mode = saved_mode
            # Position caret marker at erroneous token if error is an invalid input error
            if error_idx is not None and error_idx < len(token_spans) and len(error_lines) >= 2 and "^" in error_lines[1]:
                err_pos = token_spans[error_idx][1]
                error_lines[1] = f"{' ' * err_pos}^"
            return CommandResult(output=error_lines, success=False)

        if not cmd_def:
            if is_do:
                context.mode = saved_mode
            return CommandResult.error(f"% Invalid input detected at '{tokens[0]}'")

        # Execute handler
        try:
            result = cmd_def.handler(device, context, args)
        except Exception as e:
            result = CommandResult.error(f"% Command failed: {e}")
        finally:
            if is_do:
                context.mode = saved_mode

        # Apply output pipe filter if requested
        if filter_type and result.output:
            result.output = self._apply_filter(result.output, filter_type, filter_pattern or "")

        return result

    @staticmethod
    def _apply_filter(lines: List[str], filter_type: str, pattern: str) -> List[str]:
        """Apply Cisco-style output stream filter."""
        pat = pattern.lower()
        if filter_type == "include":
            return [line for line in lines if pat in line.lower()]
        elif filter_type == "exclude":
            return [line for line in lines if pat not in line.lower()]
        elif filter_type == "begin":
            for idx, line in enumerate(lines):
                if pat in line.lower():
                    return lines[idx:]
            return []
        elif filter_type == "section":
            filtered = []
            capturing = False
            for line in lines:
                if pat in line.lower():
                    capturing = True
                elif capturing and line and not line.startswith(" "):
                    capturing = False
                if capturing:
                    filtered.append(line)
            return filtered
        return lines

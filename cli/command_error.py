"""Standard Cisco IOS error message generators."""

from typing import List


class CommandError:
    """Generates standard Cisco IOS error formatted outputs."""

    @staticmethod
    def invalid_input(line: str, pos: int) -> List[str]:
        """
        Generate standard Cisco '^' marker error.
        Example:
            % Invalid input detected at '^' marker.
            shwo ip int br
              ^
        """
        marker_pad = " " * max(0, pos)
        return [
            "% Invalid input detected at '^' marker.",
            f"{marker_pad}^"
        ]

    @staticmethod
    def incomplete_command() -> List[str]:
        """Return standard Cisco incomplete command error."""
        return ["% Incomplete command."]

    @staticmethod
    def ambiguous_command(token: str) -> List[str]:
        """Return standard Cisco ambiguous command error."""
        return [f'% Ambiguous command:  "{token}"']

    @staticmethod
    def unknown_command(token: str) -> List[str]:
        """Return unknown command error."""
        return [f'% Invalid input detected at \'{token}\'']

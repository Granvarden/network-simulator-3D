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

    def get_cisco_help(self, raw_cmd: str, mode: CLIMode) -> List[str]:
        """
        Generate detailed, authentic Cisco IOS context-sensitive help.
        Supports:
          - Top level commands with mode header (Exec commands:, Configure commands:, etc.)
          - Subcommand help with aligned descriptions (e.g. 'show ?', 'show ip ?', 'copy ?')
          - Partial keyword queries (e.g. 'sh?', 'c?')
          - Parameter argument hints (WORD, <1-4094>, IP addresses)
          - <cr> execution indicators when a command is executable
        """
        token_descriptions: Dict[Any, str] = {
            # Top-level commands
            "clear": "Reset functions",
            "clock": "Manage the system clock",
            "configure": "Enter configuration mode",
            "copy": "Copy from one file to another",
            "debug": "Debugging functions",
            "default": "Set a command to its defaults",
            "description": "Interface specific description",
            "disable": "Turn off privileged commands",
            "do": "To run an exec command in configuration mode",
            "duplex": "Configure duplex operation",
            "enable": "Turn on privileged commands",
            "end": "Exit to privileged EXEC mode",
            "erase": "Erase a filesystem",
            "exit": "Exit from current mode",
            "help": "Description of the interactive help system",
            "hostname": "Set system's network name",
            "interface": "Select an interface to configure",
            "ip": "Global IP configuration subcommands",
            "line": "Configure a terminal line",
            "mac": "MAC configuration and tables",
            "name": "Ascii name of the VLAN",
            "no": "Negate a command or set its defaults",
            "ping": "Send echo messages",
            "quit": "Exit from current mode",
            "reload": "Halt and perform a cold restart",
            "show": "Show running system information",
            "shutdown": "Shut down the selected interface",
            "speed": "Configure speed operation",
            "switchport": "Set switching mode characteristics",
            "terminal": "Set terminal line parameters",
            "traceroute": "Trace route to destination",
            "undebug": "Disable debugging functions",
            "vlan": "VLAN configuration commands",
            "write": "Write running configuration to memory, network, or terminal",

            # PC Prompt Commands
            "cls": "Clear the terminal screen",
            "ipconfig": "Display IP configuration",
            "netstat": "Display active network connections",
            "route": "Display or modify local routing table",

            # Intermediate subcommands
            ("show", "arp"): "ARP table",
            ("show", "clock"): "Manage the system clock",
            ("show", "history"): "Display the session command history",
            ("show", "interfaces"): "Interface status and configuration",
            ("show", "ip"): "IP information",
            ("show", "mac"): "MAC address table information",
            ("show", "mac-address-table"): "MAC forwarding table",
            ("show", "running-config"): "Current operating configuration",
            ("show", "startup-config"): "Contents of startup configuration",
            ("show", "version"): "System hardware and software status",
            ("show", "vlan"): "VLAN status",
            ("show", "ip", "arp"): "IP ARP table",
            ("show", "ip", "interface"): "IP interface status and configuration",
            ("show", "ip", "interface", "brief"): "Brief summary of IP status and configuration",
            ("show", "ip", "route"): "IP routing table",

            ("configure", "terminal"): "Configure from the terminal",
            ("copy", "running-config"): "Copy from running configuration",
            ("copy", "running-config", "startup-config"): "Copy to startup configuration (NVRAM)",
            ("write", "memory"): "Write running configuration to NVRAM",

            ("ip", "address"): "Set the IP address of an interface",
            ("ip", "route"): "Establish static routes",
            ("ip", "routing"): "Enable IP routing",

            ("no", "shutdown"): "Enable the selected interface",
            ("no", "ip"): "Negate IP configuration",
            ("no", "ip", "address"): "Remove IP address from interface",
            ("no", "ip", "route"): "Remove static route",
            ("no", "vlan"): "Remove VLAN",
            ("no", "switchport"): "Reset switchport characteristics",

            ("switchport", "access"): "Set access mode characteristics of the interface",
            ("switchport", "access", "vlan"): "Set VLAN when interface is in access mode",
            ("switchport", "mode"): "Set trunk or access mode of the interface",
            ("switchport", "mode", "access"): "Set trunking mode to ACCESS unconditionally",
            ("switchport", "mode", "trunk"): "Set trunking mode to TRUNK unconditionally",
            ("switchport", "trunk"): "Set trunking characteristics of the interface",
            ("switchport", "trunk", "allowed"): "Set allowed VLANs on trunk",
            ("switchport", "trunk", "allowed", "vlan"): "Set allowed VLANs list on trunk",

            ("clear", "mac"): "Clear MAC table subcommands",
            ("clear", "mac", "address-table"): "Clear dynamic MAC forwarding table",
        }

        mode_headers = {
            CLIMode.USER_EXEC: "Exec commands:",
            CLIMode.PRIVILEGED_EXEC: "Exec commands:",
            CLIMode.GLOBAL_CONFIG: "Configure commands:",
            CLIMode.INTERFACE_CONFIG: "Interface configuration commands:",
            CLIMode.VLAN_CONFIG: "VLAN configuration commands:",
            CLIMode.LINE_CONFIG: "Line configuration commands:",
            CLIMode.ROUTER_CONFIG: "Router configuration commands:",
            CLIMode.PC_PROMPT: "Available commands:",
        }

        candidates = self.get_available_commands(mode)
        raw_stripped = raw_cmd.strip()

        # Mode-specific keyword description overrides
        if mode == CLIMode.INTERFACE_CONFIG:
            token_descriptions["ip"] = "Interface Internet Protocol config commands"

        # 1. Top-Level Help (query is '?' or 'help' or '')
        if raw_stripped in ("?", "help", ""):
            header = mode_headers.get(mode, "Available commands:")
            top_words = sorted(list({c.tokens[0] for c in candidates if c.tokens}))
            lines = [header]
            for kw in top_words:
                desc = token_descriptions.get(kw, "Execute command")
                lines.append(f"  {kw:<18} {desc}")
            return lines

        # 2. Partial keyword matching (e.g. 'sh?', 'c?' - no whitespace before '?')
        if raw_stripped.endswith("?") and not raw_cmd.endswith(" ?") and not raw_cmd.endswith("\t?"):
            clean = raw_stripped[:-1].strip()
            tokens = clean.split()
            if not tokens:
                return self.get_cisco_help("?", mode)

            prefix = tokens[-1].lower()
            prior = [t.lower() for t in tokens[:-1]]

            # Filter by prior tokens
            curr_cands = candidates
            for idx, p in enumerate(prior):
                curr_cands = [c for c in curr_cands if len(c.tokens) > idx and c.tokens[idx].startswith(p)]

            tok_idx = len(prior)
            matches = set()
            for c in curr_cands:
                if len(c.tokens) > tok_idx and c.tokens[tok_idx].startswith(prefix):
                    matches.add(c.tokens[tok_idx])

            if matches:
                return ["  " + "  ".join(sorted(matches))]
            return ["% Unrecognized command"]

        # 3. Subcommand and Parameter Help (e.g. 'show ?', 'show ip ?', 'copy ?')
        clean = raw_stripped.rstrip("?").strip()
        tokens = clean.split()
        if not tokens:
            return self.get_cisco_help("?", mode)

        # Match prior tokens against candidates with prefix tolerance
        curr_cands = candidates
        matched_tokens = []
        for idx, t in enumerate(tokens):
            t_low = t.lower()
            pos_matches = [c for c in curr_cands if len(c.tokens) > idx and c.tokens[idx].startswith(t_low)]
            if pos_matches:
                curr_cands = pos_matches
                # Canonical token
                matched_tokens.append(pos_matches[0].tokens[idx])
            else:
                break

        tok_idx = len(matched_tokens)
        help_items: Dict[str, str] = {}

        # Keywords at this position
        for c in curr_cands:
            if len(c.tokens) > tok_idx:
                kw = c.tokens[tok_idx]
                sub_key = tuple(matched_tokens + [kw])
                desc = token_descriptions.get(sub_key, token_descriptions.get(kw, c.help_summary))
                help_items[kw] = desc
            elif len(c.tokens) == tok_idx:
                help_items["<cr>"] = ""

        # Specific argument hints based on matched tokens
        m_tuple = tuple(matched_tokens)
        if m_tuple in (("ping",), ("traceroute",)):
            help_items["WORD"] = "IP address or hostname of target system"
        elif m_tuple == ("hostname",):
            help_items["WORD"] = "This system's network name"
        elif m_tuple == ("interface",):
            help_items["FastEthernet"] = "FastEthernet IEEE 802.3"
            help_items["GigabitEthernet"] = "GigabitEthernet IEEE 802.3z"
            help_items["Vlan"] = "Vlan interface"
        elif m_tuple == ("vlan",):
            help_items["<1-4094>"] = "VLAN ID"
        elif m_tuple in (("ip", "address"),):
            help_items["A.B.C.D"] = "IP address"
        elif len(matched_tokens) == 3 and matched_tokens[:2] == ["ip", "address"]:
            help_items["A.B.C.D"] = "IP subnet mask"
        elif m_tuple == ("ip", "route"):
            help_items["A.B.C.D"] = "Destination IP network"
        elif m_tuple == ("switchport", "access", "vlan"):
            help_items["<1-4094>"] = "VLAN ID"
        elif m_tuple == ("switchport", "trunk", "allowed", "vlan"):
            help_items["WORD"] = "VLAN IDs allowed on trunk (e.g. 10,20 or 1-100)"

        if not help_items:
            # If command takes no further arguments and is matched
            if curr_cands and any(len(c.tokens) == len(matched_tokens) for c in curr_cands):
                return ["  <cr>"]
            return ["% Unrecognized command"]

        # Sort so <cr> appears at the end
        lines = []
        for kw, desc in sorted(help_items.items(), key=lambda x: (x[0] == "<cr>", x[0])):
            if kw == "<cr>":
                lines.append("  <cr>")
            else:
                lines.append(f"  {kw:<18} {desc}")
        return lines

    def get_help(self, input_tokens: List[str], mode: CLIMode) -> List[str]:
        """Legacy helper delegating to get_cisco_help."""
        raw = " ".join(input_tokens) + " ?" if input_tokens else "?"
        return self.get_cisco_help(raw, mode)


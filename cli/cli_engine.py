"""Central interactive CLI Engine managing input buffers, history, tab-completion, and scrollback."""

from typing import Any, Dict, List, Optional
import pygame
from devices.device import Device
from devices.router import Router
from devices.switch import Switch
from devices.pc import PC
from network.network_engine import NetworkEngine
from .router_cli import RouterCLI
from .switch_cli import SwitchCLI
from .pc_cli import PCCLI


class CLIEngine:
    """Manages an active interactive terminal session attached to a network device."""

    def __init__(self, network_engine: Optional[NetworkEngine] = None):
        self.network_engine: Optional[NetworkEngine] = network_engine
        self.active_device: Optional[Device] = None
        self.device_handler: Any = None

        # Buffers & History
        self.input_buffer: str = ""
        self.cursor_pos: int = 0
        self.history: List[str] = []
        self.history_index: int = -1
        self.scrollback: List[str] = []
        self.max_scrollback: int = 500

        # Cursor blink timing
        self.cursor_blink_timer: float = 0.0
        self.cursor_visible: bool = True

    def attach_device(self, device: Device) -> None:
        """Attach terminal session to a device."""
        self.active_device = device
        self.input_buffer = ""
        self.cursor_pos = 0
        self.history_index = -1
        self.scrollback.clear()

        # Instantiate or reuse device-specific CLI handler
        if isinstance(device, Router):
            self.device_handler = RouterCLI(device, self.network_engine)
            self.scrollback.append(f"Connected to Router: {device.hostname}")
            self.scrollback.append("Type '?' or 'help' for available commands.")
            self.scrollback.append("")
        elif isinstance(device, Switch):
            self.device_handler = SwitchCLI(device, self.network_engine)
            self.scrollback.append(f"Connected to Switch: {device.hostname}")
            self.scrollback.append("Type '?' or 'help' for available commands.")
            self.scrollback.append("")
        elif isinstance(device, PC):
            self.device_handler = PCCLI(device, self.network_engine)
            self.scrollback.append("Microsoft Windows [Version 10.0.19045.3803]")
            self.scrollback.append("(c) Microsoft Corporation. All rights reserved.")
            self.scrollback.append("")

    def get_prompt(self) -> str:
        """Return active prompt line."""
        if not self.device_handler:
            return "CLI>"
        if hasattr(self.device_handler, "context"):
            return self.device_handler.context.get_prompt(self.active_device.hostname)
        elif hasattr(self.device_handler, "get_prompt"):
            return self.device_handler.get_prompt()
        return f"{self.active_device.hostname}>"

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Process keyboard events for terminal input. Returns True if handled."""
        if event.type != pygame.KEYDOWN:
            return False

        # Reset cursor blink on keypress
        self.cursor_visible = True
        self.cursor_blink_timer = 0.0

        # 1. Ctrl + C -> Cancel command line
        if (event.mod & pygame.KMOD_CTRL) and event.key == pygame.K_c:
            self.cancel_input()
            return True

        # 2. Enter / Return -> Execute command
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.submit_command()
            return True

        # 3. Backspace
        elif event.key == pygame.K_BACKSPACE:
            if self.cursor_pos > 0:
                self.input_buffer = self.input_buffer[:self.cursor_pos - 1] + self.input_buffer[self.cursor_pos:]
                self.cursor_pos -= 1
            return True

        # 4. Delete
        elif event.key == pygame.K_DELETE:
            if self.cursor_pos < len(self.input_buffer):
                self.input_buffer = self.input_buffer[:self.cursor_pos] + self.input_buffer[self.cursor_pos + 1:]
            return True

        # 5. Left Arrow
        elif event.key == pygame.K_LEFT:
            self.cursor_pos = max(0, self.cursor_pos - 1)
            return True

        # 6. Right Arrow
        elif event.key == pygame.K_RIGHT:
            self.cursor_pos = min(len(self.input_buffer), self.cursor_pos + 1)
            return True

        # 7. Home & End
        elif event.key == pygame.K_HOME:
            self.cursor_pos = 0
            return True
        elif event.key == pygame.K_END:
            self.cursor_pos = len(self.input_buffer)
            return True

        # 8. Up Arrow -> Command History Previous
        elif event.key == pygame.K_UP:
            if self.history:
                if self.history_index == -1:
                    self.history_index = len(self.history) - 1
                else:
                    self.history_index = max(0, self.history_index - 1)
                self.input_buffer = self.history[self.history_index]
                self.cursor_pos = len(self.input_buffer)
            return True

        # 9. Down Arrow -> Command History Next
        elif event.key == pygame.K_DOWN:
            if self.history and self.history_index != -1:
                self.history_index += 1
                if self.history_index >= len(self.history):
                    self.history_index = -1
                    self.input_buffer = ""
                else:
                    self.input_buffer = self.history[self.history_index]
                self.cursor_pos = len(self.input_buffer)
            return True

        # 10. Tab -> Autocomplete
        elif event.key == pygame.K_TAB:
            self.tab_autocomplete()
            return True

        # 11. Printable Character Input
        elif event.unicode and ord(event.unicode) >= 32:
            self.input_buffer = self.input_buffer[:self.cursor_pos] + event.unicode + self.input_buffer[self.cursor_pos:]
            self.cursor_pos += 1
            return True

        return False

    def submit_command(self) -> None:
        """Run the current command line against the active device CLI."""
        cmd = self.input_buffer.strip()
        prompt = self.get_prompt()

        # Echo prompt and command to scrollback
        self.scrollback.append(f"{prompt} {self.input_buffer}")

        if cmd:
            self.history.append(cmd)
            self.history_index = -1

            if self.device_handler:
                try:
                    output_lines = self.device_handler.execute(cmd)
                    self.scrollback.extend(output_lines)
                except Exception as e:
                    self.scrollback.append(f"% CLI Execution error: {e}")

        # Clear input buffer
        self.input_buffer = ""
        self.cursor_pos = 0

        # Trim scrollback if overflowing
        if len(self.scrollback) > self.max_scrollback:
            self.scrollback = self.scrollback[-self.max_scrollback:]

    def cancel_input(self) -> None:
        """Cancel current input line (Ctrl+C)."""
        prompt = self.get_prompt()
        self.scrollback.append(f"{prompt} {self.input_buffer}^C")
        self.input_buffer = ""
        self.cursor_pos = 0

    def tab_autocomplete(self) -> None:
        """Autocomplete commands based on active CLI mode."""
        if not self.input_buffer:
            return

        tokens = self.input_buffer.strip().split()
        if not tokens:
            return

        # Candidate keywords
        common_candidates = [
            "enable", "disable", "configure terminal", "hostname", "interface",
            "ip address", "ip route", "shutdown", "no shutdown", "description",
            "show running-config", "show interfaces", "show ip interface brief",
            "show mac address-table", "show vlan", "show ip route", "show version",
            "ping", "exit", "end", "ipconfig", "arp -a", "help"
        ]

        prefix = self.input_buffer.lower()
        matches = [c for c in common_candidates if c.lower().startswith(prefix)]

        if len(matches) == 1:
            self.input_buffer = matches[0] + " "
            self.cursor_pos = len(self.input_buffer)
        elif len(matches) > 1:
            self.scrollback.append(f"{self.get_prompt()} {self.input_buffer}")
            self.scrollback.append("  " + "  ".join(matches))

    def update(self, dt: float) -> None:
        """Update cursor blink timer."""
        self.cursor_blink_timer += dt
        if self.cursor_blink_timer >= 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_blink_timer = 0.0

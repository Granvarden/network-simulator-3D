"""CLI Session encapsulation for per-device state and history isolation."""

from typing import Any, List, Optional
from devices.device import Device
from devices.router import Router
from devices.switch import Switch
from devices.pc import PC
from network.network_engine import NetworkEngine
from .router_cli import RouterCLI
from .switch_cli import SwitchCLI
from .pc_cli import PCCLI
from .history import CLIHistory


class CLISession:
    """Maintains independent terminal session buffers, history, and CLI context for a device."""

    def __init__(self, device: Device, network_engine: Optional[NetworkEngine] = None, max_scrollback: int = 500):
        self.device_id: str = device.device_id
        self.device: Device = device
        self.network_engine: Optional[NetworkEngine] = network_engine
        self.max_scrollback: int = max_scrollback

        # Terminal state
        self.input_buffer: str = ""
        self.cursor_pos: int = 0
        self.history: CLIHistory = CLIHistory(max_size=100)
        self.scrollback: List[str] = []

        # Instantiate device-specific CLI handler
        self.handler: Any = None
        self._init_handler()

    def _init_handler(self) -> None:
        """Instantiate device-specific CLI processor with banner."""
        if isinstance(self.device, Router):
            self.handler = RouterCLI(self.device, self.network_engine)
            self.scrollback.append(f"Connected to Router: {self.device.hostname}")
            self.scrollback.append("Type '?' or 'help' for available commands.")
            self.scrollback.append("")
        elif isinstance(self.device, Switch):
            self.handler = SwitchCLI(self.device, self.network_engine)
            self.scrollback.append(f"Connected to Switch: {self.device.hostname}")
            self.scrollback.append("Type '?' or 'help' for available commands.")
            self.scrollback.append("")
        elif isinstance(self.device, PC):
            self.handler = PCCLI(self.device, self.network_engine)
            self.scrollback.append("Microsoft Windows [Version 10.0.19045.3803]")
            self.scrollback.append("(c) Microsoft Corporation. All rights reserved.")
            self.scrollback.append("")

    def get_prompt(self) -> str:
        """Retrieve dynamic prompt from active handler."""
        if hasattr(self.handler, "get_prompt"):
            return self.handler.get_prompt()
        return f"{self.device.hostname}>"

    def execute(self, cmd_line: str) -> List[str]:
        """Execute command line through session handler."""
        if not self.handler:
            return ["% No CLI handler attached"]
        return self.handler.execute(cmd_line)

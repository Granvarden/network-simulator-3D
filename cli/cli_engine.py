"""Central interactive CLI Engine managing sessions, history, tab-completion, and scrollback."""

from typing import Any, Dict, List, Optional
import pygame
from devices.device import Device
from network.network_engine import NetworkEngine
from .cli_session import CLISession
from .completer import CLICompleter


def _find_prev_word_pos(text: str, pos: int) -> int:
    """Find start index of previous word."""
    if pos <= 0:
        return 0
    p = pos - 1
    while p > 0 and text[p].isspace():
        p -= 1
    while p > 0 and not text[p - 1].isspace():
        p -= 1
    return p


def _find_next_word_pos(text: str, pos: int) -> int:
    """Find start index of next word."""
    n = len(text)
    if pos >= n:
        return n
    p = pos
    while p < n and not text[p].isspace():
        p += 1
    while p < n and text[p].isspace():
        p += 1
    return p


def _get_clipboard_text() -> str:
    """Safely extract plain text from clipboard."""
    try:
        if not pygame.scrap.get_init():
            pygame.scrap.init()
        raw = pygame.scrap.get(pygame.SCRAP_TEXT)
        if not raw:
            return ""
        raw = raw.rstrip(b'\x00')
        for enc in ("utf-8", "utf-16-le", "utf-16", "latin-1"):
            try:
                decoded = raw.decode(enc)
                if "\x00" not in decoded:
                    return decoded
            except Exception:
                pass
        return raw.decode("utf-8", errors="ignore").replace("\x00", "")
    except Exception:
        return ""


class CLIEngine:
    """Manages active interactive terminal sessions attached to network devices."""

    def __init__(self, network_engine: Optional[NetworkEngine] = None):
        self.network_engine: Optional[NetworkEngine] = network_engine
        self.active_device: Optional[Device] = None
        self.active_session: Optional[CLISession] = None
        self.sessions: Dict[str, CLISession] = {}
        self.max_scrollback: int = 500

        # Cursor blink timing
        self.cursor_blink_timer: float = 0.0
        self.cursor_visible: bool = True

    @property
    def device_handler(self) -> Optional[Any]:
        return self.active_session.handler if self.active_session else None

    @property
    def input_buffer(self) -> str:
        return self.active_session.input_buffer if self.active_session else ""

    @input_buffer.setter
    def input_buffer(self, val: str) -> None:
        if self.active_session:
            self.active_session.input_buffer = val

    @property
    def cursor_pos(self) -> int:
        return self.active_session.cursor_pos if self.active_session else 0

    @cursor_pos.setter
    def cursor_pos(self, val: int) -> None:
        if self.active_session:
            self.active_session.cursor_pos = val

    @property
    def scrollback(self) -> List[str]:
        return self.active_session.scrollback if self.active_session else []

    @scrollback.setter
    def scrollback(self, val: List[str]) -> None:
        if self.active_session:
            self.active_session.scrollback = val

    @property
    def history(self) -> List[str]:
        return self.active_session.history.entries if self.active_session else []

    def attach_device(self, device: Device) -> None:
        """Attach terminal session to a device, creating or resuming its isolated session."""
        self.active_device = device
        if device.device_id not in self.sessions:
            self.sessions[device.device_id] = CLISession(
                device=device,
                network_engine=self.network_engine,
                max_scrollback=self.max_scrollback
            )
        self.active_session = self.sessions[device.device_id]
        self.active_session.history.reset_index()

    def get_prompt(self) -> str:
        """Return active prompt line."""
        if not self.active_session:
            return "CLI>"
        return self.active_session.get_prompt()

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Process keyboard events for terminal input. Returns True if handled."""
        if event.type != pygame.KEYDOWN or not self.active_session:
            return False

        # Reset cursor blink on keypress
        self.cursor_visible = True
        self.cursor_blink_timer = 0.0

        session = self.active_session

        # 1. Ctrl Key combinations
        if event.mod & pygame.KMOD_CTRL:
            # Ctrl + V -> Paste clipboard text
            if event.key == pygame.K_v:
                clip_text = _get_clipboard_text()
                if clip_text:
                    clip_clean = clip_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")[0].replace("\t", "    ")
                    if clip_clean:
                        session.input_buffer = (
                            session.input_buffer[:session.cursor_pos] +
                            clip_clean +
                            session.input_buffer[session.cursor_pos:]
                        )
                        session.cursor_pos += len(clip_clean)
                return True

            # Ctrl + C -> Cancel command line
            elif event.key == pygame.K_c:
                self.cancel_input()
                return True

            # Ctrl + Z -> Return to privileged EXEC
            elif event.key == pygame.K_z:
                handler = session.handler
                if handler and hasattr(handler, "context"):
                    handler.context.end_mode()
                prompt = self.get_prompt()
                session.scrollback.append(f"{prompt} ^Z")
                session.input_buffer = ""
                session.cursor_pos = 0
                return True

            # Ctrl + A -> Beginning of line
            elif event.key == pygame.K_a:
                session.cursor_pos = 0
                return True

            # Ctrl + E -> End of line
            elif event.key == pygame.K_e:
                session.cursor_pos = len(session.input_buffer)
                return True

            # Ctrl + U -> Erase line before cursor
            elif event.key == pygame.K_u:
                session.input_buffer = session.input_buffer[session.cursor_pos:]
                session.cursor_pos = 0
                return True

            # Ctrl + K -> Erase from cursor to end of line
            elif event.key == pygame.K_k:
                session.input_buffer = session.input_buffer[:session.cursor_pos]
                return True

            # Ctrl + W / Ctrl + Backspace -> Erase previous word
            elif event.key in (pygame.K_w, pygame.K_BACKSPACE):
                if session.cursor_pos > 0:
                    prev_pos = _find_prev_word_pos(session.input_buffer, session.cursor_pos)
                    session.input_buffer = session.input_buffer[:prev_pos] + session.input_buffer[session.cursor_pos:]
                    session.cursor_pos = prev_pos
                return True

            # Ctrl + L -> Clear screen
            elif event.key == pygame.K_l:
                session.scrollback.clear()
                return True

            # Ctrl + Left Arrow -> Jump to previous word
            elif event.key == pygame.K_LEFT:
                session.cursor_pos = _find_prev_word_pos(session.input_buffer, session.cursor_pos)
                return True

            # Ctrl + Right Arrow -> Jump to next word
            elif event.key == pygame.K_RIGHT:
                session.cursor_pos = _find_next_word_pos(session.input_buffer, session.cursor_pos)
                return True

        # 2. Enter / Return -> Execute command
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.submit_command()
            return True

        # 3. Backspace
        elif event.key == pygame.K_BACKSPACE:
            if session.cursor_pos > 0:
                session.input_buffer = session.input_buffer[:session.cursor_pos - 1] + session.input_buffer[session.cursor_pos:]
                session.cursor_pos -= 1
            return True

        # 4. Delete
        elif event.key == pygame.K_DELETE:
            if session.cursor_pos < len(session.input_buffer):
                session.input_buffer = session.input_buffer[:session.cursor_pos] + session.input_buffer[session.cursor_pos + 1:]
            return True

        # 5. Left Arrow
        elif event.key == pygame.K_LEFT:
            session.cursor_pos = max(0, session.cursor_pos - 1)
            return True

        # 6. Right Arrow
        elif event.key == pygame.K_RIGHT:
            session.cursor_pos = min(len(session.input_buffer), session.cursor_pos + 1)
            return True

        # 7. Home & End
        elif event.key == pygame.K_HOME:
            session.cursor_pos = 0
            return True
        elif event.key == pygame.K_END:
            session.cursor_pos = len(session.input_buffer)
            return True

        # 8. Up Arrow -> Command History Previous
        elif event.key == pygame.K_UP:
            prev_cmd = session.history.previous()
            if prev_cmd is not None:
                session.input_buffer = prev_cmd
                session.cursor_pos = len(session.input_buffer)
            return True

        # 9. Down Arrow -> Command History Next
        elif event.key == pygame.K_DOWN:
            next_cmd = session.history.next()
            if next_cmd is not None:
                session.input_buffer = next_cmd
                session.cursor_pos = len(session.input_buffer)
            return True

        # 10. Tab -> Autocomplete
        elif event.key == pygame.K_TAB:
            self.tab_autocomplete()
            return True

        # 11. Printable Character Input (including ? which is submitted with Enter)
        elif event.unicode and ord(event.unicode) >= 32:
            session.input_buffer = session.input_buffer[:session.cursor_pos] + event.unicode + session.input_buffer[session.cursor_pos:]
            session.cursor_pos += 1
            return True

        return False

    def submit_command(self) -> None:
        """Run the current command line against the active device CLI."""
        if not self.active_session:
            return

        session = self.active_session
        cmd = session.input_buffer.strip()
        raw_input = session.input_buffer
        prompt = self.get_prompt()

        # Echo prompt and command to scrollback
        session.scrollback.append(f"{prompt} {raw_input}")

        if cmd:
            session.history.append(cmd)
            # Check if command is a context help query (? or ending with ?)
            if cmd == "?" or cmd.endswith("?"):
                self.execute_cisco_help(cmd)
            else:
                handler = session.handler
                if handler:
                    try:
                        # Check if handler has parser returning CommandResult
                        if hasattr(handler, "parser") and hasattr(handler, "context"):
                            result = handler.parser.execute(cmd, session.device, handler.context)
                            if result.clear_screen:
                                session.scrollback.clear()
                            else:
                                session.scrollback.extend(result.output)
                                if result.exit_requested:
                                    session.scrollback.append("% Disconnected from session")
                        else:
                            output_lines = handler.execute(cmd)
                            session.scrollback.extend(output_lines)
                    except Exception as e:
                        session.scrollback.append(f"% CLI Execution error: {e}")

        # Clear input buffer
        session.input_buffer = ""
        session.cursor_pos = 0

        # Trim scrollback if overflowing
        if len(session.scrollback) > session.max_scrollback:
            session.scrollback = session.scrollback[-session.max_scrollback:]

    def execute_cisco_help(self, query: str) -> None:
        """Display detailed Cisco IOS context-sensitive help for a submitted query."""
        if not self.active_session or not self.active_session.handler:
            return

        session = self.active_session
        handler = session.handler
        registry = getattr(handler, "registry", None)
        context = getattr(handler, "context", None)

        if registry and context:
            help_lines = registry.get_cisco_help(query, context.mode)
            session.scrollback.extend(help_lines)
        else:
            session.scrollback.append("% Help not available.")

    def cancel_input(self) -> None:
        """Cancel current input line (Ctrl+C). In config modes, returns to privileged EXEC."""
        if not self.active_session:
            return
        session = self.active_session
        prompt = self.get_prompt()
        session.scrollback.append(f"{prompt} {session.input_buffer}^C")
        session.input_buffer = ""
        session.cursor_pos = 0

        # In Cisco IOS, Ctrl+C in configuration modes exits back to privileged EXEC mode
        handler = session.handler
        if handler and hasattr(handler, "context"):
            from .prompts.mode import CLIMode
            if handler.context.mode not in (CLIMode.USER_EXEC, CLIMode.PRIVILEGED_EXEC, CLIMode.PC_PROMPT):
                handler.context.end_mode()

    def tab_autocomplete(self) -> None:
        """Autocomplete commands based on active CLI mode and CommandRegistry."""
        if not self.active_session or not self.active_session.handler:
            return

        session = self.active_session
        new_line, matches = CLICompleter.complete(session.input_buffer, session.handler)

        if new_line is not None:
            session.input_buffer = new_line
            session.cursor_pos = len(session.input_buffer)
        elif len(matches) > 1:
            session.scrollback.append(f"{self.get_prompt()} {session.input_buffer}")
            session.scrollback.append("  " + "  ".join(matches))

    def show_context_help(self) -> None:
        """Legacy helper for programmatic help queries."""
        if not self.active_session:
            return
        self.execute_cisco_help(self.active_session.input_buffer + "?")

    def update(self, dt: float) -> None:
        """Update cursor blink timer."""
        self.cursor_blink_timer += dt
        if self.cursor_blink_timer >= 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_blink_timer = 0.0

"""Unit tests verifying TerminalUI scrolling, line editing, word jumping, and cursor positioning."""

import pytest
import pygame
from cli.cli_engine import CLIEngine, _find_prev_word_pos, _find_next_word_pos
from ui.terminal import TerminalUI
from devices.router import Router
from devices.device_factory import DeviceFactory


def test_word_navigation_boundaries():
    """Verify Word Jumping helper functions accurately locate word boundaries."""
    text = "show ip interface brief"
    # Position at end (24) -> previous word start is "brief" (18)
    assert _find_prev_word_pos(text, len(text)) == 18
    # From "brief" (18) -> previous word start is "interface" (8)
    assert _find_prev_word_pos(text, 18) == 8
    # From "interface" (8) -> previous word start is "ip" (5)
    assert _find_prev_word_pos(text, 8) == 5
    # From "ip" (5) -> previous word start is "show" (0)
    assert _find_prev_word_pos(text, 5) == 0
    # From start (0) -> stays 0
    assert _find_prev_word_pos(text, 0) == 0

    # Next word jumping
    assert _find_next_word_pos(text, 0) == 5    # "show " -> "ip"
    assert _find_next_word_pos(text, 5) == 8    # "ip " -> "interface"
    assert _find_next_word_pos(text, 8) == 18   # "interface " -> "brief"
    assert _find_next_word_pos(text, 18) == len(text)  # "brief" -> end (23)


def test_cli_engine_word_editing_shortcuts():
    """Verify Ctrl+W, Ctrl+Backspace, Ctrl+K, Ctrl+U, and Ctrl+L shortcuts."""
    engine = CLIEngine()
    router = DeviceFactory.create_device("Router", "R1")
    engine.attach_device(router)

    session = engine.active_session
    session.input_buffer = "configure terminal"
    session.cursor_pos = len(session.input_buffer)

    # 1. Ctrl + W -> Erase previous word ("terminal")
    event_ctrl_w = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_w, "mod": pygame.KMOD_CTRL, "unicode": ""})
    handled = engine.handle_event(event_ctrl_w)
    assert handled is True
    assert session.input_buffer == "configure "
    assert session.cursor_pos == len("configure ")

    # 2. Ctrl + K -> Erase from cursor to end of line
    session.input_buffer = "interface GigabitEthernet0/0"
    session.cursor_pos = 10  # after "interface "
    event_ctrl_k = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_k, "mod": pygame.KMOD_CTRL, "unicode": ""})
    engine.handle_event(event_ctrl_k)
    assert session.input_buffer == "interface "

    # 3. Ctrl + U -> Erase from cursor to start of line
    session.input_buffer = "show running-config"
    session.cursor_pos = 5  # after "show "
    event_ctrl_u = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_u, "mod": pygame.KMOD_CTRL, "unicode": ""})
    engine.handle_event(event_ctrl_u)
    assert session.input_buffer == "running-config"
    assert session.cursor_pos == 0

    # 4. Ctrl + L -> Clear scrollback
    session.scrollback = ["Line 1", "Line 2", "Line 3"]
    event_ctrl_l = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_l, "mod": pygame.KMOD_CTRL, "unicode": ""})
    engine.handle_event(event_ctrl_l)
    assert len(session.scrollback) == 0


def test_cli_engine_cisco_context_help_question_mark():
    """Verify typing ? appends to input buffer and pressing Enter executes Cisco IOS context-sensitive help."""
    engine = CLIEngine()
    router = DeviceFactory.create_device("Router", "R1")
    engine.attach_device(router)

    session = engine.active_session
    session.input_buffer = "sh"
    session.cursor_pos = len(session.input_buffer)

    # 1. Typing ? appends to buffer without triggering immediately
    event_q = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_QUESTION, "mod": 0, "unicode": "?"})
    handled = engine.handle_event(event_q)
    assert handled is True
    assert session.input_buffer == "sh?"

    # 2. Pressing Enter submits command and executes Cisco IOS context help
    engine.submit_command()
    assert session.input_buffer == ""  # Buffer cleared after submit
    assert len(session.scrollback) >= 2
    # Prompt echo
    assert "sh?" in session.scrollback[-2]
    # Detailed Cisco IOS help output
    assert "show" in session.scrollback[-1]

    # 3. Top-level ? execution test
    session.input_buffer = "?"
    session.cursor_pos = 1
    engine.submit_command()
    # Must contain Cisco Exec commands header and aligned command descriptions
    assert any("Exec commands:" in line for line in session.scrollback)
    assert any("enable" in line and "Turn on privileged commands" in line for line in session.scrollback)

    # 4. Subcommand help: 'show ?'
    session.input_buffer = "show ?"
    session.cursor_pos = len(session.input_buffer)
    engine.submit_command()
    assert any("interfaces" in line for line in session.scrollback)
    assert any("ip" in line for line in session.scrollback)


def test_terminal_ui_scrolling_mechanism():
    """Verify TerminalUI scroll offset, mouse wheel, PageUp/PageDown, and jump to bottom."""
    engine = CLIEngine()
    router = DeviceFactory.create_device("Router", "R1")
    engine.attach_device(router)

    # Populate 50 lines of output
    engine.scrollback = [f"Output row {i}" for i in range(50)]

    closed = False
    def on_close():
        nonlocal closed
        closed = True

    term = TerminalUI(cli_engine=engine, on_close=on_close, screen_w=1280, screen_h=720)
    term.max_scroll = 30  # Simulate max_scroll computed from viewport

    # Initial view is at bottom
    assert term.scroll_offset == 0

    # 1. Scroll Up 3 lines
    term.scroll_up(3)
    assert term.scroll_offset == 3

    # 2. Scroll Up 20 lines
    term.scroll_up(20)
    assert term.scroll_offset == 23

    # 3. Scroll Down 10 lines
    term.scroll_down(10)
    assert term.scroll_offset == 13

    # 4. Scroll to Top
    term.scroll_to_top()
    assert term.scroll_offset == term.max_scroll

    # 5. Scroll to Bottom
    term.scroll_to_bottom()
    assert term.scroll_offset == 0

    # 6. PageUp event
    ev_pgup = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_PAGEUP, "mod": 0, "unicode": ""})
    term.handle_event(ev_pgup)
    assert term.scroll_offset == 18

    # 7. Typing character auto-snaps scroll offset to bottom
    ev_type = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_a, "mod": 0, "unicode": "a"})
    term.handle_event(ev_type)
    assert term.scroll_offset == 0
    assert engine.input_buffer == "a"

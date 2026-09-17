"""Dark theme Terminal UI overlay with smooth scrolling, monospaced typography, and robust line editing."""

import math
import pygame
from typing import Callable, List, Optional, Tuple
from config.game_config import GameConfig
from config.graphics_config import GraphicsConfig
from rendering.ui_renderer import UIRenderer
from cli.cli_engine import CLIEngine


class TerminalUI:
    """Renders a modern, responsive Dark Theme Terminal window over the 3D lab."""

    def __init__(
        self,
        cli_engine: CLIEngine,
        on_close: Callable[[], None],
        screen_w: int = GameConfig.WINDOW_WIDTH,
        screen_h: int = GameConfig.WINDOW_HEIGHT
    ):
        self.cli_engine: CLIEngine = cli_engine
        self.on_close: Callable[[], None] = on_close
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.has_manually_positioned: bool = False

        # Window geometry
        self.w = min(1040, int(screen_w * 0.90))
        self.h = min(620, int(screen_h * 0.84))
        self.x = (screen_w - self.w) / 2.0
        self.y = (screen_h - self.h) / 2.0

        # Close button rect (top right of titlebar)
        self.close_btn_rect = pygame.Rect(int(self.x + self.w - 38), int(self.y + 6), 30, 24)

        # Scrolling state
        self.scroll_offset: int = 0  # 0 = live bottom view, >0 = scrolled up into history
        self._max_scroll_override: Optional[int] = None

        # Interactive scrollbar dragging state
        self.scrollbar_dragging: bool = False
        self.scrollbar_drag_y_offset: float = 0.0
        self.scrollbar_thumb_rect: pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self.scrollbar_track_rect: pygame.Rect = pygame.Rect(0, 0, 0, 0)

        # Window dragging state
        self.dragging: bool = False
        self.drag_offset_x: float = 0.0
        self.drag_offset_y: float = 0.0

        # "Jump to bottom" pill rect
        self.jump_pill_rect: pygame.Rect = pygame.Rect(0, 0, 0, 0)

    def center_window(self, screen_w: Optional[int] = None, screen_h: Optional[int] = None) -> None:
        """Center the terminal window on screen."""
        if screen_w is not None and screen_h is not None:
            self.screen_w = screen_w
            self.screen_h = screen_h
        self.w = min(1040, int(self.screen_w * 0.90))
        self.h = min(620, int(self.screen_h * 0.84))
        self.x = (self.screen_w - self.w) / 2.0
        self.y = (self.screen_h - self.h) / 2.0
        self.close_btn_rect = pygame.Rect(int(self.x + self.w - 38), int(self.y + 6), 30, 24)
        self.has_manually_positioned = False

    @property
    def max_scroll(self) -> int:
        if self._max_scroll_override is not None:
            return self._max_scroll_override
        if not self.cli_engine.scrollback:
            return 0
        char_w = 8
        line_height = 20
        status_bar_h = 24
        title_h = 36
        max_content_w = self.w - 38
        max_cols = max(30, int(max_content_w / char_w))
        total_lines = 0
        for l in self.cli_engine.scrollback:
            total_lines += max(1, math.ceil(len(l) / max_cols))
        avail_viewport_h = self.h - title_h - status_bar_h - line_height - 20
        max_visible_lines = max(5, int(avail_viewport_h / line_height))
        return max(0, total_lines - max_visible_lines)

    @max_scroll.setter
    def max_scroll(self, val: int) -> None:
        self._max_scroll_override = val

    def resize(self, width: int, height: int) -> None:
        self.screen_w = width
        self.screen_h = height
        self.w = min(1040, int(width * 0.90))
        self.h = min(620, int(height * 0.84))
        if not self.has_manually_positioned:
            self.x = (width - self.w) / 2.0
            self.y = (height - self.h) / 2.0
        else:
            self.x = max(10, min(width - self.w - 10, self.x))
            self.y = max(10, min(height - self.h - 10, self.y))
        self.close_btn_rect = pygame.Rect(int(self.x + self.w - 38), int(self.y + 6), 30, 24)

    def scroll_up(self, lines: int = 3) -> None:
        """Scroll up into history."""
        self.scroll_offset = min(self.max_scroll, self.scroll_offset + lines)

    def scroll_down(self, lines: int = 3) -> None:
        """Scroll down towards active prompt."""
        self.scroll_offset = max(0, self.scroll_offset - lines)

    def scroll_to_top(self) -> None:
        """Scroll to the very beginning of the session scrollback."""
        self.scroll_offset = self.max_scroll

    def scroll_to_bottom(self) -> None:
        """Snap immediately to the active live input line."""
        self.scroll_offset = 0

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Process keyboard navigation, text editing, mouse dragging, and wheel scrolling."""
        # 1. ESC -> Close terminal
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.on_close()
            return True

        # 2. Mouse Wheel -> History Scrolling
        if event.type == pygame.MOUSEWHEEL:
            term_rect = pygame.Rect(int(self.x), int(self.y), int(self.w), int(self.h))
            mouse_pos = pygame.mouse.get_pos()
            if term_rect.collidepoint(mouse_pos):
                if event.y > 0:
                    self.scroll_up(3 * event.y)
                elif event.y < 0:
                    self.scroll_down(3 * abs(event.y))
                return True

        # 3. Mouse Button Down
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # Close button [X]
            if self.close_btn_rect.collidepoint(mx, my):
                self.on_close()
                return True

            # Jump to bottom pill
            if self.scroll_offset > 0 and self.jump_pill_rect.collidepoint(mx, my):
                self.scroll_to_bottom()
                return True

            # Scrollbar thumb click / drag
            if self.scrollbar_thumb_rect.collidepoint(mx, my):
                self.scrollbar_dragging = True
                self.scrollbar_drag_y_offset = my - self.scrollbar_thumb_rect.y
                return True

            # Scrollbar track click (jump page)
            if self.scrollbar_track_rect.collidepoint(mx, my):
                track_h = self.scrollbar_track_rect.height
                rel_y = my - self.scrollbar_track_rect.y
                progress = max(0.0, min(1.0, rel_y / float(track_h)))
                # progress 1.0 = bottom (offset 0), progress 0.0 = top (offset max_scroll)
                self.scroll_offset = int((1.0 - progress) * self.max_scroll)
                return True

            # Titlebar window dragging
            titlebar_rect = pygame.Rect(int(self.x), int(self.y), int(self.w), 36)
            if titlebar_rect.collidepoint(mx, my):
                self.dragging = True
                self.drag_offset_x = mx - self.x
                self.drag_offset_y = my - self.y
                return True

            # Click inside terminal window absorbs event
            term_rect = pygame.Rect(int(self.x), int(self.y), int(self.w), int(self.h))
            if term_rect.collidepoint(mx, my):
                return True

        # 4. Mouse Button Up
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
            self.scrollbar_dragging = False

        # 5. Mouse Motion
        elif event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            if self.dragging:
                self.x = max(10, min(self.screen_w - self.w - 10, mx - self.drag_offset_x))
                self.y = max(10, min(self.screen_h - self.h - 10, my - self.drag_offset_y))
                self.close_btn_rect = pygame.Rect(int(self.x + self.w - 38), int(self.y + 6), 30, 24)
                return True

            if self.scrollbar_dragging and self.max_scroll > 0:
                track = self.scrollbar_track_rect
                thumb_h = self.scrollbar_thumb_rect.height
                avail_h = track.height - thumb_h
                if avail_h > 0:
                    thumb_top = max(track.y, min(track.y + avail_h, my - self.scrollbar_drag_y_offset))
                    progress = (thumb_top - track.y) / float(avail_h)
                    self.scroll_offset = int((1.0 - progress) * self.max_scroll)
                return True

        # 6. Keyboard Page Navigation
        if event.type == pygame.KEYDOWN:
            shift_pressed = bool(event.mod & pygame.KMOD_SHIFT)

            if event.key == pygame.K_PAGEUP:
                self.scroll_up(18)
                return True
            elif event.key == pygame.K_PAGEDOWN:
                self.scroll_down(18)
                return True
            elif event.key == pygame.K_HOME and shift_pressed:
                self.scroll_to_top()
                return True
            elif event.key == pygame.K_END and shift_pressed:
                self.scroll_to_bottom()
                return True

            # Any text modification, command submission, or backspace auto-snaps view to bottom
            if (
                event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_BACKSPACE, pygame.K_DELETE, pygame.K_TAB)
                or (event.unicode and ord(event.unicode) >= 32)
                or (event.mod & pygame.KMOD_CTRL and event.key in (pygame.K_v, pygame.K_c, pygame.K_u, pygame.K_k, pygame.K_w, pygame.K_l))
            ):
                self.scroll_offset = 0

        # 7. Delegate input editing to CLI Engine
        handled = self.cli_engine.handle_event(event)

        # Check if user typed exit and got disconnected
        if self.cli_engine.scrollback and "% Disconnected" in self.cli_engine.scrollback[-1]:
            self.on_close()
            return True

        return handled

    def update(self, dt: float) -> None:
        self.cli_engine.update(dt)

    def _wrap_line(self, line: str, max_chars: int) -> List[str]:
        """Wrap long output line into multiple display lines."""
        if len(line) <= max_chars or max_chars <= 10:
            return [line]
        wrapped = []
        start = 0
        while start < len(line):
            wrapped.append(line[start:start + max_chars])
            start += max_chars
        return wrapped

    def render(self, ui: UIRenderer, screen_w: Optional[int] = None, screen_h: Optional[int] = None) -> None:
        # Dynamically adapt to active viewport dimensions if passed
        if screen_w is not None and screen_h is not None:
            if screen_w != self.screen_w or screen_h != self.screen_h:
                self.resize(screen_w, screen_h)

        # 1. Dark Backdrop Dimmer across full screen
        ui.draw_rect(0, 0, self.screen_w, self.screen_h, (10, 15, 25), alpha=0.68)

        # 2. Main Terminal Window Frame (Drop shadow + rounded card)
        ui.draw_rect(self.x + 4, self.y + 8, self.w, self.h, (0, 0, 0), alpha=0.42, corner_radius=10.0)
        ui.draw_rect(self.x, self.y, self.w, self.h, GraphicsConfig.COLOR_TERM_BG, alpha=0.98, corner_radius=10.0)
        ui.draw_rect_outline(self.x, self.y, self.w, self.h, GraphicsConfig.COLOR_TERM_BORDER, line_width=1.5)

        # 3. Terminal Titlebar
        title_h = 36
        ui.draw_rect(self.x, self.y, self.w, title_h, (25, 30, 42), alpha=1.0, corner_radius=10.0)
        ui.draw_rect(self.x, self.y + title_h - 4, self.w, 4, (25, 30, 42), alpha=1.0)
        ui.draw_rect_outline(self.x, self.y, self.w, title_h, GraphicsConfig.COLOR_TERM_BORDER, line_width=1.0)

        # Title Icon & Text
        dev_name = self.cli_engine.active_device.hostname if self.cli_engine.active_device else "Console"
        dev_type = self.cli_engine.active_device.device_type if self.cli_engine.active_device else "Serial"
        # Connection status dot
        ui.draw_rect(self.x + 16, self.y + 13, 10, 10, (34, 197, 94), corner_radius=5.0)
        title_str = f"Console Session - [{dev_name}] ({dev_type} Virtual Terminal)"
        ui.draw_text(title_str, self.x + 34, self.y + title_h / 2.0, font_size=13, color=(210, 225, 240), center_y=True)

        # Close Button [X]
        cb = self.close_btn_rect
        ui.draw_rect(cb.x, cb.y, cb.w, cb.h, (220, 53, 69), alpha=0.88, corner_radius=4.0)
        ui.draw_text("X", cb.x + cb.w / 2.0, cb.y + cb.h / 2.0, font_size=12, color=(255, 255, 255), center_x=True, center_y=True)

        # 4. Monospaced Geometry & Dimensions
        font_size = 14
        char_w, char_h = ui.measure_text("M", font_size, mono=True)
        char_w = max(7, char_w)
        line_height = 20

        content_x = self.x + 16
        content_y = self.y + title_h + 10
        status_bar_h = 24

        # Maximum character columns available before hitting scrollbar margin
        max_content_w = self.w - 38
        max_cols = max(30, int(max_content_w / char_w))

        # 5. Prepare Wrapped Display Lines
        display_lines: List[Tuple[str, Tuple[int, int, int]]] = []
        for raw_line in self.cli_engine.scrollback:
            # Color classification
            if raw_line.startswith("%"):
                color = GraphicsConfig.COLOR_TERM_ERROR
            elif "Reply from" in raw_line:
                color = GraphicsConfig.COLOR_TERM_SUCCESS
            elif raw_line.startswith("!"):
                color = (120, 140, 165)
            elif raw_line.endswith("?"):
                color = (56, 189, 248)
            else:
                color = GraphicsConfig.COLOR_TERM_TEXT

            for sub_line in self._wrap_line(raw_line, max_cols):
                display_lines.append((sub_line, color))

        # Max lines that fit in the viewport above the input area
        avail_viewport_h = self.h - title_h - status_bar_h - line_height - 20
        max_visible_lines = max(5, int(avail_viewport_h / line_height))

        total_lines_count = len(display_lines)
        self.max_scroll = max(0, total_lines_count - max_visible_lines)
        self.scroll_offset = max(0, min(self.max_scroll, self.scroll_offset))

        # Determine visible slice
        if total_lines_count <= max_visible_lines:
            lines_to_render = display_lines
        else:
            end_idx = total_lines_count - self.scroll_offset
            start_idx = max(0, end_idx - max_visible_lines)
            lines_to_render = display_lines[start_idx:end_idx]

        # Render visible scrollback lines
        curr_y = content_y
        for text, col in lines_to_render:
            ui.draw_text(text, content_x, curr_y, font_size=font_size, color=col, mono=True)
            curr_y += line_height

        # 6. Active Command Input Line with Horizontal Sliding Viewport
        # Position input line cleanly below visible lines or anchored at bottom of content area
        input_y = content_y + min(len(lines_to_render), max_visible_lines) * line_height
        # Clamp input_y to ensure it never collides with status bar
        max_input_y = self.y + self.h - status_bar_h - line_height - 4
        input_y = min(input_y, max_input_y)

        # Subtle separator line before input area if scrolled up
        if self.scroll_offset > 0:
            ui.draw_rect(self.x + 12, input_y - 3, self.w - 24, 1, (45, 55, 75), alpha=0.8)

        # Prompt Text with single trailing space
        prompt = self.cli_engine.get_prompt() + " "
        prompt_w, _ = ui.draw_text(prompt, content_x, input_y, font_size=font_size, color=GraphicsConfig.COLOR_TERM_PROMPT, mono=True)

        inp_text = self.cli_engine.input_buffer
        cursor_pos = self.cli_engine.cursor_pos

        # Available horizontal pixel width for the input text
        input_field_x = content_x + prompt_w
        available_input_w = max_content_w - prompt_w
        max_input_chars = max(10, int(available_input_w / char_w))

        # Horizontal sliding window: if user types a very long command, keep cursor in view!
        if len(inp_text) <= max_input_chars:
            disp_inp = inp_text
            cur_offset_idx = cursor_pos
            has_left_overflow = False
            has_right_overflow = False
        else:
            # Shift window so cursor stays with 5 chars of breathing room
            start_char = max(0, cursor_pos - max_input_chars + 6)
            end_char = start_char + max_input_chars
            disp_inp = inp_text[start_char:end_char]
            cur_offset_idx = cursor_pos - start_char
            has_left_overflow = (start_char > 0)
            has_right_overflow = (end_char < len(inp_text))

        # Exact pixel position of cursor calculated from prefix measurement
        cursor_prefix = disp_inp[:cur_offset_idx]
        cur_offset_px, _ = ui.measure_text(cursor_prefix, font_size=font_size, mono=True)
        cur_pixel_x = input_field_x + cur_offset_px

        # Draw left/right overflow arrows if text exceeds terminal width
        if has_left_overflow:
            ui.draw_text("<", content_x + prompt_w - 12, input_y, font_size=font_size, color=(245, 158, 11), mono=True)
        if has_right_overflow:
            ui.draw_text(">", self.x + max_content_w, input_y, font_size=font_size, color=(245, 158, 11), mono=True)

        # Draw visible input buffer
        ui.draw_text(disp_inp, input_field_x, input_y, font_size=font_size, color=GraphicsConfig.COLOR_TERM_TEXT, mono=True)

        # 7. Blinking Block Cursor with Inverted Character Display
        if self.cli_engine.cursor_visible:
            if cur_offset_idx < len(disp_inp):
                char_under = disp_inp[cur_offset_idx]
                cw, _ = ui.measure_text(char_under, font_size=font_size, mono=True)
                cur_block_w = max(char_w, cw)
            else:
                char_under = ""
                cur_block_w = char_w

            # Glowing cyan cursor block
            ui.draw_rect(cur_pixel_x, input_y + 1, cur_block_w, line_height - 3, (56, 189, 248), alpha=0.92, corner_radius=1.5)
            # Invert character inside block cursor for authentic VT100 readability
            if char_under:
                ui.draw_text(char_under, cur_pixel_x, input_y, font_size=font_size, color=(15, 23, 42), mono=True)

        # 8. Interactive Scrollbar on Right Margin
        track_w = 6
        track_x = self.x + self.w - 14
        track_y = content_y
        track_h = avail_viewport_h + line_height
        self.scrollbar_track_rect = pygame.Rect(int(track_x - 3), int(track_y), track_w + 6, int(track_h))

        # Draw track rail
        ui.draw_rect(track_x, track_y, track_w, track_h, (22, 27, 38), corner_radius=3.0)

        if total_lines_count > max_visible_lines:
            ratio = max(0.08, min(1.0, max_visible_lines / float(total_lines_count)))
            thumb_h = max(24, int(track_h * ratio))
            avail_travel = track_h - thumb_h
            # progress: 0.0 at top (max_scroll), 1.0 at bottom (scroll_offset = 0)
            progress = 1.0 - (self.scroll_offset / float(self.max_scroll))
            thumb_y = track_y + avail_travel * progress
            self.scrollbar_thumb_rect = pygame.Rect(int(track_x - 2), int(thumb_y), track_w + 4, thumb_h)

            thumb_color = (120, 140, 175) if (self.scrollbar_dragging or self.scrollbar_thumb_rect.collidepoint(pygame.mouse.get_pos())) else (75, 88, 108)
            ui.draw_rect(track_x, thumb_y, track_w, thumb_h, thumb_color, alpha=0.95, corner_radius=3.0)
        else:
            self.scrollbar_thumb_rect = pygame.Rect(0, 0, 0, 0)

        # 9. Scrolled-Up Notification Pill
        if self.scroll_offset > 0:
            pill_w = 260
            pill_h = 26
            pill_x = self.x + self.w - pill_w - 28
            pill_y = input_y - 32
            self.jump_pill_rect = pygame.Rect(int(pill_x), int(pill_y), pill_w, pill_h)

            ui.draw_rect(pill_x, pill_y, pill_w, pill_h, (15, 23, 42), alpha=0.94, corner_radius=13.0)
            ui.draw_rect_outline(pill_x, pill_y, pill_w, pill_h, (56, 189, 248), line_width=1.2)
            pill_text = f"v Scrolled up (+{self.scroll_offset} lines) - Click to return"
            ui.draw_text(pill_text, pill_x + pill_w / 2.0, pill_y + pill_h / 2.0, font_size=11, color=(56, 189, 248), center_x=True, center_y=True)
        else:
            self.jump_pill_rect = pygame.Rect(0, 0, 0, 0)

        # 10. Bottom Status Bar & Shortcuts Legend
        status_y = self.y + self.h - status_bar_h
        ui.draw_rect(self.x, status_y, self.w, status_bar_h, (20, 24, 34), alpha=1.0, corner_radius=10.0)
        # Flatten top corners of status bar
        ui.draw_rect(self.x, status_y, self.w, 4, (20, 24, 34), alpha=1.0)
        ui.draw_rect_outline(self.x, status_y, self.w, status_bar_h, GraphicsConfig.COLOR_TERM_BORDER, line_width=1.0)

        # Right status telemetry (Strictly right-aligned inside the status bar)
        conn_info = "Line Con 0 | 9600 8N1"
        conn_w, _ = ui.measure_text(conn_info, font_size=11)
        conn_x = self.x + self.w - 16 - conn_w
        ui.draw_text(conn_info, conn_x, status_y + status_bar_h / 2.0, font_size=11, color=(100, 116, 139), center_y=True)

        # Shortcuts on left, avoiding overlap with conn_info
        avail_short_w = (conn_x - (self.x + 14)) - 10
        full_shortcuts = "[Tab] Complete   [?] Help   [Ctrl+C] Cancel   [Ctrl+L] Clear   [PgUp/PgDn] Scroll   [ESC] Exit"
        if ui.measure_text(full_shortcuts, 11)[0] <= avail_short_w:
            shortcuts = full_shortcuts
        else:
            shortcuts = "[Tab] Complete   [?] Help   [Ctrl+C] Cancel   [ESC] Exit"
        ui.draw_text(shortcuts, self.x + 14, status_y + status_bar_h / 2.0, font_size=11, color=(130, 145, 168), center_y=True)

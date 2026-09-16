"""Bottom-right real-time Device and Port Overview HUD card."""

from typing import Optional
from config.game_config import GameConfig
from config.graphics_config import GraphicsConfig
from rendering.ui_renderer import UIRenderer
from player.interaction import InteractionTarget
from devices.port import Port, AdminStatus, LinkStatus


class OverviewHUD:
    """Non-blocking bottom-right HUD card showing real-time device status and port overview."""

    def __init__(self, screen_w: int = GameConfig.WINDOW_WIDTH, screen_h: int = GameConfig.WINDOW_HEIGHT):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.card_w = 380
        self.card_h = 240

    def resize(self, width: int, height: int) -> None:
        self.screen_w = width
        self.screen_h = height

    def render(
        self,
        ui: UIRenderer,
        target: InteractionTarget,
        mode: str = "CABLING_CLI",
        held_cable_port: Optional[Port] = None
    ) -> None:
        """Render the bottom-right overview card if aiming at a rack slot or device."""
        if target.target_type not in ("PORT", "DEVICE", "RACK"):
            return

        # Placement in bottom-right corner, leaving space for bottom control bar
        card_x = self.screen_w - self.card_w - 20
        card_y = self.screen_h - self.card_h - 42

        # Card Background (Translucent dark slate with rounded corners)
        ui.draw_rect(card_x, card_y, self.card_w, self.card_h, (15, 23, 42), alpha=0.92, corner_radius=12.0)
        border_color = (56, 189, 248) if mode == "CABLING_CLI" else (245, 158, 11)
        ui.draw_rect_outline(card_x, card_y, self.card_w, self.card_h, border_color, line_width=1.5)

        # 1. When aiming at a Device or Port
        if target.device:
            dev = target.device
            rack_name = target.rack.rack_id if target.rack else "Rack"
            u_range = f"U{dev.start_u}-U{dev.start_u + dev.u_height - 1}" if dev.start_u else "Unmounted"

            # Header row: Device Name & Type
            ui.draw_text(
                f"{dev.hostname} ({dev.device_type})",
                card_x + 16, card_y + 22,
                font_size=16,
                color=(255, 255, 255)
            )

            # Location badge & Power
            ui.draw_text(
                f"{rack_name} [{u_range}]",
                card_x + 16, card_y + 44,
                font_size=12,
                color=(148, 163, 184)
            )
            power_str = "POWER ON" if dev.power_state else "OFF"
            power_col = (74, 222, 128) if dev.power_state else (239, 68, 68)
            ui.draw_text(
                f"● {power_str}",
                card_x + self.card_w - 16, card_y + 22,
                font_size=12,
                color=power_col,
                center_x=False
            )

            # Divider line
            ui.draw_rect(card_x + 16, card_y + 60, self.card_w - 32, 1, (51, 65, 85), alpha=0.8)

            # Active targeted port highlight banner (if aiming directly at a port)
            if target.port:
                p = target.port
                p_box_y = card_y + 68
                ui.draw_rect(card_x + 14, p_box_y, self.card_w - 28, 48, (30, 41, 59), alpha=0.9, corner_radius=6.0)
                ui.draw_rect_outline(card_x + 14, p_box_y, self.card_w - 28, 48, (56, 189, 248), line_width=1.0)

                # Port name and Admin/Link status
                status_color = (74, 222, 128) if p.is_operational else (239, 68, 68)
                ui.draw_text(
                    f"Target Port: {p.port_name}",
                    card_x + 22, p_box_y + 14,
                    font_size=13,
                    color=(255, 255, 255)
                )
                ui.draw_text(
                    f"[{p.admin_status.value.upper()} / {p.link_status.value.upper()}]",
                    card_x + 175, p_box_y + 14,
                    font_size=12,
                    color=status_color
                )

                # Connected partner info
                if p.connected_port and p.connected_port.device_ref:
                    conn_text = f"Connected: {p.connected_port.device_ref.hostname} -> {p.connected_port.port_name}"
                    conn_col = (147, 197, 253)
                else:
                    conn_text = "No Cable Plugged In"
                    conn_col = (148, 163, 184)
                ui.draw_text(conn_text, card_x + 22, p_box_y + 32, font_size=11, color=conn_col)

                ports_start_y = card_y + 124
                max_list = 3
            else:
                ports_start_y = card_y + 70
                max_list = 5

            # List of ports overview
            ui.draw_text("Ports Overview:", card_x + 16, ports_start_y, font_size=12, color=(148, 163, 184))
            port_y = ports_start_y + 18
            ports = list(dev.ports.values())[:max_list]

            for p in ports:
                is_active = p.is_operational
                dot_col = (74, 222, 128) if is_active else (
                    (245, 158, 11) if p.admin_status == AdminStatus.UP else (148, 163, 184)
                )
                ui.draw_text(f"●", card_x + 18, port_y, font_size=10, color=dot_col)

                if p.connected_port and p.connected_port.device_ref:
                    dest = f"-> {p.connected_port.device_ref.hostname}:{p.connected_port.port_name}"
                else:
                    dest = "disconnected"

                p_str = f"{p.port_name:<8} {dest}"
                ui.draw_text(p_str, card_x + 32, port_y, font_size=11, color=(226, 232, 240))
                port_y += 18

            if len(dev.ports) > max_list:
                ui.draw_text(
                    f"+ {len(dev.ports) - max_list} more ports...",
                    card_x + 32, port_y,
                    font_size=10,
                    color=(100, 116, 139)
                )

            # Footer / Action Hints
            ui.draw_rect(card_x + 16, card_y + self.card_h - 36, self.card_w - 32, 1, (51, 65, 85), alpha=0.8)
            if mode == "CABLING_CLI":
                if held_cable_port:
                    hint = f"[F] Plug Cable into Port   [RMB] Cancel"
                    hint_col = (250, 204, 21)
                else:
                    hint = f"[E] Open CLI   [F] Cable Action   [R] Mode"
                    hint_col = (56, 189, 248)
            else:
                hint = f"[E] Remove Device from Rack   [R] Mode"
                hint_col = (245, 158, 11)

            ui.draw_text(
                hint,
                card_x + self.card_w / 2.0, card_y + self.card_h - 18,
                font_size=12,
                color=hint_col,
                center_x=True,
                center_y=True
            )

        # 2. When aiming at an empty Rack slot
        elif target.rack and target.targeted_u:
            rack_id = target.rack.rack_id
            u_slot = target.targeted_u

            ui.draw_text(
                f"{rack_id} - Slot U{u_slot}",
                card_x + 16, card_y + 24,
                font_size=16,
                color=(255, 255, 255)
            )
            ui.draw_text(
                "Status: Available (Empty Slot)",
                card_x + 16, card_y + 48,
                font_size=12,
                color=(74, 222, 128)
            )

            ui.draw_rect(card_x + 16, card_y + 68, self.card_w - 32, 1, (51, 65, 85), alpha=0.8)

            ui.draw_text(
                "Slot Specifications:",
                card_x + 16, card_y + 82,
                font_size=13,
                color=(226, 232, 240)
            )
            ui.draw_text(
                f"Standard 19-inch EIA-310-D rack mounting unit.",
                card_x + 16, card_y + 104,
                font_size=11,
                color=(148, 163, 184)
            )
            ui.draw_text(
                "Supports Router (2U), Switch (1U), or PC (2U).",
                card_x + 16, card_y + 124,
                font_size=11,
                color=(148, 163, 184)
            )

            # Footer / Action Hints
            ui.draw_rect(card_x + 16, card_y + self.card_h - 36, self.card_w - 32, 1, (51, 65, 85), alpha=0.8)
            if mode == "HARDWARE_MGMT":
                hint = f"[E] Install Device at U{u_slot}   [R] Mode"
                hint_col = (245, 158, 11)
            else:
                hint = f"Press [R] to switch to Hardware Mode"
                hint_col = (148, 163, 184)

            ui.draw_text(
                hint,
                card_x + self.card_w / 2.0, card_y + self.card_h - 18,
                font_size=12,
                color=hint_col,
                center_x=True,
                center_y=True
            )

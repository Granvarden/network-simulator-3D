"""Interface configuration commands."""

import re
from typing import Any, List
from ..prompts.mode import CLIMode
from ..command_result import CommandResult
from ..command_registry import CommandRegistry
from ..cli_context import CLIContext
from devices.port import AdminStatus
from services.interface_service import InterfaceService


class InterfaceCommands:
    """Handles interface selection and interface sub-configuration commands."""

    @classmethod
    def register_commands(cls, registry: CommandRegistry) -> None:
        # 1. interface <name>
        registry.register(
            tokens=["interface"],
            handler=cls.handle_interface,
            modes={CLIMode.GLOBAL_CONFIG},
            help_summary="Select an interface to configure",
            min_args=1,
            max_args=1
        )

        # 2. ip address <ip> <mask>
        registry.register(
            tokens=["ip", "address"],
            handler=cls.handle_ip_address,
            modes={CLIMode.INTERFACE_CONFIG},
            help_summary="Set the IPv4 address of an interface",
            min_args=2,
            max_args=2
        )

        # 3. no ip address
        registry.register(
            tokens=["no", "ip", "address"],
            handler=cls.handle_no_ip_address,
            modes={CLIMode.INTERFACE_CONFIG},
            help_summary="Remove IP address from interface",
            min_args=0,
            max_args=2
        )

        # 4. shutdown
        registry.register(
            tokens=["shutdown"],
            handler=cls.handle_shutdown,
            modes={CLIMode.INTERFACE_CONFIG},
            help_summary="Shut down the selected interface",
            min_args=0,
            max_args=0
        )

        # 5. no shutdown
        registry.register(
            tokens=["no", "shutdown"],
            handler=cls.handle_no_shutdown,
            modes={CLIMode.INTERFACE_CONFIG},
            help_summary="Enable the selected interface",
            min_args=0,
            max_args=0
        )

        # 6. description <text>
        registry.register(
            tokens=["description"],
            handler=cls.handle_description,
            modes={CLIMode.INTERFACE_CONFIG},
            help_summary="Set interface description string",
            min_args=1,
            max_args=None
        )

        # 7. no description
        registry.register(
            tokens=["no", "description"],
            handler=cls.handle_no_description,
            modes={CLIMode.INTERFACE_CONFIG},
            help_summary="Remove interface description",
            min_args=0,
            max_args=None
        )

        # 8. switchport mode <access|trunk>
        registry.register(
            tokens=["switchport", "mode"],
            handler=cls.handle_switchport_mode,
            modes={CLIMode.INTERFACE_CONFIG},
            help_summary="Set switchport mode (access or trunk)",
            min_args=1,
            max_args=1
        )

        # 9. switchport access vlan <vlan_id>
        registry.register(
            tokens=["switchport", "access", "vlan"],
            handler=cls.handle_switchport_access_vlan,
            modes={CLIMode.INTERFACE_CONFIG},
            help_summary="Set access VLAN for switchport",
            min_args=1,
            max_args=1
        )

        # 10. switchport trunk allowed vlan <vlans>
        registry.register(
            tokens=["switchport", "trunk", "allowed", "vlan"],
            handler=cls.handle_switchport_trunk_allowed_vlan,
            modes={CLIMode.INTERFACE_CONFIG},
            help_summary="Set allowed VLANs on trunk port",
            min_args=1,
            max_args=None
        )

    @staticmethod
    def handle_interface(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        if_name = args[0]
        port = InterfaceService.get_port(device, if_name)
        if not port:
            return CommandResult.error(f"% Invalid interface {if_name}")

        context.enter_mode(CLIMode.INTERFACE_CONFIG, interface=port.canonical_name)
        return CommandResult.ok()

    @staticmethod
    def handle_ip_address(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        if not context.active_interface:
            return CommandResult.error("% No interface selected")

        ip, mask = args[0], args[1]
        ok, msg = InterfaceService.set_ip_address(device, context.active_interface, ip, mask)
        if not ok:
            return CommandResult.error(msg)
        return CommandResult.ok()

    @staticmethod
    def handle_no_ip_address(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        if not context.active_interface:
            return CommandResult.error("% No interface selected")

        ok, msg = InterfaceService.remove_ip_address(device, context.active_interface)
        if not ok:
            return CommandResult.error(msg)
        return CommandResult.ok()

    @staticmethod
    def handle_shutdown(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        if not context.active_interface:
            return CommandResult.error("% No interface selected")

        ok, msg = InterfaceService.set_admin_status(device, context.active_interface, AdminStatus.DOWN)
        output = [msg] if msg else []
        return CommandResult.ok(output=output)

    @staticmethod
    def handle_no_shutdown(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        if not context.active_interface:
            return CommandResult.error("% No interface selected")

        ok, msg = InterfaceService.set_admin_status(device, context.active_interface, AdminStatus.UP)
        output = msg.split("\n") if msg else []
        return CommandResult.ok(output=output)

    @staticmethod
    def handle_description(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        if not context.active_interface:
            return CommandResult.error("% No interface selected")

        desc = " ".join(args)
        ok, msg = InterfaceService.set_description(device, context.active_interface, desc)
        if not ok:
            return CommandResult.error(msg)
        return CommandResult.ok()

    @staticmethod
    def handle_no_description(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        if not context.active_interface:
            return CommandResult.error("% No interface selected")

        ok, msg = InterfaceService.set_description(device, context.active_interface, "")
        if not ok:
            return CommandResult.error(msg)
        return CommandResult.ok()

    @staticmethod
    def handle_switchport_mode(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        if not context.active_interface:
            return CommandResult.error("% No interface selected")

        mode = args[0]
        ok, msg = InterfaceService.set_switchport_mode(device, context.active_interface, mode)
        if not ok:
            return CommandResult.error(msg)
        return CommandResult.ok()

    @staticmethod
    def handle_switchport_access_vlan(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        if not context.active_interface:
            return CommandResult.error("% No interface selected")

        try:
            vlan_id = int(args[0])
        except ValueError:
            return CommandResult.error(f"% Invalid VLAN ID: {args[0]}")

        ok, msg = InterfaceService.set_switchport_access_vlan(device, context.active_interface, vlan_id)
        if not ok:
            return CommandResult.error(msg)
        output = [msg] if msg else []
        return CommandResult.ok(output=output)

    @staticmethod
    def handle_switchport_trunk_allowed_vlan(device: Any, context: CLIContext, args: List[str]) -> CommandResult:
        if not context.active_interface:
            return CommandResult.error("% No interface selected")

        raw = "".join(args)
        # Parse comma-separated and ranges like 10,20,30-40
        vlans = []
        for part in raw.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                bounds = part.split("-")
                try:
                    start, end = int(bounds[0]), int(bounds[1])
                    vlans.extend(range(start, end + 1))
                except (ValueError, IndexError):
                    return CommandResult.error(f"% Invalid VLAN range: {part}")
            else:
                try:
                    vlans.append(int(part))
                except ValueError:
                    return CommandResult.error(f"% Invalid VLAN ID: {part}")

        ok, msg = InterfaceService.set_switchport_trunk_allowed_vlans(device, context.active_interface, vlans)
        if not ok:
            return CommandResult.error(msg)
        return CommandResult.ok()

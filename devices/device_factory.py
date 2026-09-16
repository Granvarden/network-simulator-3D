"""Device factory for generating configured network devices."""

from typing import Optional
from .device import Device
from .router import Router
from .switch import Switch
from .pc import PC


class DeviceFactory:
    """Factory to instantiate unique network devices."""

    _router_counter: int = 1
    _switch_counter: int = 1
    _pc_counter: int = 1

    @classmethod
    def create_device(cls, device_type: str, custom_hostname: Optional[str] = None) -> Device:
        """Create a new device instance by type string ('Router', 'Switch', 'PC')."""
        dt = device_type.strip().lower()

        if dt in ("router", "r"):
            dev_id = f"r{cls._router_counter}"
            hostname = custom_hostname or f"Router{cls._router_counter}"
            cls._router_counter += 1
            return Router(device_id=dev_id, hostname=hostname)

        elif dt in ("switch", "sw"):
            dev_id = f"sw{cls._switch_counter}"
            hostname = custom_hostname or f"Switch{cls._switch_counter}"
            cls._switch_counter += 1
            return Switch(device_id=dev_id, hostname=hostname)

        elif dt in ("pc", "host", "computer"):
            dev_id = f"pc{cls._pc_counter}"
            hostname = custom_hostname or f"PC{cls._pc_counter}"
            cls._pc_counter += 1
            return PC(device_id=dev_id, hostname=hostname)

        else:
            raise ValueError(f"Unknown device type: '{device_type}'")

    @classmethod
    def reset_counters(cls) -> None:
        """Reset sequence counters for fresh game/tests."""
        cls._router_counter = 1
        cls._switch_counter = 1
        cls._pc_counter = 1

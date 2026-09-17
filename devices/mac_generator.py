"""Deterministic MAC Address Generator and Validator.

Generates RFC-compliant locally administered unicast MAC addresses.
Format: 02:00:00:XX:YY:ZZ
- First octet 0x02: Bit 1 = 1 (Locally Administered), Bit 0 = 0 (Unicast).
- XX, YY: Deterministic 2-byte hash derived from device identifier.
- ZZ: Port index (0-255).
"""

import hashlib
import re
from typing import Optional


class MacAddressGenerator:
    """Generates and validates deterministic MAC addresses."""

    MAC_REGEX = re.compile(
        r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
    )
    CISCO_MAC_REGEX = re.compile(
        r"^([0-9A-Fa-f]{4}\.){2}([0-9A-Fa-f]{4})$"
    )

    @classmethod
    def generate(cls, device_id: str, port_idx: int) -> str:
        """
        Generate a deterministic, RFC-compliant locally administered unicast MAC address.
        
        Args:
            device_id: Unique device identifier string (e.g. 'router_1', 'r1', 'Switch_A')
            port_idx: Interface index on device (0 to 255)
            
        Returns:
            Formatted MAC address string: '02:00:00:xx:yy:zz'
        """
        digest = hashlib.md5(device_id.encode("utf-8")).digest()
        xx = digest[0]
        yy = digest[1]
        zz = port_idx & 0xFF
        return f"02:00:00:{xx:02x}:{yy:02x}:{zz:02x}"

    @classmethod
    def validate(cls, mac: str) -> bool:
        """Validate if string is a valid MAC address (standard or Cisco format)."""
        if not mac or not isinstance(mac, str):
            return False
        clean = mac.strip()
        return bool(cls.MAC_REGEX.match(clean) or cls.CISCO_MAC_REGEX.match(clean))

    @classmethod
    def normalize(cls, mac: str) -> str:
        """
        Normalize any valid MAC representation to lowercase colon-delimited format: 'xx:xx:xx:xx:xx:xx'.
        """
        clean = re.sub(r"[\.\-:]", "", mac.strip().lower())
        if len(clean) != 12 or not all(c in "0123456789abcdef" for c in clean):
            raise ValueError(f"Invalid MAC address format: {mac}")
        return ":".join(clean[i:i + 2] for i in range(0, 12, 2))

    @classmethod
    def to_cisco_format(cls, mac: str) -> str:
        """
        Format MAC address in Cisco IOS format: 'xxxx.yyyy.zzzz'.
        """
        clean = re.sub(r"[\.\-:]", "", mac.strip().lower())
        if len(clean) != 12 or not all(c in "0123456789abcdef" for c in clean):
            raise ValueError(f"Invalid MAC address format: {mac}")
        return f"{clean[0:4]}.{clean[4:8]}.{clean[8:12]}"

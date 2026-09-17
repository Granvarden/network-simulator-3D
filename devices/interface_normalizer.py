"""Cisco IOS interface name resolver and canonical normalizer."""

import re
from typing import Optional


class InterfaceNormalizer:
    """Normalizes various interface shorthands and aliases to canonical Cisco IOS names."""

    # Prefix mappings: (regex pattern, canonical prefix, short prefix)
    _PREFIX_PATTERNS = [
        (re.compile(r"^(?:gi|gig|gigabitethernet|g)\s*(\d+(?:/\d+)*)$", re.IGNORECASE), "GigabitEthernet", "Gi"),
        (re.compile(r"^(?:fa|fast|fastethernet|f)\s*(\d+(?:/\d+)*)$", re.IGNORECASE), "FastEthernet", "Fa"),
        (re.compile(r"^(?:te|tengig|tengigabitethernet)\s*(\d+(?:/\d+)*)$", re.IGNORECASE), "TenGigabitEthernet", "Te"),
        (re.compile(r"^(?:eth|ethernet|e)\s*(\d+(?:/\d+)*)$", re.IGNORECASE), "Ethernet", "Eth"),
        (re.compile(r"^(?:lo|loopback)\s*(\d+)$", re.IGNORECASE), "Loopback", "Lo"),
        (re.compile(r"^(?:con|console)\s*(\d*)$", re.IGNORECASE), "Console", "Con"),
    ]

    @classmethod
    def normalize(cls, name: str) -> str:
        """
        Convert any interface alias/shorthand to canonical form.
        Examples:
            'g0/0', 'gi0/0', 'Gi0/0', 'G0/0' -> 'GigabitEthernet0/0'
            'fa0/1', 'f0/1' -> 'FastEthernet0/1'
            'eth0' -> 'GigabitEthernet0/0' if PC alias or 'eth0'
        """
        clean = name.strip()
        if not clean:
            return clean

        # Special PC ethernet adapter case
        if clean.lower() in ("eth0", "ethernet0"):
            return "eth0"

        for pattern, canonical_pfx, _ in cls._PREFIX_PATTERNS:
            m = pattern.match(clean)
            if m:
                slot_id = m.group(1)
                return f"{canonical_pfx}{slot_id}" if slot_id else canonical_pfx

        # Fallback to original cleaned string
        return clean

    @classmethod
    def to_short(cls, name: str) -> str:
        """
        Convert canonical or full name to standard Cisco shorthand.
        Examples:
            'GigabitEthernet0/0' -> 'Gi0/0'
            'FastEthernet0/1' -> 'Fa0/1'
        """
        clean = name.strip()
        if clean.lower() in ("eth0", "ethernet0"):
            return "eth0"
        for pattern, _, short_pfx in cls._PREFIX_PATTERNS:
            m = pattern.match(clean)
            if m:
                slot_id = m.group(1)
                return f"{short_pfx}{slot_id}" if slot_id else short_pfx
        return clean

    @classmethod
    def is_valid_interface_syntax(cls, name: str) -> bool:
        """Verify whether an interface name matches a recognizable Cisco interface pattern."""
        clean = name.strip()
        if clean.lower() == "eth0":
            return True
        for pattern, _, _ in cls._PREFIX_PATTERNS:
            if pattern.match(clean):
                return True
        return False

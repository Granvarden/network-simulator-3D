"""IPv4 Subnet calculations and validations."""

from typing import Optional


def is_valid_ip(ip: str) -> bool:
    """Validate IPv4 address format."""
    try:
        parts = [int(p) for p in ip.strip().split(".")]
        return len(parts) == 4 and all(0 <= p <= 255 for p in parts)
    except Exception:
        return False


def is_valid_netmask(mask: str) -> bool:
    """Validate that netmask has contiguous 1s followed by 0s."""
    if not is_valid_ip(mask):
        return False
    val = ip_to_int(mask)
    # Check if inverted value + 1 is a power of 2
    inv = (~val) & 0xFFFFFFFF
    return (inv & (inv + 1)) == 0


def ip_to_int(ip: str) -> int:
    """Convert dotted IPv4 string to 32-bit unsigned integer."""
    octets = [int(p) for p in ip.strip().split(".")]
    return (octets[0] << 24) | (octets[1] << 16) | (octets[2] << 8) | octets[3]


def int_to_ip(val: int) -> str:
    """Convert 32-bit unsigned integer to dotted IPv4 string."""
    return f"{(val >> 24) & 0xFF}.{(val >> 16) & 0xFF}.{(val >> 8) & 0xFF}.{val & 0xFF}"


def get_network_address(ip: str, mask: str) -> str:
    """Calculate Network ID from IP and Subnet Mask."""
    ip_int = ip_to_int(ip)
    mask_int = ip_to_int(mask)
    return int_to_ip(ip_int & mask_int)


def is_same_subnet(ip1: str, ip2: str, mask: str) -> bool:
    """Check if two IP addresses reside in the same subnet with the given mask."""
    if not is_valid_ip(ip1) or not is_valid_ip(ip2) or not is_valid_ip(mask):
        return False
    return get_network_address(ip1, mask) == get_network_address(ip2, mask)


def netmask_to_cidr(mask: str) -> int:
    """Convert netmask to prefix length (e.g. 255.255.255.0 -> 24)."""
    val = ip_to_int(mask)
    return bin(val).count("1")


def cidr_to_netmask(cidr: int) -> str:
    """Convert prefix length to netmask (e.g. 24 -> 255.255.255.0)."""
    if not (0 <= cidr <= 32):
        raise ValueError("CIDR prefix must be between 0 and 32")
    val = (0xFFFFFFFF << (32 - cidr)) & 0xFFFFFFFF if cidr > 0 else 0
    return int_to_ip(val)

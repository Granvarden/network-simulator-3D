"""Packet and frame data structures."""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Packet:
    src_ip: str
    dst_ip: str
    ttl: int = 64
    payload: Any = None


@dataclass
class EthernetFrame:
    src_mac: str
    dst_mac: str
    ether_type: str = "IPv4"
    payload: Any = None


@dataclass
class IcmpEchoRequest:
    seq_num: int
    identifier: int
    data: str = "NetworkSimulatorPingData"


@dataclass
class IcmpEchoReply:
    seq_num: int
    identifier: int
    ttl: int
    data: str

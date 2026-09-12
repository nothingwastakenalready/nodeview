"""Read-only connector primitives used by device discovery."""

from __future__ import annotations

import concurrent.futures
import ipaddress
import socket
from dataclasses import dataclass
from time import perf_counter
from typing import Iterable, Protocol


@dataclass(frozen=True)
class DiscoveredDevice:
    address: str
    hostname: str | None
    latency_ms: int | None
    open_ports: tuple[int, ...]
    connector: str = "generic"


class Connector(Protocol):
    name: str

    def discover(self, address: str) -> DiscoveredDevice | None: ...


class GenericConnector:
    """Discover a host using only safe TCP probes; never changes remote state."""

    name = "generic"

    def __init__(self, ports: Iterable[int] = (22, 53, 80, 443, 445, 548, 8123, 8006, 8080, 9100)) -> None:
        self.ports = tuple(dict.fromkeys(int(port) for port in ports))

    def discover(self, address: str) -> DiscoveredDevice | None:
        started = perf_counter()
        try:
            with socket.create_connection((address, 80), timeout=0.35):
                latency = round((perf_counter() - started) * 1000)
        except OSError:
            latency = None

        open_ports: list[int] = []
        for port in self.ports:
            try:
                with socket.create_connection((address, port), timeout=0.2):
                    open_ports.append(port)
            except OSError:
                continue

        if latency is None and not open_ports:
            return None
        try:
            hostname = socket.gethostbyaddr(address)[0]
        except OSError:
            hostname = None
        return DiscoveredDevice(address, hostname, latency, tuple(open_ports), self.name)


def discover_network(network: str, connector: Connector | None = None, *, workers: int = 32) -> list[DiscoveredDevice]:
    """Probe an IPv4 CIDR network concurrently and return stable address order."""
    net = ipaddress.ip_network(network, strict=False)
    if net.version != 4:
        raise ValueError("only IPv4 networks are supported")
    probe = connector or GenericConnector()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        found = [device for device in pool.map(probe.discover, (str(host) for host in net.hosts())) if device]
    return sorted(found, key=lambda device: ipaddress.ip_address(device.address))

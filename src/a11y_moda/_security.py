"""URL safety checks (SSRF defence)."""
from __future__ import annotations
import ipaddress
import os
import socket
from urllib.parse import urlparse


_BLOCKED_HOSTS = {"localhost", "0.0.0.0", "::", "::1", "ip6-localhost", "ip6-loopback"}


class UnsafeURLError(ValueError):
    """URL was rejected because it points at a private / loopback / non-http host."""


def _allow_private_default() -> bool:
    """Operator can opt in via env var when scanning intranets."""
    return os.environ.get("A11Y_ALLOW_PRIVATE_HOSTS", "").strip() == "1"


def _normalise_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address):
    """Unwrap IPv4-mapped IPv6 (`::ffff:127.0.0.1`) so private/loopback checks
    land on the embedded IPv4. ipaddress's is_loopback is False on the wrapper.
    """
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        return ip.ipv4_mapped
    return ip


def _ip_is_private(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    ip = _normalise_ip(ip)
    return (ip.is_private or ip.is_loopback or ip.is_link_local
            or ip.is_reserved or ip.is_multicast or ip.is_unspecified)


def _resolve_all(host: str) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    """All IPs the resolver returns. Empty list on failure (callers treat as unsafe)."""
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return []
    out = []
    for info in infos:
        ip_str = info[4][0]
        try:
            out.append(ipaddress.ip_address(ip_str))
        except ValueError:
            continue
    return out


def is_safe_http_url(url: str, *, allow_private: bool | None = None) -> bool:
    """True when URL is safe to fetch from arbitrary callers.

    Rejects: non-http(s) schemes, missing host, loopback / private / link-local
    / reserved / multicast IP literals, IPv4-mapped IPv6 wrappers around such
    IPs, and hostnames where ANY resolved IP falls in those ranges (mitigates
    DNS rebinding where the resolver returns both a public and a private IP).

    Pass allow_private=True (or set A11Y_ALLOW_PRIVATE_HOSTS=1) to permit
    intranet scans.
    """
    if allow_private is None:
        allow_private = _allow_private_default()
    try:
        p = urlparse(url)
    except Exception:
        return False
    if p.scheme not in ("http", "https"):
        return False
    host = (p.hostname or "").lower()
    if not host:
        return False
    if allow_private:
        return True
    if host in _BLOCKED_HOSTS:
        return False
    try:
        ip = ipaddress.ip_address(host)
        return not _ip_is_private(ip)
    except ValueError:
        pass  # hostname, resolve below
    ips = _resolve_all(host)
    if not ips:
        return False
    return not any(_ip_is_private(ip) for ip in ips)


def require_safe_http_url(url: str, *, allow_private: bool | None = None) -> None:
    """Raise UnsafeURLError if the URL is not safe."""
    if not is_safe_http_url(url, allow_private=allow_private):
        raise UnsafeURLError(f"refused unsafe URL (private/loopback/non-http): {url!r}")

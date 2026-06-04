"""TLS context helpers.

Python 3.12+ tightened OpenSSL defaults (TLS 1.2 floor, SECLEVEL=2,
no unsafe legacy renegotiation). Some legacy gov / enterprise infra
still ships TLS 1.0 + weak ciphers and fails the default handshake
with `SSLV3_ALERT_HANDSHAKE_FAILURE` or `UNSAFE_LEGACY_RENEGOTIATION_DISABLED`.

This module exposes an opt-in relaxed context so users can scan those
sites without disabling TLS entirely. Triggered via `--legacy-tls`
on `scan` / `site`. Never enabled by default — relaxing TLS is a
security trade-off the user must make explicitly.
"""
from __future__ import annotations
import ssl


def legacy_ssl_context() -> ssl.SSLContext:
    """Relaxed SSL context for legacy infra.

    - Floor: TLS 1.0 (default in 3.12 is 1.2)
    - Ciphers: SECLEVEL=1 (weaker accepted)
    - Allow unsafe legacy server-side renegotiation (some old gov.tw)

    Verifies certs by default. Use for handshake-incompatible legacy
    servers, NOT for ignoring cert errors.
    """
    ctx = ssl.create_default_context()
    ctx.minimum_version = ssl.TLSVersion.TLSv1
    try:
        ctx.options |= ssl.OP_LEGACY_SERVER_CONNECT
    except AttributeError:
        ctx.options |= 0x4
    try:
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
    except ssl.SSLError:
        pass
    return ctx


def httpx_verify(legacy_tls: bool):
    """Return value for httpx.Client(verify=...) — strict default or relaxed."""
    return legacy_ssl_context() if legacy_tls else True

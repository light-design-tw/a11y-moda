"""Proper CSS extraction + declaration walker using tinycss2.

Replaces the regex-based scanner in rules/css.py — handles nested @media, comments,
and quoted values correctly.
"""
from __future__ import annotations
from dataclasses import dataclass
from urllib.parse import urljoin
from functools import lru_cache

import httpx
import tinycss2
from bs4 import BeautifulSoup, Tag

from ._security import is_safe_http_url
from ._ssl import httpx_verify


# Per-process flag — set by scanner before fetching any stylesheets. Threaded
# scans share the same value (CLI is single --legacy-tls toggle), so a module
# global is safe here. Threading `legacy_tls` through every rule that calls
# collect_declarations() / _fetch() would require touching 20+ rule files;
# this avoids that churn while still honouring the flag.
_LEGACY_TLS = False


def set_legacy_tls(enabled: bool) -> None:
    """Toggle relaxed TLS for subsequent _fetch() calls. Called by scanner.

    Note: invalidates the @lru_cache when the flag flips — same URL fetched
    under different TLS modes would otherwise return stale content.
    """
    global _LEGACY_TLS
    if _LEGACY_TLS != enabled:
        _fetch.cache_clear()
        _LEGACY_TLS = enabled


@dataclass
class Declaration:
    prop: str
    value: str
    source: str  # "<style>", "style@", or url


_STYLESHEET_MAX_BYTES = 5 * 1024 * 1024  # 5 MB per stylesheet — stops a hostile origin pinning hundreds of MB in lru_cache.


@lru_cache(maxsize=128)
def _fetch(url: str) -> str:
    # SSRF guard: a hostile page can plant <link rel="stylesheet"
    # href="http://127.0.0.1:9200/_cluster/state"> to make us pull
    # internal services. Validate before AND after redirects.
    if not is_safe_http_url(url):
        return ""
    try:
        with httpx.Client(follow_redirects=True, timeout=10.0, verify=httpx_verify(_LEGACY_TLS)) as cli:
            with cli.stream("GET", url) as r:
                if r.status_code != 200 or not is_safe_http_url(str(r.url)):
                    return ""
                buf = bytearray()
                for chunk in r.iter_bytes():
                    buf.extend(chunk)
                    if len(buf) > _STYLESHEET_MAX_BYTES:
                        return ""
                return buf.decode(r.encoding or "utf-8", errors="replace")
    except Exception:
        return ""


def _walk_rules(nodes, source: str) -> list[Declaration]:
    out: list[Declaration] = []
    for node in nodes:
        t = node.type
        if t == "qualified-rule":
            decls = tinycss2.parse_declaration_list(node.content, skip_comments=True, skip_whitespace=True)
            for d in decls:
                if d.type == "declaration":
                    val = tinycss2.serialize(d.value).strip()
                    out.append(Declaration(prop=d.lower_name, value=val, source=source))
        elif t == "at-rule":
            if node.content is not None:
                inner = tinycss2.parse_rule_list(node.content, skip_comments=True, skip_whitespace=True)
                out.extend(_walk_rules(inner, source))
    return out


def collect_declarations(soup: BeautifulSoup, base_url: str, *, fetch_external: bool = True) -> list[Declaration]:
    """Aggregate all CSS declarations the page exposes (inline, <style>, external)."""
    declarations: list[Declaration] = []

    for s in soup.find_all("style"):
        if not isinstance(s, Tag):
            continue
        text = s.get_text() or ""
        if not text.strip():
            continue
        rules = tinycss2.parse_stylesheet(text, skip_comments=True, skip_whitespace=True)
        declarations.extend(_walk_rules(rules, source="<style>"))

    for el in soup.find_all(style=True):
        if not isinstance(el, Tag):
            continue
        decls = tinycss2.parse_declaration_list(el.get("style") or "", skip_comments=True, skip_whitespace=True)
        for d in decls:
            if d.type == "declaration":
                val = tinycss2.serialize(d.value).strip()
                declarations.append(Declaration(prop=d.lower_name, value=val, source=f"style@<{el.name}>"))

    if fetch_external:
        for link in soup.find_all("link"):
            if not isinstance(link, Tag):
                continue
            rel = " ".join(link.get("rel") or []).lower()
            if "stylesheet" not in rel:
                continue
            href = (link.get("href") or "").strip()
            if not href:
                continue
            full = urljoin(base_url, href)
            if not full.startswith(("http://", "https://")):
                continue
            text = _fetch(full)
            if not text:
                continue
            rules = tinycss2.parse_stylesheet(text, skip_comments=True, skip_whitespace=True)
            declarations.extend(_walk_rules(rules, source=full))

    return declarations

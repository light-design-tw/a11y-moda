"""Discover URLs to scan: sitemap.xml fetch, bounded same-domain crawl, optional JS render.

For `file://` URLs (auditing local build output), URL discovery does not
crawl links nor look for sitemap.xml — it walks the filesystem directory
for `*.html` files. Same-origin checks are replaced by same-root-directory
checks.
"""
from __future__ import annotations
import asyncio
import time
from collections import deque
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.request import url2pathname

# defusedxml hardens against billion-laughs / external-entity attacks in
# untrusted sitemap.xml — drop-in replacement for stdlib xml.etree.
from defusedxml import ElementTree as ET

import httpx
from bs4 import BeautifulSoup

from . import USER_AGENT
from ._security import is_safe_http_url


_SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

# Non-HTML asset extensions to skip during crawl (binary downloads, fonts, media).
DEFAULT_SKIP_EXT = (
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico", ".bmp", ".tif", ".tiff",
    ".mp3", ".mp4", ".m4a", ".m4v", ".avi", ".mov", ".wmv", ".flv", ".webm", ".mkv", ".ogg", ".wav",
    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".ods", ".odp",
    ".css", ".js", ".json", ".xml", ".rss", ".atom",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".exe", ".dmg", ".pkg", ".deb", ".rpm", ".msi",
    ".epub", ".mobi", ".pss", ".txt", ".csv",
    ".swf", ".dll",
)


def _same_origin(a: str, b: str) -> bool:
    pa, pb = urlparse(a), urlparse(b)
    return (pa.scheme, pa.netloc) == (pb.scheme, pb.netloc)


def _normalize(url: str) -> str:
    no_frag, _ = urldefrag(url)
    return no_frag.rstrip("/") or no_frag


def _is_excluded(url: str, *, exclude_urls: set[str], exclude_folders: tuple[str, ...],
                 skip_ext: tuple[str, ...]) -> bool:
    low = url.lower()
    if any(low.endswith(e) for e in skip_ext):
        return True
    if url in exclude_urls:
        return True
    if any(folder and folder in url for folder in exclude_folders):
        return True
    if not is_safe_http_url(url):  # SSRF guard — drop loopback / private / file://
        return True
    return False


# Hard caps on sitemap fetch & recursion. defusedxml stops billion-laughs but
# nothing protects against 10GB sitemaps or sitemap-index cycles, so cap
# response size, recursion depth, and URL count.
_SITEMAP_MAX_BYTES = 25 * 1024 * 1024     # 25 MB per sitemap file
_SITEMAP_MAX_DEPTH = 3                     # sitemap-index nesting
_SITEMAP_MAX_URLS = 50_000                 # all sitemaps combined


async def _fetch_with_cap(cli: httpx.AsyncClient, url: str, *, max_bytes: int) -> str | None:
    """Stream-fetch a URL, abort if larger than max_bytes. Re-validates the
    final URL after redirects so a sitemap can't redirect us at a private host.
    """
    try:
        async with cli.stream("GET", url) as r:
            if r.status_code != 200:
                return None
            if not is_safe_http_url(str(r.url)):
                return None
            buf = bytearray()
            async for chunk in r.aiter_bytes():
                buf.extend(chunk)
                if len(buf) > max_bytes:
                    return None
            return buf.decode(r.encoding or "utf-8", errors="replace")
    except Exception:
        return None


async def fetch_sitemap(base: str, *, timeout: float = 15.0) -> list[str]:
    """Try common sitemap locations; recurse into sitemap-index files."""
    parsed = urlparse(base)
    root = f"{parsed.scheme}://{parsed.netloc}"
    candidates = [f"{root}/sitemap.xml", f"{root}/sitemap_index.xml", f"{root}/sitemap.xml.gz"]
    urls: list[str] = []
    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as cli:
        for c in candidates:
            text = await _fetch_with_cap(cli, c, max_bytes=_SITEMAP_MAX_BYTES)
            if not text or not text.strip().startswith("<"):
                continue
            urls.extend(await _parse_sitemap_xml(text, cli, depth=0, visited={c}))
            if urls:
                break
    return [_normalize(u) for u in urls[:_SITEMAP_MAX_URLS]]


async def _parse_sitemap_xml(xml_text: str, cli: httpx.AsyncClient,
                              *, depth: int, visited: set[str]) -> list[str]:
    out: list[str] = []
    if depth > _SITEMAP_MAX_DEPTH:
        return out
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return out
    tag = root.tag.lower()
    if "sitemapindex" in tag:
        for sm in root.findall(".//sm:sitemap/sm:loc", _SITEMAP_NS):
            sub_url = (sm.text or "").strip()
            if not sub_url or sub_url in visited or not is_safe_http_url(sub_url):
                continue
            visited.add(sub_url)
            sub_text = await _fetch_with_cap(cli, sub_url, max_bytes=_SITEMAP_MAX_BYTES)
            if sub_text:
                out.extend(await _parse_sitemap_xml(sub_text, cli, depth=depth + 1, visited=visited))
                if len(out) >= _SITEMAP_MAX_URLS:
                    return out[:_SITEMAP_MAX_URLS]
    else:
        for loc in root.findall(".//sm:url/sm:loc", _SITEMAP_NS):
            if loc.text:
                u = loc.text.strip()
                if is_safe_http_url(u):
                    out.append(u)
                    if len(out) >= _SITEMAP_MAX_URLS:
                        return out
    return out


def _extract_links_from_html(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    out = []
    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
            continue
        out.append(urljoin(base_url, href))
    return out


def crawl(
    start_url: str,
    *,
    max_pages: int = 30,
    timeout: float = 15.0,
    ua: str = USER_AGENT,
    render: bool = False,
    exclude_urls: tuple[str, ...] = (),
    exclude_folders: tuple[str, ...] = (),
    skip_ext: tuple[str, ...] = DEFAULT_SKIP_EXT,
    max_seconds: float = 0,
) -> list[str]:
    """BFS same-origin crawl. render=True → Playwright (catches JS-injected links)."""
    queue: deque[str] = deque([_normalize(start_url)])
    seen: set[str] = {_normalize(start_url)}
    found: list[str] = []
    excl_url_set = set(_normalize(u) for u in exclude_urls)
    started = time.monotonic()

    if render:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(user_agent=ua)
            page = ctx.new_page()
            while queue and len(found) < max_pages:
                if max_seconds and time.monotonic() - started > max_seconds:
                    break
                url = queue.popleft()
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=int(timeout * 1000))
                    try:
                        page.wait_for_load_state("networkidle", timeout=5000)
                    except Exception:
                        pass
                    if not is_safe_http_url(page.url):
                        continue  # Playwright followed redirect to private/file:// host
                    html = page.content()
                except Exception:
                    continue
                found.append(url)
                _enqueue(html, url, start_url, queue, seen, excl_url_set, exclude_folders, skip_ext)
            browser.close()
        return found

    with httpx.Client(follow_redirects=True, timeout=timeout, headers={"User-Agent": ua}) as cli:
        while queue and len(found) < max_pages:
            if max_seconds and time.monotonic() - started > max_seconds:
                break
            url = queue.popleft()
            try:
                r = cli.get(url)
            except Exception:
                continue
            # SSRF guard after redirect — server may bounce us at a private host.
            if not is_safe_http_url(str(r.url)):
                continue
            if r.status_code >= 400 or "html" not in r.headers.get("content-type", "").lower():
                continue
            found.append(url)
            _enqueue(r.text, url, start_url, queue, seen, excl_url_set, exclude_folders, skip_ext)
    return found


def _enqueue(html: str, current: str, origin: str, queue: deque[str], seen: set[str],
             excl_url_set: set[str], exclude_folders: tuple[str, ...], skip_ext: tuple[str, ...]) -> None:
    for link in _extract_links_from_html(html, current):
        full = _normalize(link)
        if not _same_origin(origin, full):
            continue
        if full in seen:
            continue
        if _is_excluded(full, exclude_urls=excl_url_set, exclude_folders=exclude_folders, skip_ext=skip_ext):
            continue
        seen.add(full)
        queue.append(full)


def discover_filesystem(start_url: str, *, max_pages: int = 30,
                         exclude_urls: tuple[str, ...] = (),
                         exclude_folders: tuple[str, ...] = ()) -> list[str]:
    """Walk a local directory for *.html files. `start_url` is a file:// URL.

    If the URL points at a single file, returns [start_url]. If it points at
    a directory, returns all *.html files within (sorted, depth-first).
    """
    parsed = urlparse(start_url)
    fs_path = Path(url2pathname(parsed.path))
    if fs_path.is_file():
        return [start_url] if fs_path.suffix.lower() in (".html", ".htm") else []
    if not fs_path.is_dir():
        return []
    excl_url_set = set(exclude_urls)
    out: list[str] = []
    for p in sorted(fs_path.rglob("*.htm*")):
        if p.suffix.lower() not in (".html", ".htm"):
            continue
        u = p.resolve().as_uri()
        if u in excl_url_set:
            continue
        if any(folder and folder in u for folder in exclude_folders):
            continue
        out.append(u)
        if len(out) >= max_pages:
            break
    return out


def discover(
    start_url: str,
    *,
    max_pages: int = 30,
    prefer_sitemap: bool = True,
    render: bool = False,
    exclude_urls: tuple[str, ...] = (),
    exclude_folders: tuple[str, ...] = (),
    skip_ext: tuple[str, ...] = DEFAULT_SKIP_EXT,
    max_seconds: float = 0,
) -> list[str]:
    """Sitemap-first, fall back to crawl. render only affects crawl path.

    For `file://` URLs, sitemap/crawl don't apply — walk the filesystem
    instead (see discover_filesystem).
    """
    if start_url.startswith("file://"):
        return discover_filesystem(start_url, max_pages=max_pages,
                                    exclude_urls=exclude_urls,
                                    exclude_folders=exclude_folders)
    if prefer_sitemap:
        urls = asyncio.run(fetch_sitemap(start_url))
        urls = [u for u in urls if _same_origin(start_url, u)]
        urls = [u for u in urls if not _is_excluded(u, exclude_urls=set(exclude_urls),
                                                     exclude_folders=exclude_folders, skip_ext=skip_ext)]
        if urls:
            return urls[:max_pages]
    return crawl(start_url, max_pages=max_pages, render=render,
                 exclude_urls=exclude_urls, exclude_folders=exclude_folders,
                 skip_ext=skip_ext, max_seconds=max_seconds)

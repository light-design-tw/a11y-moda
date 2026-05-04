"""Third-party origin detection.

Used by `Rule.check()` post-hook to downgrade issues whose violation lives in a
resource (CSS / font / script) loaded from a different organisation. Such issues
are valid findings but the page author cannot fix the third-party file directly
— the WCAG 2.1 §5.4 partial conformance route applies, and MODA accepts a
備註欄 declaration listing third-party content. Downgrading from `fail` to
`caveat` flags the issue for human review without claiming the site fails
outright.

Heuristics, not perfect:
- Resource URL is extracted only from snippets that follow the `value @ URL`
  format (used by CSS rules). Avoids false positives on iframe `src=` etc.,
  where the page is responsible for the wrapping element regardless of the
  iframe's origin.
- Root-domain comparison handles the common Taiwan compound TLDs
  (`*.gov.tw`, `*.com.tw`, `*.edu.tw`, etc.) without pulling in `tldextract`.
"""
from __future__ import annotations
import re
from urllib.parse import urlparse

# Match `... @ <url>` (the snippet format CSS rules emit). Capture URL only.
_AT_URL_RE = re.compile(r"@\s*(https?://[^\s<>\"']+)")

# Compound second-level labels seen in ccTLDs we care about.
_COMPOUND_SLDS = {"gov", "com", "edu", "org", "net", "co", "ne", "ac", "or"}
# ccTLDs we explicitly handle compound forms for.
_KNOWN_CCTLDS = {"tw", "cn", "uk", "au", "jp", "hk", "kr", "nz"}


def extract_resource_url(snippet: str) -> str | None:
    """Pull the resource URL out of a `value @ URL` snippet. Returns None if
    snippet doesn't match the format (e.g. raw HTML, plain text)."""
    if not snippet:
        return None
    m = _AT_URL_RE.search(snippet)
    return m.group(1) if m else None


def _root_domain(host: str) -> str:
    """Best-effort eTLD+1 without `tldextract`. Strips leading `www.` and
    handles common Taiwan / Asia ccTLD compound suffixes (`.gov.tw` etc.)."""
    if not host:
        return ""
    host = host.lower().lstrip(".")
    if host.startswith("www."):
        host = host[4:]
    parts = host.split(".")
    if len(parts) >= 3 and parts[-1] in _KNOWN_CCTLDS and parts[-2] in _COMPOUND_SLDS:
        return ".".join(parts[-3:])
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host


def is_third_party(resource_url: str, page_url: str) -> bool:
    """Return True when `resource_url` is loaded from a different organisation
    than the page itself. Same root domain (any subdomain) counts as first-party."""
    if not resource_url or not page_url:
        return False
    try:
        res_host = urlparse(resource_url).hostname or ""
        page_host = urlparse(page_url).hostname or ""
    except (ValueError, AttributeError):
        return False
    if not res_host or not page_host:
        return False
    return _root_domain(res_host) != _root_domain(page_host)


def third_party_origin(resource_url: str) -> str:
    """Display-friendly origin label for the issue message (e.g. `google.com`)."""
    if not resource_url:
        return ""
    try:
        host = urlparse(resource_url).hostname or ""
    except (ValueError, AttributeError):
        return ""
    return _root_domain(host)

"""Shared helpers and constants."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ...models import Level, PageReport
from ..base import Rule, RuleMeta, register
from ..helpers import should_skip, truncate


def _has_referenced_label(el: Tag, soup: BeautifulSoup) -> bool:
    """Resolve aria-labelledby IDs to elements with text or children."""
    ids = (el.get("aria-labelledby") or "").strip()
    if not ids:
        return False
    for token in ids.split():
        target = soup.find(id=token)
        if isinstance(target, Tag) and (target.get_text(strip=True) or len(target.find_all(recursive=False)) > 0):
            return True
    return False


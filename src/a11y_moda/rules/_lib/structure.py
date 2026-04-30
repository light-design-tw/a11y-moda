"""Shared helpers and constants."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ...models import Level, PageReport
from ..base import Rule, RuleMeta, register
from ..helpers import should_skip, truncate


_SECTIONING = ("article", "section", "hgroup", "nav", "header", "footer", "aside")

_HEADINGS = ("h1", "h2", "h3", "h4", "h5", "h6")

def _direct_child_of(descendant: Tag, ancestor_table: Tag) -> bool:
    """th/td count toward this table only when no nested <table> intervenes."""
    if not isinstance(descendant, Tag):
        return False
    p = descendant.parent
    while isinstance(p, Tag) and p is not ancestor_table:
        if p.name == "table":
            return False
        p = p.parent
    return p is ancestor_table


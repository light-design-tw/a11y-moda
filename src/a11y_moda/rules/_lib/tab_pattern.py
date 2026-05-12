"""Suspected tab-pattern detection — shared by GN1240300E (focus order) and
GN1410200E (ARIA name/role/value).

A 'tab-like group' visually behaves as `role=tablist` but is implemented as
a row of <button>/<a>/<div> siblings with category labels. Common in
designer-built sites (Wix / Webflow / Tailwind UI copy-paste). When the
group lacks role=tab/tablist, screen-reader users hear N independent
controls instead of an N-of-M tab choice — affects both focus order
(2.4.3) and role exposure (4.1.2).
"""
from __future__ import annotations
import re
from bs4 import Tag
from ..helpers import should_skip


_GROUP_HINT = re.compile(
    r"\b(tab|tabs|tablist|nav-tabs|filter|filters|categories|category|"
    r"segmented|segments|pill|pills|chips|toggle-group|switcher)\b",
    re.IGNORECASE,
)
_LIKELY_TAB_TAGS = {"button", "a", "div", "li", "span"}
_MIN_SIBLINGS = 3
_MAX_LABEL_LEN = 16  # tab labels tend to be short — "全部 / 產品服務 / 教學指南"


def _has_role_tab(el: Tag) -> bool:
    return (el.get("role") or "").strip().lower() in ("tab", "tablist")


def _short_label(el: Tag) -> bool:
    txt = el.get_text(strip=True)
    if not txt or len(txt) > _MAX_LABEL_LEN:
        return False
    # exclude long-form content blocks: skip if has block descendants
    for child in el.find_all(True):
        if isinstance(child, Tag) and child.name in ("p", "section", "article", "ul", "ol", "img", "form"):
            return False
    return True


def find_suspected_tab_groups(soup) -> list[Tag]:
    """Return container elements that look like a tab group but lack ARIA roles.

    Detection priority:
    1. Container class contains tab/filter/category-like keyword AND has
       3+ short-label children of likely-tab tags
    2. Any 3+ siblings with role-suggesting attributes (aria-selected,
       data-tab, aria-controls) but no role=tab on themselves
    """
    suspects: list[Tag] = []
    seen: set[int] = set()
    for parent in soup.find_all(True):
        if not isinstance(parent, Tag) or should_skip(parent):
            continue
        cls = " ".join(parent.get("class") or [])
        role = (parent.get("role") or "").strip().lower()
        if role == "tablist":
            continue  # already correct
        # candidate children = direct interactive-ish children with short labels
        children = [
            c for c in parent.find_all(True, recursive=False)
            if isinstance(c, Tag)
            and c.name in _LIKELY_TAB_TAGS
            and not should_skip(c)
            and _short_label(c)
        ]
        if len(children) < _MIN_SIBLINGS:
            continue
        # any child already correctly tagged → skip whole group
        if any(_has_role_tab(c) for c in children):
            continue
        # pattern signal: class hint OR explicit tab-ish attrs on children
        cls_hint = bool(_GROUP_HINT.search(cls))
        attr_hint = any(
            c.has_attr("aria-selected") or c.has_attr("data-tab") or c.has_attr("aria-controls")
            for c in children
        )
        if not (cls_hint or attr_hint):
            continue
        if id(parent) in seen:
            continue
        seen.add(id(parent))
        suspects.append(parent)
    return suspects


def labels_of(group: Tag, limit: int = 5) -> list[str]:
    return [c.get_text(strip=True) for c in group.find_all(True, recursive=False)
            if isinstance(c, Tag) and c.get_text(strip=True)][:limit]

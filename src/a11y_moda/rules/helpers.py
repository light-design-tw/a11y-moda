"""Common predicates shared across rules.

Skip elements that are not meaningfully exposed to assistive tech:
- elements inside <template>/<slot> are inert
- aria-hidden="true" hides from AT
- inline style display:none / visibility:hidden hides element
"""
from __future__ import annotations
from bs4 import Tag


def is_in_inert_container(el: Tag) -> bool:
    for parent in el.parents:
        if not isinstance(parent, Tag):
            continue
        if parent.name and parent.name.lower() in ("template", "slot"):
            return True
    return False


def is_aria_hidden(el: Tag) -> bool:
    val = (el.get("aria-hidden") or "").strip().lower()
    return val == "true"


def is_style_hidden(el: Tag) -> bool:
    style = (el.get("style") or "").lower().replace(" ", "")
    return "display:none" in style or "visibility:hidden" in style


def is_visually_hidden(el: Tag) -> bool:
    return is_aria_hidden(el) or is_style_hidden(el)


def should_skip(el: Tag) -> bool:
    return is_in_inert_container(el) or is_visually_hidden(el)


def truncate(s: str, n: int = 300) -> str:
    return s if len(s) <= n else s[:n]

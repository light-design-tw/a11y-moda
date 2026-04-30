"""Shared helpers and constants."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ...models import Level, PageReport
from ..base import Rule, RuleMeta, register
from ..helpers import should_skip, truncate


_NON_LABELED_INPUT_TYPES = {"hidden", "submit", "reset", "image", "button"}

def _label_text_image_alt_match(label: Tag) -> tuple[bool, str]:
    """Return (alt_equals_label_text, snippet) — duplicate label text."""
    text = (label.get_text() or "").strip()
    for img in label.find_all("img"):
        if not isinstance(img, Tag):
            continue
        alt = (img.get("alt") or "").strip()
        if text and alt and alt == text:
            return True, truncate(str(label))
    return False, ""

def _label_image_alt_empty(label: Tag) -> tuple[bool, str]:
    if (label.get_text() or "").strip():
        return False, ""
    for img in label.find_all("img"):
        if not isinstance(img, Tag):
            continue
        if not img.has_attr("alt"):
            continue
        if (img.get("alt") or "").strip() == "":
            return True, truncate(str(label))
    return False, ""

def _accessible_name(el: Tag, soup: BeautifulSoup) -> bool:
    if (el.get("aria-label") or "").strip():
        return True
    if (el.get("title") or "").strip():
        return True
    ids = (el.get("aria-labelledby") or "").strip()
    if ids:
        for token in ids.split():
            target = soup.find(id=token)
            if isinstance(target, Tag) and (target.get_text(strip=True) or len(target.find_all(recursive=False)) > 0):
                return True
    return False

def _check_control(ctrl: Tag, labels: list[Tag], soup: BeautifulSoup) -> tuple[bool, str, str]:
    """Return (is_error, message, snippet)."""
    cid = (ctrl.get("id") or "").strip()
    matched_label: Tag | None = None
    for lbl in labels:
        for_attr = (lbl.get("for") or "").strip()
        if for_attr and cid and for_attr == cid:
            matched_label = lbl
            break
    if matched_label is not None:
        bad, snip = _label_text_image_alt_match(matched_label)
        if bad:
            return True, "<img>的alt屬性值不得與label的文字內容相同。", snip
        bad, snip = _label_image_alt_empty(matched_label)
        if bad:
            return True, "<img>的alt屬性值不得為空值。", snip
        if not (matched_label.get_text() or "").strip() and not matched_label.find_all(["img", "svg"]):
            return True, "對應之label元素不可以是空值。", truncate(str(ctrl))
        return False, "", ""
    if isinstance(ctrl.parent, Tag) and ctrl.parent.name == "label":
        return False, "", ""
    if _accessible_name(ctrl, soup):
        return False, "", ""
    return True, "需有對應的label標籤組件。如為無法設置標籤組件，請以title屬性或aria-*屬性提供該控制元件的標題說明。", truncate(str(ctrl))


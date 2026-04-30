"""GN1210101E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


_NATIVELY_FOCUSABLE = {"a", "button", "input", "select", "textarea", "details", "summary"}
_INTERACTIVE_ROLES = {
    "button", "link", "checkbox", "radio", "menuitem", "menuitemcheckbox",
    "menuitemradio", "option", "switch", "tab", "treeitem", "combobox", "slider",
}
# Roles whose WAI-ARIA design pattern uses roving tabindex — inactive items
# legitimately carry tabindex="-1" while one sibling holds tabindex="0".
# Arrow keys (not Tab) navigate between siblings.
_ROVING_TABINDEX_ROLES = {
    "tab", "menuitem", "menuitemcheckbox", "menuitemradio",
    "treeitem", "option", "radio", "gridcell",
    "columnheader", "rowheader",
}


@register
class KeyboardReachable(Rule):
    """GN1210101E — interactive controls must be reachable via keyboard (Tab)."""

    meta = RuleMeta(
        rule_id="GN1210101E",
        guideline="2.1.1",
        level=Level.A,
        desc="所有可操作的功能、連結、控制元件均應能由鍵盤操作（Tab 可達）",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        for tag in _NATIVELY_FOCUSABLE:
            for el in soup.find_all(tag):
                if not isinstance(el, Tag) or should_skip(el):
                    continue
                ti = (el.get("tabindex") or "").strip()
                if ti != "-1":
                    continue
                if tag == "a" and not (el.get("href") or "").strip():
                    continue
                if tag == "input" and (el.get("type") or "").lower() == "hidden":
                    continue
                roles = (el.get("role") or "").lower().split()
                if any(r in _ROVING_TABINDEX_ROLES for r in roles):
                    continue
                report.add(self._issue(
                    message=f"<{tag}> 設定 tabindex=\"-1\"，已從鍵盤 Tab 序列移除，無法以鍵盤聚焦。",
                    snippet=truncate(str(el), 200),
                ))
                return
        for el in soup.find_all(attrs={"role": True}):
            if not isinstance(el, Tag) or should_skip(el):
                continue
            if el.name in _NATIVELY_FOCUSABLE:
                continue
            roles = (el.get("role") or "").lower().split()
            if not any(r in _INTERACTIVE_ROLES for r in roles):
                continue
            ti = (el.get("tabindex") or "").strip()
            if ti not in ("", "-1"):
                continue
            report.add(self._issue(
                message=f"<{el.name} role=\"{el.get('role')}\"> 為自定義互動元件但未設 tabindex=\"0\"，鍵盤無法聚焦操作。",
                snippet=truncate(str(el), 200),
            ))
            return

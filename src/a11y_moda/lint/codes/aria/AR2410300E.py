"""AR2410300E lint — status-y components should expose role=status / aria-live.

Heuristic: any element with class names hinting at status (loading,
saving, complete, etc) plus visible content should have role=status,
role=alert, role=log, or aria-live. JSX `className={...}` dynamic
expressions can't be inspected statically; emit caveat when the only
className is dynamic.

The original scan rule emits one issue per page max; we emit one per
file to keep lint noise low. Status: info (advisory).
"""
from __future__ import annotations
import re
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import find_html_elements, get_html_attr


_STATUS_HINT = re.compile(r"(status|loading|saving|saved|loaded|complete|completed|成功|完成|載入)", re.IGNORECASE)
_ALLOWED_ROLES = ("status", "alert", "log")


@register
class StatusRoleLint(LintRule):
    meta = RuleMeta(
        rule_id="AR2410300E",
        guideline="4.1.3",
        level=Level.AA,
        desc="疑似狀態訊息元件應使用 ARIA role=status / aria-live",
        source="extension",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            yield from self._check_html(parsed)
        else:
            yield from self._check_jsx(parsed)

    def _check_html(self, parsed):
        for el in find_html_elements(parsed.tree):
            cls = get_html_attr(el, "class")
            if cls.kind != "literal" or not cls.value:
                continue
            if not _STATUS_HINT.search(cls.value):
                continue
            role = get_html_attr(el, "role")
            live = get_html_attr(el, "aria-live")
            if role.kind == "literal" and role.value and role.value.lower() in _ALLOWED_ROLES:
                continue
            if live.kind in ("literal", "boolean") and live.value:
                continue
            yield self._issue(
                status="info",
                message=f'class="{cls.value[:60]}" 含狀態詞 — 缺 role=status / aria-live',
                node=el)
            return

    def _check_jsx(self, parsed):
        from ...helpers import find_jsx_elements, get_attr
        for el in find_jsx_elements(parsed.tree):
            # className OR class
            cls = get_attr(el, "className")
            if cls.kind == "missing":
                cls = get_attr(el, "class")
            if cls.kind != "literal" or not cls.value:
                continue
            if not _STATUS_HINT.search(cls.value):
                continue
            role = get_attr(el, "role")
            live = get_attr(el, "aria-live")
            if role.kind == "literal" and role.value and role.value.lower() in _ALLOWED_ROLES:
                continue
            if live.kind in ("literal", "boolean") and live.value:
                continue
            yield self._issue(
                status="info",
                message=f'className="{cls.value[:60]}" 含狀態詞 — 缺 role=status / aria-live',
                node=el)
            return

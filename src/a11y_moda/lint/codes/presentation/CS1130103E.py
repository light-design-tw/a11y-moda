"""CS1130103E lint — no deprecated text-styling elements (<font>/<basefont>/<marquee>/<blink>)."""
from __future__ import annotations
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import (
    find_jsx_elements_any, get_attr,
    find_html_elements, get_html_attr,
)


_DEPRECATED = ("font", "basefont", "marquee", "blink")


@register
class DeprecatedTextTagLint(LintRule):
    meta = RuleMeta(
        rule_id="CS1130103E",
        guideline="1.3.1",
        level=Level.A,
        desc="禁用已淘汰的 <font>/<basefont>/<marquee>/<blink>",
        source="extension",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            for tag in _DEPRECATED:
                for el in find_html_elements(parsed.tree, tag):
                    yield self._issue(status="fail",
                        message=f"使用已淘汰的 <{tag}> — 請改 CSS",
                        node=el)
                    return
            # color=... attribute on non-hr elements
            for el in find_html_elements(parsed.tree):
                from ...helpers import _html_tag_name
                if _html_tag_name(el) == "hr":
                    continue
                if get_html_attr(el, "color").kind != "missing":
                    yield self._issue(status="info",
                        message=f"<{_html_tag_name(el)}> 使用 color 屬性 — 請改 CSS color",
                        node=el)
                    return
            return

        for el in find_jsx_elements_any(parsed.tree, _DEPRECATED):
            tag = next((c.text.decode("utf-8", errors="replace")
                        for c in el.children if c.type == "identifier"), "?")
            yield self._issue(status="fail",
                message=f"使用已淘汰的 <{tag}> — 請改 CSS",
                node=el)
            return

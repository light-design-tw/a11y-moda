"""CS1110114E lint — no spacer/placeholder images (1x1 gif, blank.gif)."""
from __future__ import annotations
from typing import Iterable

from ....models import Level
from ....rules.base import RuleMeta
from ...base import LintRule, LintIssue, register
from ...helpers import find_jsx_elements, get_attr, find_html_elements, get_html_attr


_SPACER_HINTS = ("spacer", "blank.gif", "1x1", "pixel.gif")


@register
class NoSpacerImageLint(LintRule):
    meta = RuleMeta(
        rule_id="CS1110114E",
        guideline="1.1.1",
        level=Level.A,
        desc="<img> 不應作版面占位用 (spacer / 1x1 GIF) — 請用 CSS",
        source="extension",
    )

    def _check(self, parsed) -> Iterable[LintIssue]:
        if parsed.language == "html":
            for img in find_html_elements(parsed.tree, "img"):
                src = get_html_attr(img, "src")
                if src.kind != "literal" or not src.value:
                    continue
                src_lower = src.value.lower()
                if any(h in src_lower for h in _SPACER_HINTS):
                    yield self._issue(status="fail",
                        message="疑似 spacer 圖片用於版面 — 請改 CSS",
                        node=img)
                    return
                # 1x1 + .gif
                w = get_html_attr(img, "width")
                h = get_html_attr(img, "height")
                if (w.kind == "literal" and w.value in ("0", "1") or
                    h.kind == "literal" and h.value in ("0", "1")) and src_lower.endswith(".gif"):
                    yield self._issue(status="fail",
                        message="1x1 透明 GIF 用於版面 — 請改 CSS",
                        node=img)
                    return
            return

        for img in find_jsx_elements(parsed.tree, "img"):
            src = get_attr(img, "src")
            if src.kind != "literal" or not src.value:
                continue
            src_lower = src.value.lower()
            if any(h in src_lower for h in _SPACER_HINTS):
                yield self._issue(status="fail",
                    message="疑似 spacer 圖片用於版面 — 請改 CSS",
                    node=img)
                return

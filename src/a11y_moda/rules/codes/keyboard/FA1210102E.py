"""FA1210102E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate

# Pointer-specific *activation* events that stand in for a click. Hover-only
# events (onmouseover/out/move/enter/leave) are excluded — they are usually
# supplementary and flagging them is FP-prone.
_POINTER_ACTIVATION = (
    "onmousedown", "onmouseup", "onpointerdown", "onpointerup",
    "ontouchstart", "ontouchend", "ondblclick",
)
# A device-independent / keyboard path on the same element exempts it.
_KEYBOARD_OR_CLICK = ("onclick", "onkeydown", "onkeyup", "onkeypress")


@register
class PointerOnlyActivation(Rule):
    """FA1210102E — a function bound only to pointer events has no keyboard path (2.1.1)."""

    meta = RuleMeta(
        rule_id="FA1210102E",
        guideline="2.1.1",
        level=Level.A,
        desc="某功能僅以指標裝置（含手勢）專屬事件處理，鍵盤使用者無法操作，導致鍵盤(2.1.1)失敗",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        # Inline handlers only — addEventListener-bound logic is invisible to
        # static parsing. Conservative: catches the clearly-detectable cases.
        offenders: list[Tag] = []
        for el in soup.find_all(True):
            if not isinstance(el, Tag) or should_skip(el):
                continue
            ptr = [a for a in _POINTER_ACTIVATION if el.has_attr(a)]
            if not ptr:
                continue
            if any(el.has_attr(k) for k in _KEYBOARD_OR_CLICK):
                continue  # has a click / key handler → keyboard-reachable path exists
            offenders.append(el)
        if not offenders:
            return
        sample = offenders[0]
        attrs = [a for a in _POINTER_ACTIVATION if sample.has_attr(a)]
        report.add(self._issue(
            message=(
                f"功能僅綁定指標專屬事件（{', '.join(attrs)}），無對應的 onclick / 鍵盤事件 — "
                f"鍵盤使用者無法觸發（共 {len(offenders)} 處）。請改用原生可聚焦元件，"
                f"或同時提供 onclick / 鍵盤事件處理。"
            ),
            snippet=truncate(str(sample)),
        ))

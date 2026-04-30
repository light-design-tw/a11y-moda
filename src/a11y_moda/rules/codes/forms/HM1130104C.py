"""HM1130104C rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.forms import _check_control, _NON_LABELED_INPUT_TYPES


@register
class FormControlsHaveLabel(Rule):
    """HM1130104C — visible inputs/select/textarea need <label> or aria/title."""

    meta = RuleMeta(
        rule_id="HM1130104C",
        guideline="1.3.1",
        level=Level.A,
        desc="可見的表單控制元件均需有對應的標籤<label>組件，或有標題(title)屬性，且其內容或值均不得為空字串或空白",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        labels = [l for l in soup.find_all("label") if isinstance(l, Tag)]
        for inp in soup.find_all("input"):
            if not isinstance(inp, Tag) or should_skip(inp):
                continue
            t = (inp.get("type") or "").strip().lower()
            if t in _NON_LABELED_INPUT_TYPES:
                continue
            err, msg, snip = _check_control(inp, labels, soup)
            if err:
                report.add(self._issue(message=msg, snippet=snip))
                ctx.state["HM1130104C_ok"] = False
                ctx.state["HM1130104C_error"] = msg
                return
        for sel in soup.find_all("select"):
            if not isinstance(sel, Tag) or should_skip(sel):
                continue
            err, msg, snip = _check_control(sel, labels, soup)
            if err:
                report.add(self._issue(message=msg, snippet=snip))
                ctx.state["HM1130104C_ok"] = False
                ctx.state["HM1130104C_error"] = msg
                return
        for ta in soup.find_all("textarea"):
            if not isinstance(ta, Tag) or should_skip(ta):
                continue
            err, msg, snip = _check_control(ta, labels, soup)
            if err:
                report.add(self._issue(message=msg, snippet=snip))
                ctx.state["HM1130104C_ok"] = False
                ctx.state["HM1130104C_error"] = msg
                return
        ctx.state["HM1130104C_ok"] = True

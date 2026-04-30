"""GN1250101E rule."""
from __future__ import annotations
import re
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class SliderSinglePoint(Rule):
    """GN1250101E — range/slider needs single-point keyboard fallback (the native one)."""

    meta = RuleMeta(rule_id="GN1250101E", guideline="2.5.1", level=Level.A,
        desc="為控制滑塊提供單點啟動",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        for el in soup.find_all(class_=re.compile(r"slider|range", re.IGNORECASE)):
            if not isinstance(el, Tag) or should_skip(el):
                continue
            if el.find("input", attrs={"type": "range"}):
                continue
            role = (el.get("role") or "").lower()
            if role == "slider" and el.has_attr("aria-valuenow"):
                continue
            report.add(self._issue(
                message="自訂滑塊元件未使用 <input type=range> 也未提供 role=slider + aria-valuenow。",
                snippet=truncate(str(el)[:200]),
                status="info",
            ))
            return

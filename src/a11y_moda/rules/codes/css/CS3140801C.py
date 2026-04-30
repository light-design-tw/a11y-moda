"""CS3140801C rule."""
from __future__ import annotations
import re
from bs4 import BeautifulSoup
from ....css_utils import collect_declarations
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ..._lib.css import _FUNCTIONAL_PREFIXES, _ABSOLUTE_UNIT_RE


@register
class ColumnWidthRelative(Rule):
    """CS3140801C — column width should use % or em-based units (not pure px/pt)."""

    meta = RuleMeta(
        rule_id="CS3140801C",
        guideline="1.4.8",
        level=Level.AAA,
        desc="需有CSS樣式規則使用百分比數值或相對長度單位來設定欄寬，且最大欄寬不得超過80個字母(中日韓語系的40個文字)",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        decls = collect_declarations(soup, url)
        widths = [d for d in decls if d.prop in ("width", "max-width")]
        if not widths:
            return
        any_relative = False
        absolute_offenders: list[tuple[str, str]] = []
        for d in widths:
            v = d.value.lower().rstrip(";")
            if not v or v in ("auto", "inherit", "initial", "unset"):
                continue
            if any(v.startswith(fn) for fn in _FUNCTIONAL_PREFIXES):
                any_relative = True
                continue
            if v.endswith(("%", "em", "rem", "ch", "vw")):
                any_relative = True
                continue
            if _ABSOLUTE_UNIT_RE.search(v):
                absolute_offenders.append((v, d.source))
        if not any_relative and absolute_offenders:
            sample = ", ".join(o[0] for o in absolute_offenders[:3])
            status = "info" if ctx.freego_compat else "fail"
            report.add(self._issue(
                message="未發現以百分比或相對長度單位設定欄寬之 CSS 規則。",
                snippet=sample,
                status=status,
            ))

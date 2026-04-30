"""HM1130103C_1 rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class OptgroupLabel(Rule):
    """HM1130103C_1 — <optgroup> needs unique non-empty label."""

    meta = RuleMeta(
        rule_id="HM1130103C_1",
        guideline="1.3.1",
        level=Level.A,
        desc="表單選擇<select>組件則需以選項分群<optgroup>組件來將選項<option>組件加以分群",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        for s in soup.find_all("select"):
            if not isinstance(s, Tag) or should_skip(s):
                continue
            optgroups = s.find_all("optgroup")
            if not optgroups:
                continue
            seen: set[str] = set()
            for og in optgroups:
                if not og.has_attr("label"):
                    report.add(self._issue(
                        message="使用optgroup元素群組選擇項，請提供該元素之label屬性幫助螢幕報讀軟體報讀。",
                        snippet=truncate(str(og)),
                    ))
                    return
                lbl = (og.get("label") or "").strip()
                if not lbl:
                    report.add(self._issue(
                        message="optgroup元素中的label屬性不可以是空值或重複其他label屬性內容。",
                        snippet=truncate(str(og)),
                    ))
                    return
                if lbl in seen:
                    report.add(self._issue(
                        message="optgroup元素中的label屬性不可以是空值或重複其他label屬性內容。",
                        snippet=truncate(str(og)),
                    ))
                    return
                seen.add(lbl)

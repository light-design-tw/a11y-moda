"""HM1130100C rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.structure import _SECTIONING, _HEADINGS


@register
class HeadingHierarchy(Rule):
    """HM1130100C — headings exist and form valid nested structure."""

    meta = RuleMeta(
        rule_id="HM1130100C",
        guideline="1.3.1",
        level=Level.A,
        desc="網頁中的標頭組件必須要按照正確的巢狀層次結構來配置",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        before_count = len(report.issues)
        headings = [t for t in soup.find_all(_HEADINGS) if isinstance(t, Tag) and not should_skip(t)]
        role_headings = [
            t for t in soup.find_all(attrs={"role": "heading"})
            if isinstance(t, Tag) and not should_skip(t)
        ]

        if not headings:
            for rh in role_headings:
                lvl = (rh.get("aria-level") or "").strip()
                if not lvl:
                    report.add(self._issue(
                        message="使用role=heading角色時，aria-level為必要屬性，且不可為空值。",
                        snippet=truncate(str(rh)),
                    ))
                    ctx.state["HM1130100C_ok"] = False
                    return
            if not role_headings:
                report.add(self._issue(message="網頁請使用標題組件提供螢幕報讀軟體使用者辨識網頁結構並有利操作"))
                ctx.state["HM1130100C_ok"] = False
                return

        if not soup.find(_SECTIONING) and len([h for h in headings if h.name == "h1"]) > 1:
            report.add(self._issue(
                message="使用標題組件，其內容不可以為空值，且不要使用超過一個以上的h1層級標題。",
            ))
            return

        for t in headings:
            imgs = [c for c in t.find_all("img") if isinstance(c, Tag) and not should_skip(c)]
            if imgs:
                if t.get_text(strip=True):
                    continue
                for img in imgs:
                    if not img.has_attr("alt") or img.get("alt", "").strip() == "":
                        report.add(self._issue(
                            message="使用標題組件，其內容不可以為空值。",
                            snippet=truncate(str(t)),
                        ))
                        return
                continue
            if not t.get_text(strip=True):
                report.add(self._issue(
                    message="使用標題組件，其內容不可以為空值。",
                    snippet=truncate(str(t)),
                ))
                return

        for rh in role_headings:
            if not rh.has_attr("aria-level") or (rh.get("aria-level") or "").strip() == "":
                report.add(self._issue(
                    message="使用role=heading角色時，aria-level為必要屬性，且不可為空值。",
                    snippet=truncate(str(rh)),
                ))
                ctx.state["HM1130100C_ok"] = False
                return
        ctx.state["HM1130100C_ok"] = len(report.issues) == before_count

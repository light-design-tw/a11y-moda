"""HM1240401C rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.nav_links import _resolve_labelledby, _inline_hidden


@register
class LinkHasAccessibleText(Rule):
    """HM1240401C — <a> with href needs accessible text/label/img alt/svg name."""

    meta = RuleMeta(
        rule_id="HM1240401C",
        guideline="2.4.4",
        level=Level.A,
        desc="具有連結目的之鏈結<a>組件均需有鏈結文字，且其內容不得為空字串或空白",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        for a in soup.find_all("a", href=True):
            if not isinstance(a, Tag) or should_skip(a):
                continue
            if not (a.get("href") or "").strip():
                continue
            text = a.get_text().strip()
            spans = [s for s in a.find_all("span") if isinstance(s, Tag)]
            if spans and all(_inline_hidden(s) for s in spans):
                hidden_text = "".join(s.get_text() for s in spans if _inline_hidden(s))
                text = text.replace(hidden_text, "").strip()
            if text:
                continue
            if (a.get("aria-label") or "").strip():
                continue
            imgs = [i for i in a.find_all("img") if isinstance(i, Tag) and not should_skip(i)]
            if imgs:
                if any((i.has_attr("alt") and (i.get("alt") or "").strip()) for i in imgs):
                    continue
                report.add(self._issue(
                    message="具有連結用途的圖片超連結，圖片的替代文字不可以是空值。",
                    snippet=truncate(str(a)),
                ))
                return
            svgs = [s for s in a.find_all("svg") if isinstance(s, Tag) and (s.get("role") or "").strip() == "img"]
            if svgs:
                ok = False
                for svg in svgs:
                    if (svg.get("aria-label") or "").strip() or _resolve_labelledby(svg, soup):
                        ok = True
                        break
                if ok:
                    continue
                report.add(self._issue(
                    message="在非img元素使用role=img角色時，應有該角色的替代文字內容，供螢幕報讀軟體辨識。",
                    snippet=truncate(str(a)),
                ))
                return
            report.add(self._issue(
                message="具有連結目的之鏈結組件內需有連結文字或圖片。",
                snippet=truncate(str(a)),
            ))
            return

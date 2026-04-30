"""HM1410200C rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.nav_links import _resolve_labelledby


@register
class FormButtonAndLinkRoles(Rule):
    """HM1410200C — input/button need value/label, links/forms must not use role=presentation when focusable."""

    meta = RuleMeta(
        rule_id="HM1410200C",
        guideline="4.1.2",
        level=Level.A,
        desc="依據規格使用表單控制元件組件及鏈結組件，完整提供各組件之角色、名稱、屬性、值",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        for inp in soup.select("input[type=button]"):
            if not isinstance(inp, Tag) or should_skip(inp):
                continue
            if (inp.get("value") or "").strip() == "":
                report.add(self._issue(
                    message="input元素若型別為按鈕時，應要有可辨識的角色名稱，value屬性不可以是空值。",
                    snippet=truncate(str(inp)),
                ))
                return

        for btn in soup.find_all("button"):
            if not isinstance(btn, Tag) or should_skip(btn):
                continue
            if btn.get_text(strip=True):
                continue
            if (btn.get("aria-label") or "").strip() or _resolve_labelledby(btn, soup):
                continue
            if (btn.get("title") or "").strip():
                continue
            imgs = [i for i in btn.find_all("img") if isinstance(i, Tag) and not should_skip(i)]
            if imgs and any(i.has_attr("alt") and (i.get("alt") or "").strip() for i in imgs):
                continue
            svgs = [s for s in btn.find_all("svg") if isinstance(s, Tag)]
            svg_named = False
            for svg in svgs:
                if (svg.get("aria-label") or "").strip() or _resolve_labelledby(svg, soup):
                    svg_named = True
                    break
                title_el = svg.find("title")
                if isinstance(title_el, Tag) and (title_el.get_text(strip=True) or ""):
                    svg_named = True
                    break
            if svg_named:
                continue
            report.add(self._issue(
                message="button元素應要有可辨識的按鈕角色名稱。",
                snippet=truncate(str(btn)),
            ))
            return

        for el in soup.select("a[href], area[href], form, iframe, input[type], button[type], select[type], textarea[type]"):
            if not isinstance(el, Tag) or should_skip(el):
                continue
            if el.name in ("a", "area") and not (el.get("href") or "").strip():
                continue
            if (el.get("type") or "") == "hidden" or el.has_attr("disabled"):
                continue
            try:
                tabindex = int((el.get("tabindex") or "0").strip() or "0")
            except ValueError:
                continue
            if tabindex < 0:
                continue
            role = (el.get("role") or "").strip()
            if role in ("presentation", "none"):
                report.add(self._issue(
                    message="可以取得焦點之元素，不可使用role=presentation或role=none角色，以免造成螢幕報讀軟體無法報讀。",
                    snippet=truncate(str(el)),
                ))
                return

"""HM1110105C rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.img_alt import _has_referenced_label


@register
class ObjectAlt(Rule):
    """HM1110105C — <applet>/<object> need non-empty text alternative."""

    meta = RuleMeta(
        rule_id="HM1110105C",
        guideline="1.1.1",
        level=Level.A,
        desc="物件組件(如<applet>、<embed>、<object>)需有替代文字內容",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        for applet in soup.find_all("applet"):
            if not isinstance(applet, Tag) or should_skip(applet):
                continue
            if applet.has_attr("alt") and applet.get("alt", "").strip():
                continue
            report.add(self._issue(
                message="使用applet元素須以alt屬性描述該元素，或於元素區塊中請提供該元素的替代文字。",
                snippet=truncate(str(applet)),
            ))
            return

        for obj in soup.find_all("object"):
            if not isinstance(obj, Tag) or should_skip(obj):
                continue
            if (obj.get("title") or "").strip() or obj.has_attr("aria-label"):
                continue
            if _has_referenced_label(obj, soup):
                continue
            if obj.get_text(strip=True):
                continue
            child_tags = [c for c in obj.find_all(recursive=False) if isinstance(c, Tag)]
            if child_tags and any(c.name and c.name.lower() != "param" for c in child_tags):
                continue
            report.add(self._issue(
                message="使用object元素，須提供不為空值的替代內容。",
                snippet=truncate(str(obj)),
            ))
            return

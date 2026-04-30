"""CS2141200E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


@register
class TextSpacingOverride(Rule):
    """CS2141200E — author CSS should not prevent user spacing override."""

    meta = RuleMeta(rule_id="CS2141200E", guideline="1.4.12", level=Level.AA,
        desc="允許使用者按照其偏好覆蓋原有的網頁文字設定間距",
        source="extension")

    def _check(self, soup, report, *, html, url, ctx) -> None:
        from ....css_utils import collect_declarations
        decls = collect_declarations(soup, url)
        for d in decls:
            v = d.value.lower()
            if d.prop in ("line-height", "letter-spacing", "word-spacing") and "!important" in v:
                report.add(self._issue(
                    message=f"{d.prop} 使用 !important，會阻擋使用者覆蓋偏好間距。",
                    snippet=truncate(d.value, 200),
                    status="info",
                ))
                return

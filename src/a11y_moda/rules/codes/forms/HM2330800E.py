"""HM2330800E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate

# Auth-relevant input types and their expected autocomplete tokens.
_AUTH_TYPES = {
    "password": ("current-password", "new-password"),
    "email": ("email", "username"),
}


@register
class AuthInputAutocomplete(Rule):
    """HM2330800E — email/password inputs need appropriate autocomplete (3.3.8)."""

    meta = RuleMeta(
        rule_id="HM2330800E",
        guideline="3.3.8",
        level=Level.AA,
        desc="電子郵件與密碼輸入欄位應提供適當的 autocomplete 標記，協助密碼管理器與瀏覽器自動填入，符合可及的驗證",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        # HM2130500E validates the token WHEN autocomplete is present (1.3.5);
        # this rule covers the 3.3.8 angle — auth fields that lack it entirely.
        for inp in soup.find_all("input"):
            if not isinstance(inp, Tag) or should_skip(inp):
                continue
            t = (inp.get("type") or "").strip().lower()
            if t not in _AUTH_TYPES:
                continue
            ac = (inp.get("autocomplete") or "").strip().lower()
            if ac and ac != "off":
                continue
            rec = " / ".join(_AUTH_TYPES[t])
            state = "停用 (off)" if ac == "off" else "未設"
            report.add(self._issue(
                message=(
                    f"{t} 輸入欄位的 autocomplete {state}，密碼管理器/自動填入無法協助，影響可及的驗證(3.3.8)。"
                    f"建議設 autocomplete=\"{rec}\"。"
                ),
                snippet=truncate(str(inp)),
            ))
            return

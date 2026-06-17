"""FA2330801E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate

# Inline onpaste handlers that cancel the paste (block re-entry).
_BLOCK_TOKENS = ("returnfalse", "preventdefault", "return!1")
# Auth / verification-code style fields where blocking paste hurts most.
_GUARDED_TYPES = ("password", "text", "email", "tel", "number")


@register
class AuthInputPasteBlocked(Rule):
    """FA2330801E — blocking paste on password/code inputs fails 3.3.8/3.3.9."""

    meta = RuleMeta(
        rule_id="FA2330801E",
        guideline="3.3.8",
        level=Level.AA,
        desc="阻擋密碼或驗證碼欄位的貼上/重新輸入（如 onpaste 回傳 false），使用者無法以密碼管理器填入，導致可及的驗證失敗",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        # Inline handlers only — addEventListener('paste', …) is invisible to
        # static parsing.
        for inp in soup.find_all("input"):
            if not isinstance(inp, Tag) or should_skip(inp):
                continue
            t = (inp.get("type") or "").strip().lower()
            if t not in _GUARDED_TYPES:
                continue
            raw = (inp.get("onpaste") or "").strip()
            if not raw:
                continue
            norm = raw.lower().replace(" ", "")
            if norm == "false" or any(tok in norm for tok in _BLOCK_TOKENS):
                report.add(self._issue(
                    message=(
                        f"{t} 欄位以 onpaste 阻擋貼上（{truncate(raw, 40)}），使用者無法以密碼管理器或複製貼上"
                        f"填入，影響可及的驗證(3.3.8/3.3.9)。請移除貼上限制。"
                    ),
                    snippet=truncate(str(inp)),
                ))
                return

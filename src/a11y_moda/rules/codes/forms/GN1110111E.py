"""GN1110111E rule."""
from __future__ import annotations
import re
from bs4 import BeautifulSoup, Tag
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate


_CAPTCHA_HINT_RE = re.compile(r"captcha|驗證碼|驗證圖|圖形驗證|recaptcha|hcaptcha|turnstile|geetest", re.IGNORECASE)
_ALT_METHOD_RE = re.compile(r"語音|聲音|audio|email|電子郵件|郵件|mail|電話|客服|傳真|fax", re.IGNORECASE)
_THIRD_PARTY_BUILTIN = re.compile(r"recaptcha|hcaptcha|turnstile", re.IGNORECASE)


@register
class CaptchaAlternative(Rule):
    """GN1110111E — CAPTCHA must offer a second verification method (audio / email)."""

    meta = RuleMeta(
        rule_id="GN1110111E",
        guideline="1.1.1",
        level=Level.A,
        desc="CAPTCHA驗證機制須提供至少一種替代驗證方式（語音、電子郵件等）",
        source="extension",
    )

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx) -> None:
        for el in self._candidates(soup):
            if should_skip(el):
                continue
            if self._has_builtin_audio(el):
                continue
            if self._has_alternative_nearby(el):
                continue
            report.add(self._issue(
                message="疑似 CAPTCHA 驗證但未發現替代方式（語音／email／客服等），障礙使用者無法通過驗證。",
                snippet=truncate(str(el), 200),
            ))
            return

    @staticmethod
    def _candidates(soup: BeautifulSoup) -> list[Tag]:
        out: list[Tag] = []
        for el in soup.find_all(["img", "input", "canvas", "iframe"]):
            if not isinstance(el, Tag):
                continue
            blob = " ".join([
                el.get("alt") or "",
                el.get("src") or "",
                el.get("title") or "",
                el.get("aria-label") or "",
                " ".join(el.get("class") or []),
                el.get("id") or "",
            ])
            if _CAPTCHA_HINT_RE.search(blob):
                out.append(el)
        return out

    @staticmethod
    def _has_builtin_audio(el: Tag) -> bool:
        src_blob = (el.get("src") or "") + " " + " ".join(el.get("class") or [])
        return bool(_THIRD_PARTY_BUILTIN.search(src_blob))

    @staticmethod
    def _has_alternative_nearby(el: Tag) -> bool:
        scope: Tag | None = el
        for _ in range(3):
            if scope is None or not isinstance(scope, Tag):
                break
            if scope.find("audio"):
                return True
            for a in scope.find_all("a", href=True):
                if (a.get("href") or "").lower().startswith(("mailto:", "tel:")):
                    return True
            text = scope.get_text(" ", strip=True)
            if _ALT_METHOD_RE.search(text):
                return True
            scope = scope.parent if isinstance(scope.parent, Tag) else None
        return False

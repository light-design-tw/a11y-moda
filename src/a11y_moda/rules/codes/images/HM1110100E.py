"""HM1110100E rule."""
from __future__ import annotations
import re
from bs4 import BeautifulSoup, Tag
from ....llm import parse_verdict
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, _SAMPLE_LIMIT, have_llm, judge_or_caveat


@register
class AltAppropriateness(Rule):
    """HM1110100E — alt text should describe image purpose, not just exist."""

    meta = RuleMeta(
        rule_id="HM1110100E",
        guideline="1.1.1",
        level=Level.A,
        desc="圖片需要加上有意義、可代替圖片在文件上下文中的功能及內容的替代文字",
        source="extension",
    )

    SYSTEM = f"""你是無障礙稽核員。依 WCAG 1.1.1 判斷 <img> 的 alt 屬性是否能傳達圖片的功能或內容。

判斷標準（最低合規門檻，不是「最佳」）：
- pass：alt 含具體名詞或動作描述
- fail：alt 為檔名（如 image1.jpg、IMG_0001.png）、純通用詞（image、icon、圖片、照片）、或純標點
- unsure：alt 短但語意可能成立、或脈絡不明

{OUTPUT_INSTRUCTIONS}"""

    def _check(self, soup: BeautifulSoup, report: PageReport, *, html, url, ctx) -> None:
        if not have_llm(ctx):
            return
        candidates: list[tuple[Tag, str]] = []
        for img in soup.find_all("img"):
            if not isinstance(img, Tag) or should_skip(img):
                continue
            if not img.has_attr("alt"):
                continue
            alt = (img.get("alt") or "").strip()
            if not alt:
                continue
            if len(alt) > 30:
                continue
            src = img.get("src", "")
            parent_text = (img.parent.get_text(" ", strip=True) if isinstance(img.parent, Tag) else "")[:200]
            user_msg = f"src: {src}\nalt: {alt}\ncontext: {parent_text or '(none)'}"
            candidates.append((img, user_msg))
            if len(candidates) >= _SAMPLE_LIMIT:
                break
        for img, msg in candidates:
            try:
                verdict, reason = parse_verdict(ctx.llm.judge(self.SYSTEM, msg, max_tokens=2048))
            except Exception as e:
                report.add(self._issue(message=f"LLM err: {e}", status="caveat"))
                return
            if verdict == "fail":
                report.add(self._issue(
                    message=f"alt 不適切：{reason}",
                    snippet=truncate(str(img), 200), status="info"))
                return

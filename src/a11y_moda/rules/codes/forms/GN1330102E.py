"""GN1330102E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, _SAMPLE_LIMIT, have_llm, judge_or_caveat


@register
class SuccessFeedbackPresent(Rule):
    """GN1330102E — successful submission should give explicit feedback."""

    meta = RuleMeta(rule_id="GN1330102E", guideline="3.3.1", level=Level.A,
        desc="資料成功送出後，提供成功的回饋",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。依 WCAG 3.3.1 判斷送出成功訊息是否明確。

判斷標準：
- pass：訊息含「成功」「已送出」「已收到」等明確狀態詞，或下一步指引
- fail：訊息含糊（「謝謝」「OK」） 或僅 emoji

{OUTPUT_INSTRUCTIONS}"""

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not have_llm(ctx):
            return
        msgs = []
        for el in soup.find_all(True):
            if not isinstance(el, Tag) or should_skip(el):
                continue
            cls = " ".join(el.get("class") or [])
            if "success" not in cls.lower() and "thank" not in (el.get_text() or "").lower()[:60]:
                continue
            text = el.get_text(" ", strip=True)
            if 5 < len(text) < 300:
                msgs.append(text)
            if len(msgs) >= 3:
                break
        if not msgs:
            return
        joined = "\n---\n".join(msgs)
        v = judge_or_caveat(self, ctx, report, self.SYSTEM, joined)
        if v is None:
            return
        if v[0] == "fail":
            report.add(self._issue(
                message=f"成功回饋訊息不明確：{v[1]}",
                snippet=truncate(joined, 300), status="info"))

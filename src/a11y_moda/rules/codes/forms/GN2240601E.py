"""GN2240601E rule."""
from __future__ import annotations
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, _SAMPLE_LIMIT, have_llm, judge_or_caveat


@register
class FormLabelDescriptive(Rule):
    """GN2240601E — form labels must describe the purpose of each control."""

    meta = RuleMeta(
        rule_id="GN2240601E",
        guideline="2.4.6",
        level=Level.AA,
        desc="提供描述性的標籤",
        source="extension",
    )

    SYSTEM = f"""你是無障礙稽核員。依 WCAG 2.4.6 判斷表單 label 是否能讓使用者知道應填什麼。

判斷標準（最低合規門檻）：
- pass：label 含具名識別詞（即使簡短，例如「姓名」「Email」「電話」）
- fail：label 為空、僅標點、或純通用詞（input、value、data、欄位）
- unsure：邊界

{OUTPUT_INSTRUCTIONS}"""

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not have_llm(ctx):
            return
        labels = {l.get("for", "").strip(): l for l in soup.find_all("label") if isinstance(l, Tag) and l.get("for")}
        candidates: list[tuple[Tag, str, str]] = []
        for inp in soup.find_all(["input", "select", "textarea"]):
            if not isinstance(inp, Tag) or should_skip(inp):
                continue
            t = (inp.get("type") or "text").lower()
            if t in ("hidden", "submit", "button", "reset", "image"):
                continue
            iid = (inp.get("id") or "").strip()
            label_text = (labels[iid].get_text(strip=True) if iid in labels else "")
            if not label_text:
                label_text = (inp.get("aria-label") or "").strip()
            if not label_text:
                continue
            placeholder = (inp.get("placeholder") or "").strip()
            candidates.append((inp, label_text, placeholder))
            if len(candidates) >= _SAMPLE_LIMIT:
                break
        for inp, lbl, ph in candidates:
            msg = f"label: {lbl}\ntype: {inp.get('type','text')}\nplaceholder: {ph or '(none)'}\nname: {inp.get('name','')}"
            v = judge_or_caveat(self, ctx, report, self.SYSTEM, msg)
            if v is None:
                return
            if v[0] == "fail":
                report.add(self._issue(
                    message=f"表單 label 不夠描述性：「{lbl}」— {v[1]}",
                    snippet=truncate(str(inp), 200), status="info"))
                return

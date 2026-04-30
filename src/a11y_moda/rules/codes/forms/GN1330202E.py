"""GN1330202E rule."""
from __future__ import annotations
import re
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, _SAMPLE_LIMIT, have_llm, judge_or_caveat


@register
class ExpectedFormatExample(Rule):
    """GN1330202E — provide example of expected input format."""

    meta = RuleMeta(rule_id="GN1330202E", guideline="3.3.2", level=Level.A,
        desc="提供預期的資料格式與範例",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。依 WCAG 3.3.2 判斷需要特定格式的欄位（電話、日期、Email）是否提供格式範例。

判斷標準：
- pass：label / placeholder / hint 含具體範例格式
- fail：欄位需特定格式但完全無範例

{OUTPUT_INSTRUCTIONS}"""

    _NEEDS_EXAMPLE_TYPES = {"tel", "date", "datetime-local", "email", "url", "number"}

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not have_llm(ctx):
            return
        candidates = []
        for inp in soup.find_all("input"):
            if not isinstance(inp, Tag) or should_skip(inp):
                continue
            t = (inp.get("type") or "text").lower()
            if t not in self._NEEDS_EXAMPLE_TYPES:
                continue
            candidates.append(inp)
            if len(candidates) >= _SAMPLE_LIMIT:
                break
        for inp in candidates:
            placeholder = (inp.get("placeholder") or "").strip()
            label = ""
            iid = (inp.get("id") or "").strip()
            if iid:
                lbl = soup.find("label", attrs={"for": iid})
                if isinstance(lbl, Tag):
                    label = lbl.get_text(" ", strip=True)
            msg = f"type: {inp.get('type','text')}\nlabel: {label}\nplaceholder: {placeholder}\naria-describedby: {inp.get('aria-describedby','')}"
            v = judge_or_caveat(self, ctx, report, self.SYSTEM, msg)
            if v is None:
                return
            if v[0] == "fail":
                report.add(self._issue(
                    message=f"{inp.get('type','text')} 欄位未提供格式範例：{v[1]}",
                    snippet=truncate(str(inp), 200), status="info"))
                return

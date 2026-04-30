"""CS1130203E rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....llm import parse_verdict
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import truncate
from ..._lib.vision_rules import _have_vision, _vision_judge, _VISION_OUTPUT


@register
class VisualReadingOrder(Rule):
    """CS1130203E — visual reading order should make sense."""

    meta = RuleMeta(rule_id="CS1130203E", guideline="1.3.2", level=Level.A,
        desc="DOM物件順序需與視覺順序一致",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。看截圖，判斷視覺閱讀順序是否合理（從上到下、左到右）。

【fail】
- 標題在內文之後出現
- 操作按鈕在說明文字之前
- 副標跑到主標前
- 視覺上區塊跳來跳去

【pass】
- 順序合理
- 看起來流暢

【unsure】
- 創意排版難判斷

{_VISION_OUTPUT}"""

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not _have_vision(ctx):
            return
        v = _vision_judge(self, ctx, report, self.SYSTEM,
                          "判斷視覺閱讀順序是否合理",
                          ctx.viewport_screenshot)
        if v is None:
            return
        if v[0] == "fail":
            report.add(self._issue(
                message=f"視覺閱讀順序疑有問題：{v[1]}",
                status="info",
            ))

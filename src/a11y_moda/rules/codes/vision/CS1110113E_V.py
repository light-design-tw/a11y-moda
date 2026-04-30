"""CS1110113E_V rule."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ....llm import parse_verdict
from ....models import Level, PageReport
from ...base import Rule, RuleMeta, register
from ...helpers import truncate
from ..._lib.vision_rules import _have_vision, _vision_judge, _VISION_OUTPUT


@register
class DecorativeImagesViaCssVision(Rule):
    """CS1110113E_V — vision check augmenting programmatic decorative-image detection."""

    meta = RuleMeta(rule_id="CS1110113E_V", guideline="1.1.1", level=Level.A,
        desc="裝飾性圖片均透過CSS來置入（視覺判斷）",
        source="extension")

    SYSTEM = f"""你是無障礙稽核員。看截圖，判斷頁面中是否有大量「明顯裝飾用」圖片應改 CSS background。

【fail】
- 重複的線條 / 紋理 / 漸層當 <img>
- 純美觀分隔線當 <img>
- icon 反覆出現當 <img>（應用 CSS sprite 或 SVG）

【pass】
- 圖片都有資訊內容（產品照、流程圖、頭像）
- 截圖無圖片

{_VISION_OUTPUT}"""

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not _have_vision(ctx):
            return
        # Skip when too few <img> to be worth checking
        if len(soup.find_all("img")) < 3:
            return
        v = _vision_judge(self, ctx, report, self.SYSTEM,
                          "判斷頁面圖片是否大量為裝飾用",
                          ctx.viewport_screenshot)
        if v is None:
            return
        if v[0] == "fail":
            report.add(self._issue(
                message=f"視覺判斷頁面有裝飾性圖片宜改 CSS：{v[1]}",
                status="info",
            ))

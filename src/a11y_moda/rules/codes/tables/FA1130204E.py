"""FA1130204E rule."""
from __future__ import annotations
from bs4 import Tag
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate
from ..._lib.llm_common import OUTPUT_INSTRUCTIONS, have_llm, judge_or_caveat

# Block-level content inside a cell signals layout (vs tabular data) use.
_BLOCK_TAGS = ("p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "section", "article", "img")


@register
class LayoutTableLinearization(Rule):
    """FA1130204E — a layout table must linearise into a meaningful sequence (1.3.2)."""

    meta = RuleMeta(
        rule_id="FA1130204E",
        guideline="1.3.2",
        level=Level.A,
        desc="以 HTML 排版表格佈局時，線性化（依原始碼順序逐格閱讀）後仍須保持有意義的序列",
        source="extension",
    )

    SYSTEM = f"""你是無障礙稽核員。依 WCAG 1.3.2，判斷一個「排版用」表格線性化後（螢幕報讀軟體依原始碼順序、逐列逐欄讀出儲存格）閱讀序列是否仍有意義。

判斷標準：
- pass：逐格讀出的順序連貫、語意完整（例如每列為一組相關內容）
- fail：逐格讀出會在不相關的欄位間跳動、語意斷裂（典型：多欄並排的獨立內容被交錯讀出）

{OUTPUT_INSTRUCTIONS}"""

    def _check(self, soup, report, *, html, url, ctx) -> None:
        if not have_llm(ctx):
            return
        for table in soup.find_all("table"):
            if not isinstance(table, Tag) or should_skip(table):
                continue
            if table.find("th"):
                continue  # a marked data table, not a layout table
            rows = [r for r in table.find_all("tr") if isinstance(r, Tag)]
            if len(rows) < 2:
                continue
            cells: list[str] = []
            block_cells = 0
            for r in rows:
                rc = [c for c in r.find_all("td", recursive=False) if isinstance(c, Tag)]
                if len(rc) < 2:
                    continue  # need ≥2 columns to have a linearisation risk
                for c in rc:
                    if any(c.find(b) for b in _BLOCK_TAGS):
                        block_cells += 1
                    txt = c.get_text(" ", strip=True)
                    if txt:
                        cells.append(txt[:120])
            # Layout-table signal: multi-column rows whose cells carry block content.
            if len(cells) < 4 or block_cells < 2:
                continue
            linear = " | ".join(cells)[:1200]
            msg = f"排版表格線性化後的儲存格順序：\n{linear}"
            v = judge_or_caveat(self, ctx, report, self.SYSTEM, msg)
            if v is None:
                return
            if v[0] == "fail":
                report.add(self._issue(
                    message=f"排版表格線性化後序列不具意義：{v[1]}",
                    snippet=truncate(str(table)[:200]),
                    status="info",
                ))
            return

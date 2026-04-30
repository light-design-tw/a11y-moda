"""Shared helpers and constants."""
from __future__ import annotations
from bs4 import BeautifulSoup, Tag
from ...llm import parse_verdict
from ...models import Level, PageReport
from ..base import Rule, RuleMeta, register
from ..helpers import truncate


_VISION_OUTPUT = """
【輸出格式（嚴格遵守）】
固定兩行：
VERDICT: pass | fail | unsure
REASON: 一句繁體中文（不超過 50 字）

【一律繁體中文（zh-TW）。禁簡體字、英文。】
"""

def _have_vision(ctx) -> bool:
    if not getattr(ctx, "llm", None):
        return False
    if not ctx.llm.supports_vision():
        return False
    if not ctx.viewport_screenshot:
        return False
    return True

def _vision_judge(rule, ctx, report, system: str, user: str, image: bytes, *, max_tokens: int = 2048):
    try:
        return parse_verdict(ctx.llm.judge_with_image(system, user, image, max_tokens=max_tokens))
    except Exception as e:
        report.add(rule._issue(message=f"Vision LLM err: {e}", status="caveat"))
        return None


"""Shared helpers + prompts for all LLM-judged rules. (relocated to _lib)"""
from __future__ import annotations

from ...llm import parse_verdict


_SAMPLE_LIMIT = 8


SKIP_LINK_PATTERNS = (
    "跳至主要內容", "跳到主要內容", "跳到內容", "跳過導覽", "跳過導航", "跳至內容區",
    "skip to main content", "skip to content", "skip navigation", "skip nav",
    "skip to navigation", "jump to content", "jump to main",
)

UNIVERSAL_NAV_LABELS = (
    "首頁", "回首頁", "回到首頁", "返回", "上一頁", "下一頁",
    "登入", "登出", "註冊", "註冊會員", "會員登入", "加入會員", "會員中心",
    "搜尋", "搜索", "查詢", "送出", "確定", "取消",
    "聯絡我們", "聯繫我們", "關於我們",
    "home", "back", "next", "previous", "login", "logout", "sign in", "sign up", "register",
    "search", "submit", "cancel", "ok", "contact", "about",
)

VAGUE_BLACKLIST = (
    "click here", "click", "here", "點此", "點這裡", "請點此",
    "more", "more...", "更多", "詳細", "詳情",
    "link", "連結", "按鈕", "go", "繼續",
    "...", "→", ">", "»",
)


OUTPUT_INSTRUCTIONS = """\
【輸出格式（嚴格遵守）】
固定兩行：
VERDICT: pass | fail | unsure
REASON: 一句繁體中文說明（不超過 50 字）

【一律使用繁體中文回覆，禁用簡體字、英文。】
"""


def is_standard_pattern(text: str) -> bool:
    """True when text is a known a11y convention or universal nav — pass without LLM."""
    if not text:
        return False
    low = text.strip().lower()
    if any(low == p.lower() for p in SKIP_LINK_PATTERNS):
        return True
    if any(low == p.lower() for p in UNIVERSAL_NAV_LABELS):
        return True
    return False


def is_definitely_vague(text: str) -> bool:
    """True when text is on the obvious vague blacklist — fail without LLM."""
    if not text:
        return True
    low = text.strip().lower()
    return any(low == p.lower() or low == p for p in VAGUE_BLACKLIST)


def have_llm(ctx) -> bool:
    return getattr(ctx, "llm", None) is not None


def judge_or_caveat(rule, ctx, report, system, user, max_tokens=2048):
    """Run LLM call, log caveat on failure, return (verdict, reason) or None."""
    try:
        return parse_verdict(ctx.llm.judge(system, user, max_tokens=max_tokens))
    except Exception as e:
        report.add(rule._issue(message=f"LLM err: {e}", status="caveat"))
        return None

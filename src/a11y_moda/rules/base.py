from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from bs4 import BeautifulSoup

from ..models import Issue, Level, PageReport


@dataclass
class RuleMeta:
    rule_id: str
    guideline: str
    level: Level
    desc: str
    # source = "freego" → rule covered by the official MODA tool's machine checks;
    # source = "extension" → an E (人工/manual) rule we automated programmatically.
    source: str = "freego"


@dataclass
class RuleContext:
    """Per-page state shared across rules in a single scan."""
    state: dict[str, Any] = field(default_factory=dict)
    freego_compat: bool = False  # align reporting behaviour with the official MODA tool
    ignore: set[str] = field(default_factory=set)  # rule_ids to skip
    text_samples: list = field(default_factory=list)   # populated when browser scan runs
    tab_stops: list = field(default_factory=list)
    browser_used: bool = False
    llm: Any = None  # LLMClient or None — rules check before using
    full_screenshot: bytes | None = None  # full-page PNG bytes (when --render)
    viewport_screenshot: bytes | None = None  # above-the-fold PNG bytes


class Rule(ABC):
    meta: RuleMeta

    def check(self, soup: BeautifulSoup, report: PageReport, *, html: str = "", url: str = "", ctx: RuleContext | None = None) -> None:
        if ctx is None:
            ctx = RuleContext()
        if self.meta.rule_id in ctx.ignore:
            return
        try:
            self._check(soup, report, html=html, url=url, ctx=ctx)
        except Exception as e:
            report.add(self._issue(message=f"檢測發生異常：{type(e).__name__}: {e}", status="caveat"))

    @abstractmethod
    def _check(self, soup: BeautifulSoup, report: PageReport, *, html: str, url: str, ctx: RuleContext) -> None: ...

    def _issue(self, *, message: str = "", snippet: str = "", status="fail") -> Issue:
        return Issue(
            rule_id=self.meta.rule_id,
            guideline=self.meta.guideline,
            level=self.meta.level,
            desc=self.meta.desc,
            message=message,
            snippet=snippet[:300],
            status=status,
        )


_REGISTRY: list[type[Rule]] = []


def register(cls: type[Rule]) -> type[Rule]:
    _REGISTRY.append(cls)
    return cls


def all_rules(level: Level | None = None, *, sources: set[str] | None = None) -> list[Rule]:
    rules = [c() for c in _REGISTRY]
    if level is not None:
        rules = [r for r in rules if r.meta.level <= level]
    if sources is not None:
        rules = [r for r in rules if r.meta.source in sources]
    return rules

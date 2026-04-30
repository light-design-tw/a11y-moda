from __future__ import annotations
import inspect
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
    form_sims: list = field(default_factory=list)      # FormProbeResult, populated when browser scan runs
    browser_used: bool = False
    llm: Any = None  # LLMClient or None — rules check before using
    full_screenshot: bytes | None = None  # full-page PNG bytes (when --render)
    viewport_screenshot: bytes | None = None  # above-the-fold PNG bytes


class Rule(ABC):
    meta: RuleMeta
    uses_llm: bool = False  # set automatically by @register

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


_LLM_MARKERS = ("ctx.llm", "judge_or_caveat", "judge_with_image", "from ..._lib.llm_", "from ..._lib.vision_rules")


def register(cls: type[Rule]) -> type[Rule]:
    """Register a rule. Auto-detect LLM use by inspecting the module source.

    A rule is flagged uses_llm=True if its source imports any of the LLM helper
    modules or calls ctx.llm / judge_or_caveat / judge_with_image directly.
    Used by the scanner to fan LLM-bound rules out across worker threads while
    keeping pure-DOM rules serial (they may share ctx.state).
    """
    try:
        src = inspect.getsource(inspect.getmodule(cls))
        cls.uses_llm = any(m in src for m in _LLM_MARKERS)
    except (OSError, TypeError):
        cls.uses_llm = False
    _REGISTRY.append(cls)
    return cls


def all_rules(level: Level | None = None, *, sources: set[str] | None = None) -> list[Rule]:
    rules = [c() for c in _REGISTRY]
    if level is not None:
        rules = [r for r in rules if r.meta.level <= level]
    if sources is not None:
        rules = [r for r in rules if r.meta.source in sources]
    return rules

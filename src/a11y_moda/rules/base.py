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
    # runtime_authoritative=True means the rule's verdict requires runtime
    # evidence (rendered DOM, computed CSS, focus traversal, cross-file event
    # wiring) that source-only AST cannot reach. The lint runner downgrades
    # any "fail" from such a rule to "caveat" — AST literally cannot prove
    # the violation, only suggest review. The scan runner ignores this flag
    # (it has Playwright + computed style and can fail authoritatively).
    runtime_authoritative: bool = False


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
        before = len(report.issues)
        try:
            self._check(soup, report, html=html, url=url, ctx=ctx)
        except Exception as e:
            report.add(self._issue(message=f"檢測發生異常：{type(e).__name__}: {e}", status="caveat"))
        # Downgrade issues whose violation lives in a third-party resource
        # (different root domain). User can opt out via --strict-third-party
        # or --freego-compat (Freego doesn't distinguish third-party).
        if not ctx.state.get("strict_third_party") and not ctx.freego_compat and url:
            from ._lib.origin import extract_resource_url, is_third_party, third_party_origin
            for issue in report.issues[before:]:
                if issue.status != "fail":
                    continue
                res_url = extract_resource_url(issue.snippet)
                if not res_url or not is_third_party(res_url, url):
                    continue
                origin = third_party_origin(res_url)
                issue.status = "caveat"
                issue.message = (
                    f"[third-party: {origin}] {issue.message} "
                    f"註：此違規來自第三方資源，需於申請時備註欄聲明 "
                    f"(參 WCAG 2.1 §5.4 Partial Conformance)。"
                )

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


# Names imported into a rule module from `_lib/llm_*` or `_lib/vision_rules`
# that signal the rule will issue an LLM/VLM call. Detected via vars(module)
# rather than re-reading source from disk — faster and more accurate (won't
# match commented-out examples).
_LLM_IMPORT_MARKERS = (
    "judge_or_caveat", "judge_with_image", "have_llm",          # _lib/llm_common
    "_vision_judge", "_have_vision",                              # _lib/vision_rules
)


def register(cls: type[Rule]) -> type[Rule]:
    """Register a rule. Auto-detect LLM use from imported names in module."""
    mod = inspect.getmodule(cls)
    mod_vars = vars(mod) if mod is not None else {}
    cls.uses_llm = any(name in mod_vars for name in _LLM_IMPORT_MARKERS)
    _REGISTRY.append(cls)
    return cls


def all_rules(level: Level | None = None, *, sources: set[str] | None = None) -> list[Rule]:
    rules = [c() for c in _REGISTRY]
    if level is not None:
        rules = [r for r in rules if r.meta.level <= level]
    if sources is not None:
        rules = [r for r in rules if r.meta.source in sources]
    return rules

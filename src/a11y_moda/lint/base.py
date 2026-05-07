"""Lint rule base class + auto-discovery registry.

Mirrors the design of `rules.base` (the scan registry) but operates on
parsed source files rather than rendered DOM. A LintRule's `_check`
yields LintIssue records; the runner aggregates them per-file.

Rules share `rule_id` with the scan stage by reusing `RuleMeta`. A finding
identified as `HM1110100C` at lint time refers to the same MODA code as
the same `HM1110100C` at scan time — agents and reports group across
stages by that ID.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Literal

from ..models import Level, Status
from ..rules.base import RuleMeta  # reuse the same meta shape as scan
from .parser import ParsedFile, Language


@dataclass
class LintIssue:
    """A finding emitted by a lint rule. Mirrors `models.Issue` plus location."""
    rule_id: str
    guideline: str
    level: Level
    desc: str
    message: str = ""
    snippet: str = ""
    status: Status = "fail"
    file_path: str = ""
    line: int = 0
    col: int = 0


class LintRule(ABC):
    meta: RuleMeta
    # Languages this rule applies to. Default: TSX/JSX (the majority of rules).
    # HTML-only or CSS-only rules override.
    applies_to: tuple[Language, ...] = ("tsx", "jsx", "ts", "js", "html")

    def check(self, parsed: ParsedFile) -> list[LintIssue]:
        if parsed.language not in self.applies_to:
            return []
        out: list[LintIssue] = []
        try:
            for issue in self._check(parsed):
                # Backfill file_path if rule forgot.
                if not issue.file_path:
                    issue.file_path = str(parsed.path)
                out.append(issue)
        except Exception as e:
            out.append(LintIssue(
                rule_id=self.meta.rule_id,
                guideline=self.meta.guideline,
                level=self.meta.level,
                desc=self.meta.desc,
                message=f"lint 規則執行例外：{type(e).__name__}: {e}",
                status="caveat",
                file_path=str(parsed.path),
            ))
        return out

    @abstractmethod
    def _check(self, parsed: ParsedFile) -> Iterable[LintIssue]: ...

    def _issue(self, *, status: Status, message: str, node=None, snippet_text: str = "") -> LintIssue:
        """Convenience constructor. Pass `node` to fill line/col automatically."""
        line, col = (0, 0)
        if node is not None:
            from .helpers import position, snippet
            line, col = position(node)
            if not snippet_text:
                snippet_text = snippet(node)
        return LintIssue(
            rule_id=self.meta.rule_id,
            guideline=self.meta.guideline,
            level=self.meta.level,
            desc=self.meta.desc,
            message=message,
            snippet=snippet_text[:300],
            status=status,
            line=line,
            col=col,
        )


_REGISTRY: list[type[LintRule]] = []


def register(cls: type[LintRule]) -> type[LintRule]:
    _REGISTRY.append(cls)
    return cls


def all_lint_rules(level: Level | None = None) -> list[LintRule]:
    """Auto-discover by importing every leaf module under codes/."""
    _autodiscover()
    rules = [c() for c in _REGISTRY]
    if level is not None:
        rules = [r for r in rules if r.meta.level <= level]
    return rules


_autodiscover_done = False


def _autodiscover() -> None:
    """Import every rule file under lint/codes/<topic>/ so @register fires."""
    global _autodiscover_done
    if _autodiscover_done:
        return
    import importlib
    import pkgutil
    from . import codes as _codes_pkg
    for topic in pkgutil.iter_modules(_codes_pkg.__path__):
        topic_pkg = importlib.import_module(f"{_codes_pkg.__name__}.{topic.name}")
        if not hasattr(topic_pkg, "__path__"):
            continue
        for leaf in pkgutil.iter_modules(topic_pkg.__path__):
            importlib.import_module(f"{topic_pkg.__name__}.{leaf.name}")
    _autodiscover_done = True

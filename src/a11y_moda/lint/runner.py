"""Walk source files, dispatch lint rules, aggregate results."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from ..models import Level
from .base import LintIssue, all_lint_rules
from .parser import detect_language, parse_file


_DEFAULT_EXTS = (".tsx", ".jsx", ".ts", ".js", ".html", ".htm")
# Directories never worth linting — bundles, deps, build cache.
_DEFAULT_EXCLUDE_DIRS = frozenset({
    "node_modules", ".next", ".nuxt", ".svelte-kit", ".astro",
    "dist", "build", "out", ".vercel", ".turbo",
    ".git", ".cache", "__pycache__", ".pytest_cache",
    ".a11y-moda",  # our own report dir
})


@dataclass
class FileResult:
    path: str
    language: str
    issues: list[LintIssue] = field(default_factory=list)
    fetch_error: str = ""

    @property
    def by_status(self) -> dict[str, int]:
        out = {"fail": 0, "caveat": 0, "info": 0, "pass": 0}
        for i in self.issues:
            out[i.status] = out.get(i.status, 0) + 1
        return out


@dataclass
class LintReport:
    files: list[FileResult] = field(default_factory=list)

    @property
    def summary(self) -> dict[str, int]:
        out = {"files_scanned": len(self.files), "fail": 0, "caveat": 0, "info": 0}
        for fr in self.files:
            for i in fr.issues:
                out[i.status] = out.get(i.status, 0) + 1
        return out


def expand_paths(inputs: Iterable[str | Path], *, exts: tuple[str, ...] = _DEFAULT_EXTS,
                  exclude_dirs: frozenset[str] = _DEFAULT_EXCLUDE_DIRS) -> list[Path]:
    """Resolve a mix of file/dir/glob inputs to a flat list of source files."""
    out: list[Path] = []
    seen: set[Path] = set()
    for raw in inputs:
        p = Path(raw)
        if p.is_file():
            if p.suffix.lower() in exts:
                rp = p.resolve()
                if rp not in seen:
                    seen.add(rp)
                    out.append(rp)
            continue
        if p.is_dir():
            for sub in p.rglob("*"):
                if sub.suffix.lower() not in exts:
                    continue
                # Skip excluded dirs anywhere in the path.
                if any(part in exclude_dirs for part in sub.parts):
                    continue
                if not sub.is_file():
                    continue
                rp = sub.resolve()
                if rp not in seen:
                    seen.add(rp)
                    out.append(rp)
    return sorted(out)


def lint_files(paths: list[Path], *, level: Level = Level.AA) -> LintReport:
    rules = all_lint_rules(level=level)
    report = LintReport()
    for path in paths:
        fr = FileResult(path=str(path), language=detect_language(path) or "")
        parsed = parse_file(path)
        if parsed is None:
            fr.fetch_error = "unsupported language or file too large"
            report.files.append(fr)
            continue
        for rule in rules:
            fr.issues.extend(rule.check(parsed))
        report.files.append(fr)
    return report

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


def _load_gitignore(root: Path):
    """Load .gitignore from a scanned directory (top level only — nested
    .gitignore files are not currently merged). Returns a pathspec or None.
    """
    gi = root / ".gitignore"
    if not gi.exists():
        return None
    try:
        from pathspec import PathSpec
        from pathspec.patterns import GitWildMatchPattern
    except ImportError:
        return None
    try:
        with open(gi, encoding="utf-8", errors="replace") as f:
            return PathSpec.from_lines(GitWildMatchPattern, f)
    except OSError:
        return None


def _build_user_spec(patterns: tuple[str, ...]):
    """Compile user-supplied --exclude glob patterns into a pathspec.

    Normalises backslashes to forward slashes for two reasons:
    1. gitignore syntax uses forward slashes regardless of OS.
    2. On Windows, the Python C runtime may glob-expand `**` when received
       as a separate argv element (e.g. `--exclude docs/**` becomes the
       mangled string `docs\\`). Normalising recovers the user's intent —
       `docs\\` becomes `docs/` which gitignore reads as "the docs directory".
       Tell users to prefer `--exclude=docs/**` (= form) on Windows to
       avoid the mangling entirely; this is a defence-in-depth fallback.
    """
    if not patterns:
        return None
    try:
        from pathspec import PathSpec
        from pathspec.patterns import GitWildMatchPattern
    except ImportError:
        return None
    cleaned = tuple(p.replace("\\", "/") for p in patterns)
    return PathSpec.from_lines(GitWildMatchPattern, cleaned)


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


def expand_paths(inputs: Iterable[str | Path], *,
                  exts: tuple[str, ...] = _DEFAULT_EXTS,
                  exclude_dirs: frozenset[str] = _DEFAULT_EXCLUDE_DIRS,
                  exclude_globs: tuple[str, ...] = (),
                  respect_gitignore: bool = True) -> list[Path]:
    """Resolve a mix of file/dir inputs to a flat list of source files.

    Filter chain (in order):
      1. Extension allowlist (exts).
      2. Built-in dir exclusion (node_modules / .next / dist / ...).
      3. .gitignore at each scanned dir root (if respect_gitignore).
      4. User --exclude glob patterns (exclude_globs).

    Files passed directly bypass all filters — caller asked for them.
    """
    out: list[Path] = []
    seen: set[Path] = set()
    user_spec = _build_user_spec(exclude_globs)
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
            gitignore_spec = _load_gitignore(p) if respect_gitignore else None
            for sub in p.rglob("*"):
                if sub.suffix.lower() not in exts:
                    continue
                # Built-in dir blocklist (anywhere in the path).
                if any(part in exclude_dirs for part in sub.parts):
                    continue
                if not sub.is_file():
                    continue
                # gitignore + user excludes match against paths relative to
                # the scanned directory (matches Git semantics).
                try:
                    rel = sub.relative_to(p).as_posix()
                except ValueError:
                    rel = str(sub)
                if gitignore_spec is not None and gitignore_spec.match_file(rel):
                    continue
                if user_spec is not None and user_spec.match_file(rel):
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

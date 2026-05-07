"""Tree-sitter parser facade for JSX/TSX/HTML source files.

Lazy-loads grammars on first use. Tree-sitter parsing is forgiving of
syntax errors (it returns a partial tree with ERROR nodes), which is
what we want — a half-typed JSX file in --watch mode should still surface
issues for the parts that did parse.
"""
from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal


Language = Literal["tsx", "jsx", "ts", "js", "html"]


# Per-file size cap. Rule-of-thumb: real source files are <100 KB; anything
# larger is generated code or vendored bundles we shouldn't be linting.
_MAX_FILE_BYTES = 5 * 1024 * 1024


@dataclass
class ParsedFile:
    """Parsed source — AST root + metadata for rules to query."""
    path: Path
    language: Language
    source: bytes               # raw file bytes (for snippet extraction)
    tree: object                # tree_sitter.Tree


def detect_language(path: Path) -> Language | None:
    suffix = path.suffix.lower()
    if suffix == ".tsx":
        return "tsx"
    if suffix == ".jsx":
        return "jsx"
    if suffix == ".ts":
        return "ts"
    if suffix == ".js":
        return "js"
    if suffix in (".html", ".htm"):
        return "html"
    return None


@lru_cache(maxsize=8)
def _get_parser(language: Language):
    """Lazy-load tree-sitter grammar; cache parser per language."""
    from tree_sitter import Language as TSLanguage, Parser
    if language in ("tsx", "jsx"):
        # tree-sitter-typescript ships two grammars; tsx handles JSX too.
        import tree_sitter_typescript as ts_ts
        lang = TSLanguage(ts_ts.language_tsx())
    elif language in ("ts", "js"):
        import tree_sitter_typescript as ts_ts
        lang = TSLanguage(ts_ts.language_typescript())
    elif language == "html":
        import tree_sitter_html as ts_html
        lang = TSLanguage(ts_html.language())
    else:
        raise ValueError(f"unsupported language: {language}")
    return Parser(lang)


def parse_file(path: Path) -> ParsedFile | None:
    """Parse a source file. Returns None if language unknown or file too large."""
    language = detect_language(path)
    if language is None:
        return None
    try:
        size = path.stat().st_size
    except OSError:
        return None
    if size > _MAX_FILE_BYTES:
        return None
    try:
        source = path.read_bytes()
    except OSError:
        return None
    parser = _get_parser(language)
    tree = parser.parse(source)
    return ParsedFile(path=path, language=language, source=source, tree=tree)


def parse_source(source: bytes, language: Language, path: Path | None = None) -> ParsedFile:
    """Parse a raw byte string — used by tests and CLI stdin path."""
    parser = _get_parser(language)
    tree = parser.parse(source)
    return ParsedFile(path=path or Path("<stdin>"), language=language, source=source, tree=tree)

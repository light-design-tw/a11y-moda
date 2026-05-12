"""Command-line entry."""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

import click

# Windows consoles default to a non-UTF-8 code page (cp950 on zh-TW Windows),
# which mojibakes our zh-TW output. Reconfigure stdio before any rule output
# is emitted. POSIX systems already default to UTF-8.
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

from .crawler import crawl, discover
from .llm import LLMClient, LLMConfig
from .models import Level, PageReport, ScanReport
from .report import page_to_markdown, page_to_html_block, scan_to_markdown, scan_to_html
from .scanner import scan_page, scan_urls
from ._security import is_safe_http_url


def _load_env_files(explicit_path: str | None) -> None:
    """Load .env in three layers, lowest precedence first.

    Order (later loads do NOT override already-set vars):
      1. ~/.config/a11y-moda/.env   — global personal default
      2. ./.env                     — per-project (cwd)
      3. --env-file PATH            — explicit override (highest)

    Existing process-level env (shell `export`, Docker `-e`, CI runner)
    always wins because each load is called with override=False.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        if explicit_path:
            click.echo(f"warning: --env-file given but python-dotenv not installed; ignoring {explicit_path}",
                        err=True)
        return
    global_env = Path.home() / ".config" / "a11y-moda" / ".env"
    if global_env.exists():
        load_dotenv(global_env, override=False)
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        load_dotenv(cwd_env, override=False)
    if explicit_path:
        load_dotenv(explicit_path, override=False)


def _build_llm(base_url: str | None, key: str | None, model: str | None) -> LLMClient | None:
    cfg = None
    if base_url and model:
        cfg = LLMConfig(base_url=base_url, api_key=key or "sk-noauth", model=model)
    else:
        cfg = LLMConfig.from_env()
    return LLMClient(cfg) if cfg else None


def _llm_options(f):
    """Apply the four `--llm-*` options to a Click command."""
    f = click.option("--llm-concurrency", type=int, default=1,
                     help="Per-page LLM rule concurrency. Default 1 (serial). Raise on endpoints "
                          "that serve concurrent requests well (vLLM batched, OpenAI/Anthropic API). "
                          "Local single-GPU models may degrade or OOM above 1.")(f)
    f = click.option("--llm-model", default=None,
                     help="Model name (falls back to A11Y_LLM_MODEL env)")(f)
    f = click.option("--llm-key", default=None,
                     help="API key (falls back to A11Y_LLM_KEY / OPENAI_API_KEY env)")(f)
    f = click.option("--llm-base-url", default=None,
                     help="OpenAI-compatible endpoint, e.g. https://api.openai.com/v1")(f)
    return f


def _resolve_url(url: str, *, allow_file: bool) -> str:
    """Convert filesystem paths to file:// URIs when --allow-file is set.

    Lets the user pass `./index.html`, `D:\\dist\\index.html`, or
    `/var/www/site/` as if it were a URL. Without --allow-file we leave
    the value alone — the SSRF guard will reject a non-http(s) URL with a
    clearer message than "file not found".
    """
    if not allow_file:
        return url
    if url.startswith(("http://", "https://", "file://")):
        return url
    p = Path(url).resolve()
    return p.as_uri()


def _enforce_url_safety(url: str, *, allow_private: bool, allow_file: bool = False) -> None:
    """Block accidental scans of localhost / metadata / file:// URLs."""
    if allow_private:
        os.environ["A11Y_ALLOW_PRIVATE_HOSTS"] = "1"
    if allow_file:
        os.environ["A11Y_ALLOW_FILE"] = "1"
    if not is_safe_http_url(url, allow_private=allow_private, allow_file=allow_file):
        hints = ["Only public http(s) URLs allowed by default."]
        hints.append("Pass --allow-private-hosts to scan localhost / RFC1918 / link-local intranets.")
        hints.append("Pass --allow-file to scan local build output via file:// URLs or filesystem paths.")
        raise click.UsageError(f"refused unsafe URL: {url!r}. " + " ".join(hints))


def _serialize_page(report: PageReport) -> dict:
    return {
        "url": report.url,
        "status_code": report.status_code,
        "fetch_error": report.fetch_error,
        "issues": [
            {
                "rule_id": i.rule_id,
                "guideline": i.guideline,
                "level": int(i.level),
                "desc": i.desc,
                "message": i.message,
                "snippet": i.snippet,
                "status": i.status,
            }
            for i in report.issues
        ],
        "summary": {
            "fail": sum(1 for i in report.issues if i.status == "fail"),
            "info": sum(1 for i in report.issues if i.status == "info"),
            "caveat": sum(1 for i in report.issues if i.status == "caveat"),
        },
    }


def _serialize_scan(scan: ScanReport) -> dict:
    pages = [_serialize_page(p) for p in scan.pages]
    site_summary = {
        "pages_scanned": len(pages),
        "fail": sum(p["summary"]["fail"] for p in pages),
        "info": sum(p["summary"]["info"] for p in pages),
        "caveat": sum(p["summary"]["caveat"] for p in pages),
    }
    return {
        "site_summary": site_summary,
        "by_rule": scan.aggregate_by_rule(),
        "pages": pages,
    }


@click.group()
@click.version_option(None, "-V", "--version", package_name="a11y-moda", prog_name="a11y-moda")
@click.option("--env-file", type=click.Path(exists=True, dir_okay=False), default=None,
              help="Path to a .env file (highest precedence; must exist). Otherwise "
                   "loads ./.env and ~/.config/a11y-moda/.env when present. Existing "
                   "process env vars are never overridden.")
@click.pass_context
def main(ctx: click.Context, env_file: str | None) -> None:
    """Taiwan MODA accessibility CLI — WCAG A/AA/AAA · zh-TW · 129 rules.

    \b
    AUDIT (find a11y violations in your code or pages)
      lint <paths>          source-level (tree-sitter; no browser, no LLM)
      scan <URL>            one page (rendered DOM via Playwright)
      site <URL>            whole site (sitemap → BFS, rendered DOM)

    \b
    KNOWLEDGE (query MODA rule metadata; agents call these BEFORE writing
    accessibility-sensitive elements like <button>, <form>, <img>, etc.)
      rules list            list rules by level / topic / source / scope
      rules show <RULE_ID>  show one rule (rule_id, WCAG SC, level, desc, ...)
      rules search <query>  search by keyword / WCAG SC / topic
      explain  <RULE_ID>    short alias for `rules show`

    \b
    INTEGRATION (one-line install for AI agents / IDEs)
      init <ide>            install integration template (claude-code,
                            cursor, copilot, aider, agent)
      init --list           show all available IDE integrations

    \b
    INSTALL VARIANTS (since v0.3.0)
      pip install a11y-moda             lint + rules (lightweight ~30MB)
      pip install 'a11y-moda[scan]'     add browser-based scan / site
      playwright install chromium       required for --render

    Docs: https://github.com/light-design-tw/a11y-moda
    """
    _load_env_files(env_file)


def _serialize_lint(report) -> dict:
    return {
        "summary": report.summary,
        "files": [
            {
                "path": fr.path,
                "language": fr.language,
                "fetch_error": fr.fetch_error,
                "by_status": fr.by_status,
                "issues": [
                    {
                        "rule_id": i.rule_id,
                        "guideline": i.guideline,
                        "level": int(i.level),
                        "desc": i.desc,
                        "message": i.message,
                        "snippet": i.snippet,
                        "status": i.status,
                        "line": i.line,
                        "col": i.col,
                    }
                    for i in fr.issues
                ],
            }
            for fr in report.files
        ],
    }


@main.command()
@click.argument("paths", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("--level", type=click.Choice(["A", "AA", "AAA"]), default="AA",
              help="Compliance level. Lint emits all rules at or below this level.")
@click.option("--exclude", "exclude_globs", multiple=True,
              help="Glob pattern to exclude (repeatable). Matches against paths "
                   "relative to each scanned directory. Examples: "
                   "'**/*.test.tsx', 'app/api/og/**', 'packages/embeds/**'. "
                   "On Windows prefer the `--exclude=<pattern>` form (no space) — "
                   "the space-separated form may have `**` mangled by the C runtime.")
@click.option("--no-gitignore", is_flag=True, default=False,
              help="Don't apply .gitignore patterns from scanned directories. "
                   "Default: respected (matches behaviour of eslint, ruff, prettier).")
@click.option("--fail-only", is_flag=True, default=False,
              help="Show only `fail` issues (drop caveat/info). Useful for CI gating.")
@click.option("--strict", is_flag=True, default=False,
              help="Exit with non-zero status when any `fail` issue is present. "
                   "For pre-commit / CI: combine with --fail-only for hard gates.")
@click.option("--format", "fmt", type=click.Choice(["json", "md"]), default="json",
              help="Output format. JSON is the stable contract for AI agents and tools; "
                   "md is for humans.")
@click.option("--output", "-o", type=click.Path(), default=None,
              help="Write report to file. Bare filename → ./reports/<file>.")
def lint(paths: tuple[str, ...], level: str, exclude_globs: tuple[str, ...],
         no_gitignore: bool, fail_only: bool, strict: bool,
         fmt: str, output: str | None) -> None:
    """Source-level a11y lint for JSX / TSX / JS / HTML files.

    Pass one or more paths — files or directories. Directories are walked
    recursively (excluding node_modules, .next, dist, build, .git, etc.).

    Three-tier issue status:

      fail    AST confirmed a violation (e.g. <img> with no alt at all).
      caveat  AST sees the pattern but cannot statically confirm — typically
              dynamic values (`alt={var}`) or rules whose verdict requires
              runtime CSS / DOM. AI agents reading the report can decide
              whether to act.
      info    AST advisory only — pattern is borderline (e.g. alt="" might
              be correct for decorative images).

    Lint runs without LLM, browser, or network. Same rule_id space as the
    `scan` / `site` commands; share the same MODA codes across the pipeline.
    """
    from .lint.runner import expand_paths, lint_files
    resolved = expand_paths(paths, exclude_globs=exclude_globs,
                             respect_gitignore=not no_gitignore)
    if not resolved:
        click.echo("no source files found in the given paths", err=True)
        sys.exit(1)
    print(f"linting {len(resolved)} file(s)", file=sys.stderr)
    report = lint_files(resolved, level=Level[level])
    if fail_only:
        for fr in report.files:
            fr.issues = [i for i in fr.issues if i.status == "fail"]
    fmt = _resolve_fmt(fmt, output)
    if fmt == "md":
        text = _lint_to_markdown(report)
    else:
        text = json.dumps(_serialize_lint(report), ensure_ascii=False, indent=2)
    _write(text, output)
    if strict and report.summary.get("fail", 0) > 0:
        sys.exit(1)


def _lint_to_markdown(report) -> str:
    s = report.summary
    lines = [
        f"# a11y-moda lint",
        "",
        f"- files: **{s['files_scanned']}**",
        f"- fail: **{s['fail']}**, caveat: {s['caveat']}, info: {s['info']}",
        "",
    ]
    for fr in report.files:
        if not fr.issues:
            continue
        lines.append(f"## `{fr.path}`")
        lines.append("")
        for i in fr.issues:
            badge = {"fail": "🔴", "caveat": "🟡", "info": "🔵"}.get(i.status, "⚪")
            lines.append(f"- {badge} **L{i.line}:C{i.col}** `{i.rule_id}` — {i.message}")
        lines.append("")
    return "\n".join(lines)


@main.command()
@click.argument("url")
@click.option("--level", type=click.Choice(["A", "AA", "AAA"]), default="AA")
@click.option("--render/--no-render", default=False, help="Use headless Chromium for JS-rendered pages")
@click.option("--freego-compat", is_flag=True, default=False,
              help="Match the official MODA tool's reporting for these rule IDs "
                   "(CS2140401C/CS3140801C/CS3140802C) — useful when cross-checking output")
@click.option("--ignore", multiple=True, help="Rule IDs to skip (repeatable)")
@click.option("--freego-only", is_flag=True, default=False,
              help="Only run rules covered by the official MODA tool's machine checks "
                   "(skip extension E rules)")
@click.option("--no-extension", is_flag=True, default=False,
              help="Alias for --freego-only")
@click.option("--fail-only", is_flag=True, default=False, help="Show only fail issues")
@click.option("--allow-private-hosts", is_flag=True, default=False,
              help="Permit scanning localhost / RFC1918 / link-local URLs (intranet audits). "
                   "Off by default to block SSRF via redirects / sitemaps to internal endpoints.")
@click.option("--allow-file", is_flag=True, default=False,
              help="Permit `file://` URLs and accept filesystem paths "
                   "(./index.html, D:\\dist, /var/www/site) — used to audit local build output "
                   "without spinning up a dev server. Off by default so a redirect from a "
                   "public site can't trick the scanner into reading local files.")
@click.option("--probe-modals", is_flag=True, default=False,
              help="Click likely modal-trigger buttons (預約/contact/register …) to discover "
                   "forms inside dialogs. OFF by default — clicking on production sites can "
                   "trigger booking / billing / analytics. Destructive keywords (付款/delete/"
                   "unsubscribe …) are always skipped even when this is on.")
@click.option("--dark-mode", is_flag=True, default=False,
              help="Also scan in prefers-color-scheme=dark and merge findings. "
                   "Runs the scan TWICE (light then dark) — most contrast bugs in design "
                   "systems live only in the dark variant. Dark-only issues are tagged "
                   "[深色模式] in the merged report. Requires --render.")
@click.option("--strict-third-party", is_flag=True, default=False,
              help="Treat third-party resource violations (e.g. Google CSE CSS) as fail. "
                   "Default: downgrade to caveat with [third-party: <origin>] prefix, since "
                   "site author cannot fix external resources directly (WCAG 2.1 §5.4 "
                   "Partial Conformance route applies).")
@_llm_options
@click.option("--format", "fmt", type=click.Choice(["json", "md", "html"]), default="json")
@click.option("--output", "-o", type=click.Path(), default=None,
              help="If extension is .md/.html, format auto-detected")
def scan(url: str, level: str, render: bool, freego_compat: bool,
         ignore: tuple[str, ...], freego_only: bool, no_extension: bool,
         fail_only: bool, allow_private_hosts: bool, allow_file: bool,
         probe_modals: bool, dark_mode: bool,
         strict_third_party: bool,
         llm_base_url: str | None, llm_key: str | None, llm_model: str | None,
         llm_concurrency: int,
         fmt: str, output: str | None) -> None:
    """Scan a single URL."""
    if render:
        from .fetcher import ensure_playwright_or_die
        ensure_playwright_or_die("scan --render")
    if dark_mode and not render:
        click.echo("warning: --dark-mode has no effect without --render (static fetch can't emulate color scheme)", err=True)
    url = _resolve_url(url, allow_file=allow_file)
    _enforce_url_safety(url, allow_private=allow_private_hosts, allow_file=allow_file)
    sources = {"freego"} if (freego_only or no_extension) else None
    llm = _build_llm(llm_base_url, llm_key, llm_model)

    def _scan(scheme: str | None):
        return scan_page(url, level=Level[level], render=render,
                         freego_compat=freego_compat, ignore=ignore, sources=sources, llm=llm,
                         llm_workers=llm_concurrency, probe_modals=probe_modals,
                         strict_third_party=strict_third_party, color_scheme=scheme)

    if dark_mode and render:
        # Two passes — light first, dark second. Merged at PageReport level.
        from .scanner import _merge_dark_into_page
        click.echo("scanning in light mode (1/2)...", err=True)
        light_page = _scan(None)
        click.echo("scanning in dark mode (2/2)...", err=True)
        dark_page = _scan("dark")
        report = _merge_dark_into_page(light_page, dark_page)
    else:
        report = _scan("dark" if dark_mode else None)

    if fail_only:
        report.issues = [i for i in report.issues if i.status == "fail"]
    fmt = _resolve_fmt(fmt, output)
    if fmt == "json":
        text = json.dumps(_serialize_page(report), ensure_ascii=False, indent=2)
    elif fmt == "md":
        text = page_to_markdown(report)
    else:
        from .models import ScanReport as _SR
        wrap = _SR(pages=[report])
        text = scan_to_html(wrap, title=f"Scan: {url}")
    _write(text, output)


@main.command()
@click.argument("start_url")
@click.option("--level", type=click.Choice(["A", "AA", "AAA"]), default="AA")
@click.option("--render/--no-render", default=False)
@click.option("--freego-compat", is_flag=True, default=False)
@click.option("--ignore", multiple=True)
@click.option("--freego-only", is_flag=True, default=False,
              help="Only run rules covered by the official MODA tool's machine checks "
                   "(skip extension E rules)")
@click.option("--no-extension", is_flag=True, default=False, help="Alias for --freego-only")
@click.option("--fail-only", is_flag=True, default=False)
@click.option("--max-pages", type=int, default=30, help="Max pages to scan")
@click.option("--source", type=click.Choice(["sitemap", "crawl", "auto"]), default="auto",
              help="URL discovery: sitemap.xml, in-page crawl, or sitemap-then-crawl")
@click.option("--workers", type=int, default=4, help="Parallel workers for static scans")
@click.option("--delay", type=float, default=0.0, help="Sleep N seconds before each request (be polite)")
@click.option("--rps", type=float, default=0.0, help="Global cap: max requests per second (0 = unlimited)")
@click.option("--render-crawl", is_flag=True, default=False, help="Use Playwright in crawler too (catches JS-injected links)")
@click.option("--exclude-url", multiple=True, help="Exact URLs to skip (repeatable)")
@click.option("--exclude-folder", multiple=True, help="URL substrings to skip e.g. /admin (repeatable)")
@click.option("--max-time", type=float, default=0, help="Max scan duration in seconds (0 = unlimited)")
@click.option("--allow-private-hosts", is_flag=True, default=False,
              help="Permit scanning localhost / RFC1918 / link-local URLs (intranet audits). "
                   "Off by default to block SSRF via redirects / sitemaps to internal endpoints.")
@click.option("--allow-file", is_flag=True, default=False,
              help="Permit `file://` URLs and accept filesystem paths. For `site`, walks the "
                   "directory recursively for *.html files instead of crawling links / sitemap. "
                   "Used to audit local build output (Astro/Next export/Hugo/Eleventy dist).")
@click.option("--probe-modals", is_flag=True, default=False,
              help="Click likely modal-trigger buttons (預約/contact/register …) to discover "
                   "forms inside dialogs. OFF by default — clicking on production sites can "
                   "trigger booking / billing / analytics. Destructive keywords (付款/delete/"
                   "unsubscribe …) are always skipped even when this is on.")
@click.option("--dark-mode", is_flag=True, default=False,
              help="Also scan in prefers-color-scheme=dark and merge findings. "
                   "Runs the scan TWICE (light then dark) — most contrast bugs in design "
                   "systems live only in the dark variant. Dark-only issues are tagged "
                   "[深色模式] in the merged report. Requires --render.")
@click.option("--strict-third-party", is_flag=True, default=False,
              help="Treat third-party resource violations (e.g. Google CSE CSS) as fail. "
                   "Default: downgrade to caveat with [third-party: <origin>] prefix, since "
                   "site author cannot fix external resources directly (WCAG 2.1 §5.4 "
                   "Partial Conformance route applies).")
@_llm_options
@click.option("--group-by", type=click.Choice(["rule", "wcag", "url"]), default="rule",
              help="MD/JSON grouping (rule = most actionable; HTML always shows all 3 tabs)")
@click.option("--format", "fmt", type=click.Choice(["json", "md", "html"]), default="json")
@click.option("--output", "-o", type=click.Path(), default=None,
              help="If extension is .md/.html, format auto-detected")
def site(start_url: str, level: str, render: bool, freego_compat: bool,
         ignore: tuple[str, ...], freego_only: bool, no_extension: bool,
         fail_only: bool, max_pages: int,
         source: str, workers: int, delay: float, rps: float,
         render_crawl: bool, exclude_url: tuple[str, ...], exclude_folder: tuple[str, ...],
         max_time: float, allow_private_hosts: bool, allow_file: bool,
         probe_modals: bool, dark_mode: bool,
         strict_third_party: bool,
         llm_base_url: str | None, llm_key: str | None, llm_model: str | None,
         llm_concurrency: int,
         group_by: str, fmt: str, output: str | None) -> None:
    """Discover and scan a whole site."""
    if render or render_crawl:
        from .fetcher import ensure_playwright_or_die
        flag = "--render" if render and not render_crawl else (
            "--render-crawl" if render_crawl and not render else "--render / --render-crawl"
        )
        ensure_playwright_or_die(f"site {flag}")
    if dark_mode and not render:
        click.echo("warning: --dark-mode has no effect without --render (static fetch can't emulate color scheme)", err=True)
    start_url = _resolve_url(start_url, allow_file=allow_file)
    _enforce_url_safety(start_url, allow_private=allow_private_hosts, allow_file=allow_file)
    if start_url.startswith("file://"):
        # Filesystem walk — sitemap / crawl don't apply to local build output.
        from .crawler import discover_filesystem
        urls = discover_filesystem(start_url, max_pages=max_pages,
                                    exclude_urls=exclude_url,
                                    exclude_folders=exclude_folder)
    elif source == "sitemap":
        from .crawler import fetch_sitemap
        import asyncio
        urls = asyncio.run(fetch_sitemap(start_url))[:max_pages]
    elif source == "crawl":
        urls = crawl(start_url, max_pages=max_pages, render=render_crawl,
                     exclude_urls=exclude_url, exclude_folders=exclude_folder,
                     max_seconds=max_time)
    else:
        urls = discover(start_url, max_pages=max_pages, prefer_sitemap=True,
                        render=render_crawl, exclude_urls=exclude_url,
                        exclude_folders=exclude_folder, max_seconds=max_time)
    if not urls:
        urls = [start_url]
    print(f"discovered {len(urls)} URL(s)", file=sys.stderr)

    sources = {"freego"} if (freego_only or no_extension) else None
    llm = _build_llm(llm_base_url, llm_key, llm_model)
    def _site_scan(scheme: str | None):
        return scan_urls(urls, level=Level[level], render=render,
                         freego_compat=freego_compat, ignore=ignore,
                         workers=workers, progress=True, delay=delay, rps=rps,
                         sources=sources, llm=llm, llm_workers=llm_concurrency,
                         probe_modals=probe_modals,
                         strict_third_party=strict_third_party,
                         color_scheme=scheme)

    if dark_mode and render:
        from .scanner import merge_dark_into_report
        click.echo("scanning in light mode (1/2)...", err=True)
        light_report = _site_scan(None)
        click.echo("scanning in dark mode (2/2)...", err=True)
        dark_report = _site_scan("dark")
        scan_report = merge_dark_into_report(light_report, dark_report)
    else:
        scan_report = _site_scan("dark" if dark_mode else None)
    if llm:
        print(f"LLM stats: {llm.stats}", file=sys.stderr)
    if fail_only:
        for p in scan_report.pages:
            p.issues = [i for i in p.issues if i.status == "fail"]
    fmt = _resolve_fmt(fmt, output)
    if fmt == "json":
        text = json.dumps(_serialize_scan(scan_report), ensure_ascii=False, indent=2)
    elif fmt == "md":
        text = scan_to_markdown(scan_report, title=f"Site scan: {start_url}", group_by=group_by)
    else:
        text = scan_to_html(scan_report, title=f"Site scan: {start_url}")
    _write(text, output)


# ---------------------------------------------------------------------------
# `rules` subcommand group — query MODA accessibility rule knowledge.
# ---------------------------------------------------------------------------
#
# Lets AI agents (Cursor, Copilot, Aider, Claude Code, custom agents) query
# the rule registry without parsing scan/lint output. Two consumption modes:
#
#   1. Pre-write: agent about to write <button>, <form>, etc. queries
#      relevant rules first → writes accessible code from the start.
#   2. Post-edit: agent receives a lint issue with rule_id → queries
#      `rules show <id>` for full context, fix guidance, MODA mapping.
#
# Both scan + lint registries are unioned. A rule_id appearing in both gets
# `scope: ["scan", "lint"]`. `runtime_authoritative` reflects the lint side
# when present (since 0.2.1 only lint inspects this flag).

def _all_rules_metadata() -> list[dict]:
    """Union scan + lint rule registries, return list of metadata dicts.

    Each entry has 9 fields:
      rule_id, guideline, level (int), level_name, desc, source,
      runtime_authoritative, wcag_url, topic, scope (list of "scan" / "lint")
    """
    from .rules import all_rules
    from .lint.base import all_lint_rules

    out: dict[str, dict] = {}

    def _topic_from_module(mod_name: str) -> str:
        # a11y_moda.rules.codes.aria.AR2410300E → aria
        # a11y_moda.lint.codes.keyboard.GN1210100E → keyboard
        parts = mod_name.split(".")
        return parts[-2] if len(parts) >= 2 else "misc"

    def _wcag_url(guideline: str) -> str:
        # WAI Quickref anchors by SC number — works for all 2.1 SC. Avoids
        # the Understanding/<name> URL format which requires per-SC name
        # lookup we don't maintain.
        slug = guideline.replace(".", "-")
        return f"https://www.w3.org/WAI/WCAG21/quickref/#sc-{slug}"

    def _record(rule, scope: str) -> None:
        rid = rule.meta.rule_id
        topic = _topic_from_module(type(rule).__module__)
        runtime_auth = getattr(rule.meta, "runtime_authoritative", False)
        if rid in out:
            if scope not in out[rid]["scope"]:
                out[rid]["scope"].append(scope)
            if runtime_auth:
                out[rid]["runtime_authoritative"] = True
            return
        out[rid] = {
            "rule_id": rid,
            "guideline": rule.meta.guideline,
            "level": int(rule.meta.level),
            "level_name": rule.meta.level.name,
            "desc": rule.meta.desc,
            "source": rule.meta.source,
            "runtime_authoritative": runtime_auth,
            "wcag_url": _wcag_url(rule.meta.guideline),
            "topic": topic,
            "scope": [scope],
        }

    for r in all_rules():
        _record(r, "scan")
    for r in all_lint_rules():
        _record(r, "lint")

    return sorted(out.values(), key=lambda d: d["rule_id"])


# English element / concept → zh-TW substring(s) appearing in rule descriptions.
# Lets agents query with English (`button`, `form`, `image`) and find the
# Chinese-described rule. Keep tight — only common a11y-relevant elements.
_SEARCH_ALIASES: dict[str, tuple[str, ...]] = {
    "button": ("按鈕", "button", "btn"),
    "link": ("連結", "link", "a 元素", "<a"),
    "form": ("表單", "form"),
    "input": ("輸入", "input", "欄位"),
    "label": ("標籤", "label"),
    "image": ("圖片", "image", "img"),
    "img": ("圖片", "img"),
    "video": ("影片", "video"),
    "audio": ("音訊", "audio", "音檔"),
    "iframe": ("iframe", "內嵌"),
    "table": ("表格", "table"),
    "heading": ("標題", "heading", "h1", "h2", "h3"),
    "lang": ("語言", "lang"),
    "alt": ("替代文字", "alt"),
    "aria": ("aria", "role"),
    "role": ("role", "aria"),
    "focus": ("焦點", "focus"),
    "keyboard": ("鍵盤", "keyboard"),
    "color": ("色彩", "顏色", "對比"),
    "contrast": ("對比", "contrast"),
    # Corpus has no rule specifically for <dialog>/<modal>; nearest a11y
    # concepts are alert/status (aria-live) + focus management.
    "modal": ("alert", "aria-live", "焦點", "status"),
    "dialog": ("alert", "aria-live", "焦點", "status"),
    "navigation": ("導覽", "navigation", "nav"),
    "landmark": ("landmark", "地標", "main", "header", "footer"),
    "skip": ("略過", "skip"),
    "title": ("title", "標題"),
    "meta": ("meta", "metadata"),
}


def _filter_rules(rules: list[dict], *, level: str | None, topic: str | None,
                  source: str | None, scope: str | None,
                  search: str | None) -> list[dict]:
    out = rules
    if level:
        max_lv = {"A": 1, "AA": 2, "AAA": 3}[level]
        out = [r for r in out if r["level"] <= max_lv]
    if topic:
        out = [r for r in out if r["topic"] == topic]
    if source:
        out = [r for r in out if r["source"] == source]
    if scope:
        out = [r for r in out if scope in r["scope"]]
    if search:
        q = search.lower()
        # Expand English keyword to alias substrings if registered.
        terms = list(_SEARCH_ALIASES.get(q, (q,)))
        # Always include the raw query so partial / multi-word still matches.
        if q not in terms:
            terms.append(q)
        out = [r for r in out
               if any(t in r["rule_id"].lower()
                      or t in r["desc"].lower()
                      or t in r["guideline"]
                      or t in r["topic"]
                      for t in terms)]
    return out


def _rules_to_md(rules: list[dict], *, full: bool = False) -> str:
    """Markdown table for terminal-friendly output."""
    if not rules:
        return "_(no rules match)_"
    if full:
        # one section per rule
        chunks = []
        for r in rules:
            chunks.append(
                f"### `{r['rule_id']}` — {r['desc']}\n\n"
                f"- **WCAG SC**: {r['guideline']} ([Understanding]({r['wcag_url']}))\n"
                f"- **Level**: {r['level_name']}\n"
                f"- **Topic**: {r['topic']}\n"
                f"- **Source**: {r['source']}\n"
                f"- **Scope**: {', '.join(r['scope'])}\n"
                f"- **runtime_authoritative**: {r['runtime_authoritative']}\n"
            )
        return "\n".join(chunks)
    # compact table
    lines = ["| rule_id | WCAG | Level | Topic | Scope | Description |",
             "|---|---|---|---|---|---|"]
    for r in rules:
        scope_str = "+".join(r["scope"])
        lines.append(
            f"| `{r['rule_id']}` | {r['guideline']} | {r['level_name']} | "
            f"{r['topic']} | {scope_str} | {r['desc']} |"
        )
    return "\n".join(lines)


@main.group()
def rules() -> None:
    """Query MODA accessibility rule knowledge (no audit; just metadata).

    For AI agents writing accessible code: query rules BEFORE writing
    interactive elements, not just after lint reports an issue. See
    `examples/` for IDE integration patterns (Cursor, Copilot, Aider).
    """


@rules.command("list")
@click.option("--level", type=click.Choice(["A", "AA", "AAA"]), default=None,
              help="Max compliance level to include (A < AA < AAA). "
                   "Omit to list all levels.")
@click.option("--topic", default=None,
              help="Filter by topic directory under codes/ (e.g. forms, aria, "
                   "keyboard, images, headings, links, lang, meta, navigation, "
                   "media, focus, presentation, structure, tables, responsive).")
@click.option("--source", type=click.Choice(["freego", "extension"]), default=None,
              help="freego = Freego machine-checked rule (C suffix); "
                   "extension = E rule we automated.")
@click.option("--scope", type=click.Choice(["scan", "lint"]), default=None,
              help="Only rules implemented in this stage's runner.")
@click.option("--search", default=None,
              help="Substring match in rule_id / desc / guideline / topic.")
@click.option("--format", "fmt", type=click.Choice(["json", "md"]), default="md")
@click.option("--output", "-o", type=click.Path(), default=None)
def rules_list(level: str | None, topic: str | None, source: str | None,
               scope: str | None, search: str | None,
               fmt: str, output: str | None) -> None:
    """List rules matching filters. Default: all 129 rules in compact table."""
    rs = _filter_rules(_all_rules_metadata(), level=level, topic=topic,
                       source=source, scope=scope, search=search)
    if fmt == "json":
        text = json.dumps({"count": len(rs), "rules": rs},
                          ensure_ascii=False, indent=2)
    else:
        header = (f"# a11y-moda rules — {len(rs)} match\n\n"
                  f"_Filters: level={level} topic={topic} source={source} "
                  f"scope={scope} search={search!r}_\n\n")
        text = header + _rules_to_md(rs)
    _write(text, output)


@rules.command("show")
@click.argument("rule_id")
@click.option("--format", "fmt", type=click.Choice(["json", "md"]), default="md")
@click.option("--output", "-o", type=click.Path(), default=None)
def rules_show(rule_id: str, fmt: str, output: str | None) -> None:
    """Show detailed metadata for one rule_id."""
    rs = [r for r in _all_rules_metadata() if r["rule_id"] == rule_id]
    if not rs:
        click.echo(f"ERROR: no rule with id {rule_id!r}. "
                   "Try `a11y-moda rules list` to browse all.", err=True)
        sys.exit(2)
    if fmt == "json":
        text = json.dumps(rs[0], ensure_ascii=False, indent=2)
    else:
        text = _rules_to_md(rs, full=True)
    _write(text, output)


@rules.command("search")
@click.argument("query")
@click.option("--format", "fmt", type=click.Choice(["json", "md"]), default="md")
@click.option("--output", "-o", type=click.Path(), default=None)
def rules_search(query: str, fmt: str, output: str | None) -> None:
    """Substring search across rule_id, description, WCAG SC, topic.

    Examples:
      a11y-moda rules search button
      a11y-moda rules search 1.1.1
      a11y-moda rules search alt
    """
    rs = _filter_rules(_all_rules_metadata(), level=None, topic=None,
                       source=None, scope=None, search=query)
    if fmt == "json":
        text = json.dumps({"query": query, "count": len(rs), "rules": rs},
                          ensure_ascii=False, indent=2)
    else:
        header = f"# a11y-moda rules — search {query!r} ({len(rs)} match)\n\n"
        text = header + _rules_to_md(rs)
    _write(text, output)


# Top-level alias for `rules show <RULE_ID>` — short and direct.
@main.command("explain")
@click.argument("rule_id")
@click.option("--format", "fmt", type=click.Choice(["json", "md"]), default="md")
@click.option("--output", "-o", type=click.Path(), default=None)
@click.pass_context
def explain(ctx: click.Context, rule_id: str, fmt: str, output: str | None) -> None:
    """Alias for `rules show <RULE_ID>` — short form."""
    ctx.invoke(rules_show, rule_id=rule_id, fmt=fmt, output=output)


# ---------------------------------------------------------------------------
# `init` subcommand — install bundled IDE / agent integration template.
# ---------------------------------------------------------------------------
#
# Eliminates the GitHub-clone-and-copy step. Examples are bundled in the
# package (since v0.3.1) via package-data. `init` reads them via
# importlib.resources and writes / prints them to the user's target.
#
# Design choices:
#   - No interactive prompt mode. AI agents (Claude Code, Cursor, Copilot
#     Bash) lack stdin and would hang. `--list` + clear ERROR-with-options
#     gives the same UX without the hang risk.
#   - --force required to overwrite existing files. Avoids destroying a
#     user's hand-crafted .cursorrules / SKILL.md.
#   - --print sends content to stdout instead of writing — useful for CI
#     preview, piping to other commands, or pasting into agent prompts.
#   - --dest overrides the default install path per IDE.
#   - `agent` IDE has no default file path — always prints to stdout
#     unless --dest given. The expected workflow is to paste it into the
#     agent's system prompt setting (which is GUI / config-specific).

# IDE name → (bundled subpath, default install dest, kind)
# kind: "dir" copies a whole subtree; "file" copies one file; "stdout"
# always prints to stdout (no default file destination).
_INIT_TARGETS: dict[str, tuple[str, str | None, str]] = {
    "claude-code": ("claude-code-skill",
                    "~/.claude/skills/a11y-moda",
                    "dir"),
    "cursor":      ("cursor/.cursorrules",
                    "./.cursorrules",
                    "file"),
    "copilot":     ("copilot/.github/copilot-instructions.md",
                    "./.github/copilot-instructions.md",
                    "file"),
    "aider":       ("aider/.aider.conf.yml",
                    "./.aider.conf.yml",
                    "file"),
    "agent":       ("generic-agent/AGENT.md",
                    None,
                    "stdout"),
}

# Per-IDE next-step hints printed after successful install.
_INIT_NEXT_STEPS: dict[str, str] = {
    "claude-code": (
        "  - Reload Claude Code (the skill registers on next start)\n"
        "  - Test: type /a11y-moda or say \"check a11y\""
    ),
    "cursor": (
        "  - Reload Cursor (the rules apply to next chat / Composer / inline-edit)\n"
        "  - Test: ask Cursor \"what MODA rules apply to <button>?\""
    ),
    "copilot": (
        "  - Open GitHub Copilot Chat in this repo\n"
        "  - Instructions auto-apply to next message"
    ),
    "aider": (
        "  - Run aider in this repo — config auto-loads\n"
        "  - The lint-cmd hook will run a11y-moda lint after each edit"
    ),
    "agent": (
        "  - Paste the printed content into your agent's system prompt /\n"
        "    instructions setting (location varies by agent)"
    ),
}


def _list_init_targets_text() -> str:
    """Compact textual list of install targets for --list / ERROR output."""
    lines = []
    width = max(len(k) for k in _INIT_TARGETS)
    for ide, (_, dest, kind) in _INIT_TARGETS.items():
        if kind == "stdout":
            shown = "(prints to stdout — paste into agent system prompt)"
        else:
            shown = dest
        lines.append(f"  {ide:<{width}}   {shown}")
    return "\n".join(lines)


def _resolve_init_dest(ide: str, dest_override: str | None) -> Path:
    """Expand ~, make Path. dest_override wins over per-IDE default."""
    _, default_dest, kind = _INIT_TARGETS[ide]
    if dest_override:
        return Path(os.path.expanduser(dest_override))
    if default_dest is None:
        # `agent` IDE — no default; caller should have used --print or --dest.
        raise click.UsageError(
            f"`init {ide}` has no default file destination. "
            f"Use --print to send to stdout, or --dest <path> to choose a file."
        )
    return Path(os.path.expanduser(default_dest))


def _read_bundled(subpath: str) -> bytes:
    """Read a bundled example by subpath under a11y_moda/_examples/."""
    import importlib.resources as ir
    parts = subpath.split("/")
    res = ir.files("a11y_moda._examples")
    for p in parts:
        res = res / p
    return res.read_bytes()


def _iter_bundled_dir(subpath: str):
    """Yield (relative_filename, bytes) for every file under a bundled dir."""
    import importlib.resources as ir
    root = ir.files("a11y_moda._examples")
    for p in subpath.split("/"):
        root = root / p
    for entry in root.iterdir():
        if entry.is_file():
            yield entry.name, entry.read_bytes()
        elif entry.is_dir():
            # Recurse one level (current bundle only has 1-deep subdirs)
            for sub in entry.iterdir():
                if sub.is_file():
                    yield f"{entry.name}/{sub.name}", sub.read_bytes()


@main.command("init")
@click.argument("ide", required=False)
@click.option("--list", "list_only", is_flag=True,
              help="List all available IDE / agent integrations and exit.")
@click.option("--dest", type=click.Path(), default=None,
              help="Override the default install path.")
@click.option("--print", "print_only", is_flag=True,
              help="Print content to stdout instead of writing to disk.")
@click.option("--force", is_flag=True,
              help="Overwrite existing destination files.")
def init(ide: str | None, list_only: bool, dest: str | None,
         print_only: bool, force: bool) -> None:
    """Install a11y-moda integration template for an IDE / agent.

    Available IDEs: claude-code, cursor, copilot, aider, agent
    Run `a11y-moda init --list` for full path details.

    Examples:
      a11y-moda init claude-code
      a11y-moda init cursor
      a11y-moda init aider --force
      a11y-moda init agent --print > my-prompt.md
      a11y-moda init copilot --dest /custom/path/instructions.md
    """
    if list_only:
        click.echo("Available a11y-moda integrations:\n")
        click.echo(_list_init_targets_text())
        click.echo("\nUse: a11y-moda init <ide>")
        return

    if not ide:
        click.echo("ERROR: missing IDE name.\n", err=True)
        click.echo("Available:", err=True)
        click.echo(_list_init_targets_text(), err=True)
        click.echo("\nRun: a11y-moda init <ide>           e.g. a11y-moda init cursor",
                   err=True)
        click.echo("List: a11y-moda init --list", err=True)
        sys.exit(2)

    if ide not in _INIT_TARGETS:
        click.echo(f"ERROR: unknown IDE {ide!r}.\n", err=True)
        click.echo("Available:", err=True)
        click.echo(_list_init_targets_text(), err=True)
        sys.exit(2)

    bundled_subpath, _, kind = _INIT_TARGETS[ide]

    # --print: always go stdout regardless of kind/dest
    if print_only:
        if kind == "dir":
            # Print a separator-marked concatenation of all files
            for fname, content in _iter_bundled_dir(bundled_subpath):
                click.echo(f"# ===== {fname} =====")
                click.echo(content.decode("utf-8", errors="replace"))
                click.echo()
            return
        content = _read_bundled(bundled_subpath)
        click.echo(content.decode("utf-8", errors="replace"))
        return

    # `agent` IDE without --print and without --dest → tell user
    if kind == "stdout" and dest is None:
        click.echo(
            "ERROR: `init agent` has no default file destination.\n"
            "Choose one:\n"
            "  a11y-moda init agent --print              # print to stdout\n"
            "  a11y-moda init agent --print > AGENT.md   # save to file\n"
            "  a11y-moda init agent --dest AGENT.md      # write to specific path",
            err=True,
        )
        sys.exit(2)

    target = _resolve_init_dest(ide, dest)

    # `agent` (kind=stdout) with --dest given → treat as file write.
    if kind == "stdout":
        kind = "file"

    if kind == "file":
        if target.exists() and not force:
            click.echo(
                f"ERROR: {target} already exists.\n"
                f"Use --force to overwrite, or --print to preview.",
                err=True,
            )
            sys.exit(2)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(_read_bundled(bundled_subpath))
        line_count = target.read_text(encoding="utf-8").count("\n")
        click.echo(f"Installing a11y-moda {ide} integration...\n")
        click.echo(f"  source: bundled {bundled_subpath}")
        click.echo(f"  dest:   {target}")
        click.echo(f"\n[OK] Wrote {line_count} lines to {target}")
        click.echo(f"\nNext:\n{_INIT_NEXT_STEPS[ide]}")
        return

    if kind == "dir":
        target.mkdir(parents=True, exist_ok=True)
        wrote_count = 0
        skipped = []
        for rel_name, content in _iter_bundled_dir(bundled_subpath):
            dest_file = target / rel_name
            if dest_file.exists() and not force:
                skipped.append(rel_name)
                continue
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            dest_file.write_bytes(content)
            wrote_count += 1
        click.echo(f"Installing a11y-moda {ide} skill...\n")
        click.echo(f"  source: bundled {bundled_subpath}/")
        click.echo(f"  dest:   {target}/")
        click.echo(f"\n[OK] Copied {wrote_count} file(s)")
        if skipped:
            click.echo(f"     Skipped (use --force to overwrite): {', '.join(skipped)}")
        click.echo(f"\nNext:\n{_INIT_NEXT_STEPS[ide]}")
        return


def _resolve_fmt(fmt: str, output: str | None) -> str:
    """Output extension overrides --format when explicit (.md/.html)."""
    if output:
        ext = Path(output).suffix.lower()
        if ext == ".md":
            return "md"
        if ext in (".html", ".htm"):
            return "html"
        if ext == ".json":
            return "json"
    return fmt


def _write(text: str, output: str | None) -> None:
    if output:
        path = Path(output)
        # Bare filename (no slash, not absolute) → drop into ./reports/ to keep cwd clean.
        if not path.is_absolute() and len(path.parts) == 1:
            path = Path("reports") / path
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"wrote {path}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()

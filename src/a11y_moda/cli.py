"""Command-line entry."""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

import click

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


def _enforce_url_safety(url: str, *, allow_private: bool) -> None:
    """Block accidental scans of localhost / metadata / file:// URLs."""
    if allow_private:
        os.environ["A11Y_ALLOW_PRIVATE_HOSTS"] = "1"
    if not is_safe_http_url(url, allow_private=allow_private):
        raise click.UsageError(
            f"refused unsafe URL: {url!r}. Only public http(s) URLs allowed by default. "
            f"Pass --allow-private-hosts to scan localhost / RFC1918 / link-local intranets."
        )


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
@click.option("--env-file", type=click.Path(exists=True, dir_okay=False), default=None,
              help="Path to a .env file (highest precedence; must exist). Otherwise "
                   "loads ./.env and ~/.config/a11y-moda/.env when present. Existing "
                   "process env vars are never overridden.")
@click.pass_context
def main(ctx: click.Context, env_file: str | None) -> None:
    """MODA accessibility scanner."""
    _load_env_files(env_file)


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
@click.option("--probe-modals", is_flag=True, default=False,
              help="Click likely modal-trigger buttons (預約/contact/register …) to discover "
                   "forms inside dialogs. OFF by default — clicking on production sites can "
                   "trigger booking / billing / analytics. Destructive keywords (付款/delete/"
                   "unsubscribe …) are always skipped even when this is on.")
@_llm_options
@click.option("--format", "fmt", type=click.Choice(["json", "md", "html"]), default="json")
@click.option("--output", "-o", type=click.Path(), default=None,
              help="If extension is .md/.html, format auto-detected")
def scan(url: str, level: str, render: bool, freego_compat: bool,
         ignore: tuple[str, ...], freego_only: bool, no_extension: bool,
         fail_only: bool, allow_private_hosts: bool, probe_modals: bool,
         llm_base_url: str | None, llm_key: str | None, llm_model: str | None,
         llm_concurrency: int,
         fmt: str, output: str | None) -> None:
    """Scan a single URL."""
    _enforce_url_safety(url, allow_private=allow_private_hosts)
    sources = {"freego"} if (freego_only or no_extension) else None
    llm = _build_llm(llm_base_url, llm_key, llm_model)
    report = scan_page(url, level=Level[level], render=render,
                       freego_compat=freego_compat, ignore=ignore, sources=sources, llm=llm,
                       llm_workers=llm_concurrency, probe_modals=probe_modals)
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
@click.option("--probe-modals", is_flag=True, default=False,
              help="Click likely modal-trigger buttons (預約/contact/register …) to discover "
                   "forms inside dialogs. OFF by default — clicking on production sites can "
                   "trigger booking / billing / analytics. Destructive keywords (付款/delete/"
                   "unsubscribe …) are always skipped even when this is on.")
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
         max_time: float, allow_private_hosts: bool, probe_modals: bool,
         llm_base_url: str | None, llm_key: str | None, llm_model: str | None,
         llm_concurrency: int,
         group_by: str, fmt: str, output: str | None) -> None:
    """Discover and scan a whole site."""
    _enforce_url_safety(start_url, allow_private=allow_private_hosts)
    if source == "sitemap":
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
    scan_report = scan_urls(urls, level=Level[level], render=render,
                            freego_compat=freego_compat, ignore=ignore,
                            workers=workers, progress=True, delay=delay, rps=rps,
                            sources=sources, llm=llm, llm_workers=llm_concurrency,
                            probe_modals=probe_modals)
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

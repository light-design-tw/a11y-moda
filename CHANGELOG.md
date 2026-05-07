# Changelog

All notable changes to `a11y-moda` are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [SemVer](https://semver.org/) — schema may shift before 1.0.

## [Unreleased]

## [0.1.0] — 2026-05-07

First public release on PyPI.

### Added
- `a11y-moda scan <URL>` — single-page WCAG audit
- `a11y-moda site <URL>` — full-site crawl (sitemap-first, BFS fallback) + audit
- WCAG A / AA / AAA level filtering via `--level`
- Static (httpx + BeautifulSoup) and rendered (Playwright / headless Chromium) scan modes
- Output formats: JSON / Markdown / HTML (HTML auto-renders rule / WCAG / URL views)
- 129 registered rules covering Freego machine-checked C rules + extension E rules
- 20 / 20 MODA AAA self-evaluation questions automated (18 hard, 2 with informative caveat)
- OpenAI-compatible LLM client (works with OpenAI, Anthropic, OpenRouter, Ollama, vLLM, LM Studio, llama.cpp server)
- Vision (VLM) support for screenshot-based rules; auto-probes endpoint capability
- LLM result caching at `~/.cache/a11y-moda/llm/`
- Auto-detect third-party resource violations → downgrade to caveat with `[third-party: <origin>]` prefix; opt out via `--strict-third-party`
- `--freego-compat` to align reporting format with the official tool
- `--ignore RULE_ID`, `--workers`, `--rps`, `--render-crawl`, `--probe-modals` flags
- zh-TW report output (LLM responses auto-prefixed with Traditional Chinese instructions; `to_traditional()` post-processes any simplified Chinese)

### Notes
- Pre-1.0: output schema may change. Pin `==0.1.x` in CI.
- `pip install` does not download Chromium — run `playwright install chromium` before using `--render`.

[Unreleased]: https://github.com/light-design-tw/a11y-moda/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/light-design-tw/a11y-moda/releases/tag/v0.1.0

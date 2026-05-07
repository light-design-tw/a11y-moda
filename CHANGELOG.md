# Changelog

All notable changes to `a11y-moda` are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [SemVer](https://semver.org/) — schema may shift before 1.0.

## [Unreleased]

## [0.1.2] — 2026-05-08

Polish batch — quality-of-life fixes that should have been in 0.1.0.

### Added
- `a11y-moda --version` / `-V` now prints the installed version (was a
  `click.UsageError: No such option` before).
- README badges for PyPI version, supported Python versions, and license.
- README pointer to `docs/AI_INTEGRATION.md` and the bundled Claude Code
  skill — AI workflow features were undiscoverable from the main README.

### Fixed
- zh-TW console output on Windows. The default code page (cp950 on
  Traditional Chinese systems, cp1252 on English) mojibakes the rule
  output. CLI now reconfigures `sys.stdout` / `sys.stderr` to UTF-8 on
  `win32`. POSIX systems are unaffected.

[0.1.2]: https://github.com/light-design-tw/a11y-moda/releases/tag/v0.1.2

## [0.1.1] — 2026-05-08

First dogfood patch — caught while running the v0.1.0 CLI against a real
zh-TW Next.js site whose dark/light theme toggle was an icon-only button.

### Fixed
- `GN2141103E` (contrast toggle control) now recognises zh-TW theme
  vocabulary (`深色模式`, `淺色模式`, `主題切換`, `切換主題`) plus
  `light.?mode` / `theme.?toggle`. Previously the regex only matched
  `dark.?mode` / `高對比` / `對比切換` / `無障礙模式`, so common Taiwanese
  phrasing was missed.
- `GN2141103E` now also scans `aria-label` / `title` / `alt` on
  `<button>` / `<a>` / `<input>` elements, not just `soup.get_text()`.
  Icon-only toggles (SVG inside the button, label provided via
  `aria-label`) used to evade detection because their visible text was
  empty.

[0.1.1]: https://github.com/light-design-tw/a11y-moda/releases/tag/v0.1.1

## [0.1.0a1] — 2026-05-07

Dry-run alpha to validate the PyPI publish pipeline (OIDC trusted publisher,
GitHub environment gating, CHANGELOG extraction). Same code as the planned
0.1.0; no functional differences. Pre-releases are excluded from
`pip install a11y-moda` by default — pass `--pre` to install this alpha.

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

[Unreleased]: https://github.com/light-design-tw/a11y-moda/compare/v0.1.2...HEAD
[0.1.0]: https://github.com/light-design-tw/a11y-moda/releases/tag/v0.1.0
[0.1.0a1]: https://github.com/light-design-tw/a11y-moda/releases/tag/v0.1.0a1

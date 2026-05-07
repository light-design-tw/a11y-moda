# Changelog

All notable changes to `a11y-moda` are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [SemVer](https://semver.org/) — schema may shift before 1.0.

## [Unreleased]

## [0.2.0] — 2026-05-08

Two big additions, both targeting the **write/build** stage of the
workflow (T1–T6) where rendered-DOM scan can't reach: source-level
`lint` and `file://` build-output audit.

### Added — `lint` command (source-level static analysis)

- New `a11y-moda lint <paths...>` subcommand. Walks JSX/TSX/TS/JS/HTML
  source via tree-sitter, runs deterministic AST checks. **No
  LLM/VLM** — fast, offline, repeatable. Complements rendered-DOM
  `scan` (different signal, same rule_id namespace).
- **50 rules ported** from the scan rule set (out of ~77 lintable),
  spanning: image-alt family, page metadata, forms structure,
  ARIA roles/labels, navigation/landmark, link text, headings,
  tables, lang attributes, deprecated tags, keyboard handlers,
  inline style, RTL/bidi, viewport, media controls, dialog/carousel
  patterns, focus visibility.
- Three-tier status — `fail` (deterministic violation), `caveat`
  (likely violation but needs human/runtime check; e.g. wrapper
  components with `{...spread}`), `info` (style/preference). Lets
  AI agents decide which to act on; `--fail-only` filters to fail
  tier; `--strict` exits non-zero on any issue.
- `--exclude PATTERN` (repeatable, gitignore-style globs); built-in
  excludes for `node_modules` / `.next` / `dist` / `build` / `.git`
  / `.cache` etc. `.gitignore` respected by default; opt out with
  `--no-gitignore`.
- Output formats: `--format json|md`, `-o FILE` honored same as
  `scan`/`site`.
- Wrapper-component heuristic — capital-first JSX tags
  (`<Button>`, `<Dialog>`) downgrade keyboard/structure violations
  to `caveat`, since shadcn/Radix/HeadlessUI commonly delegate
  accessibility to the underlying primitive.
- Decorative-image heuristic — `<img alt="">` paired with explicit
  `role="presentation"` / `role="none"` / `aria-hidden="true"` is
  recognised as intentional and skipped silently.
- New runtime dependencies: `tree-sitter` (>=0.23,<0.26),
  `tree-sitter-typescript`, `tree-sitter-html`, `pathspec`.

### Added — `file://` build-output audit

- `--allow-file` flag on both `scan` and `site`. Permits `file://`
  URLs and accepts plain filesystem paths (`./index.html`,
  `D:\dist\`, `/var/www/site/`). Off by default so a redirect from
  a public site can't trick the scanner into reading local files.
- `A11Y_ALLOW_FILE=1` environment variable equivalent.
- Filesystem-walk discovery for `site` mode when target is a
  `file://` URL or directory. Recursively finds all `*.html` /
  `*.htm` files, sorts deterministically, respects `--max-pages` /
  `--exclude-folder`. Sitemap and BFS link-crawl don't apply
  (build output has no sitemap; following `<a href>` from local
  files is not what users expect).
- `crawler.discover_filesystem(start_url, ...)` public function.
- Relative paths (`./out/`, `dist/index.html`) and Windows
  backslash paths (`D:\dist\index.html`) auto-resolve to absolute
  `file://` URIs when `--allow-file` is on.
- `fetcher._read_local_file()` for the static path; `fetch_with_page`
  (Playwright) handles `file://` natively, no extra code needed.

### Notes

- `--render` works with `file://` — Playwright loads the file URL
  natively; all probes (contrast, focus, tab walk, form simulation,
  screenshots) operate on the rendered local DOM.
- `_security.is_safe_http_url()` gains an `allow_file` parameter
  (defaults to env var). Existing callers pass through unchanged.
- **Workflow positioning** — `lint` covers T1–T3 (write/edit/save),
  `file://` scan covers T4–T6 (build/preview/pre-deploy), HTTP scan
  covers T7+ (staging/prod). All share the MODA rule_id namespace.
  Complements rather than replaces `eslint-plugin-jsx-a11y` (no
  MODA rule_id mapping) and DopplerKuo `a11y-tw-audit-skill` (LLM
  at write-time).
- Lint rule files live at `src/a11y_moda/lint/codes/<topic>/<RULE_ID>.py`
  with auto-discovery (one file per rule_id, mirrors `rules/codes/`
  layout).

[0.2.0]: https://github.com/light-design-tw/a11y-moda/releases/tag/v0.2.0

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

[Unreleased]: https://github.com/light-design-tw/a11y-moda/compare/v0.2.0...HEAD
[0.1.0]: https://github.com/light-design-tw/a11y-moda/releases/tag/v0.1.0
[0.1.0a1]: https://github.com/light-design-tw/a11y-moda/releases/tag/v0.1.0a1

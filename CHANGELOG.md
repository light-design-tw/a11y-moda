# Changelog

All notable changes to `a11y-moda` are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [SemVer](https://semver.org/) — schema may shift before 1.0.

## [Unreleased]

## [0.3.1] — 2026-05-08

UX completion patch for v0.3.0's knowledge-service positioning. Removes
the "go clone GitHub and copy this file" friction for IDE / agent
integration. Also revamps top-level `--help` to surface all current
capabilities (audit / knowledge / integration) at a glance.

### Added

- **`a11y-moda init <ide>` subcommand** — one-line install of bundled
  IDE / agent integration templates. No more "open GitHub → find
  examples/ → copy → paste".
  - `init claude-code` → `~/.claude/skills/a11y-moda/` (full skill dir
    with SKILL.md + REFERENCE.md)
  - `init cursor` → `./.cursorrules`
  - `init copilot` → `./.github/copilot-instructions.md`
  - `init aider` → `./.aider.conf.yml`
  - `init agent` → stdout (or `--dest` for file write); platform-agnostic
    AGENT.md for any LLM agent (Cline, Continue, RooCode, custom)
  - `init --list` — list all IDEs + their default install paths
  - `init <ide> --print` — preview content (don't write); useful for CI
    / piping to other commands / pasting into agent prompts
  - `init <ide> --dest <path>` — override default install path
  - `init <ide> --force` — overwrite existing destination files
- **Bundled examples in package** — `_examples/` directory now ships
  with the wheel via `[tool.setuptools.package-data]`. End users no
  longer need to clone the repo.
- **Comprehensive `--help`** — top-level help text now lists all
  capabilities organised into AUDIT / KNOWLEDGE / INTEGRATION /
  INSTALL sections. Single screen overview for new users.

### Changed

- **`examples/` → `src/a11y_moda/_examples/`** — moved into the package
  so it ships with `pip install a11y-moda`. GitHub browse paths updated
  in README, README.en, docs/AI_INTEGRATION.md. Old `examples/` URLs in
  CHANGELOG entries 0.3.0 left as historical record.
- **`docs/AI_INTEGRATION.md` §11** — recommends `a11y-moda init <ide>`
  as the primary install path; manual copy from GitHub demoted to
  fallback.
- **`SKILL.md` README** — install instructions simplified from
  "git clone + curl" to "`a11y-moda init claude-code`".

### Notes

- **Why no interactive prompt** — `a11y-moda init` (no IDE arg) prints
  ERROR + clear options list rather than a `click.prompt` loop. AI
  agents (Claude Code, Cursor, Copilot, Aider) shell out without TTY
  stdin and would hang on interactive prompts. Single-line
  `init <ide>` works the same for AI and human users.
- **Why `--force` required for overwrite** — `.cursorrules`,
  `SKILL.md`, etc. are commonly hand-edited. Silent overwrite would
  destroy user work. Default behavior: refuse with helpful ERROR;
  `--force` opt-in to replace.
- **Why `init agent` has no default file path** — the AGENT.md content
  is meant for the agent's *system prompt* setting (location varies
  by agent: Cline = workspace settings, Continue = config.json,
  custom = code). Default = stdout for piping; `--dest` for file.
- **AI install flow now possible**: user says "set up a11y-moda for
  Cursor", agent runs `pip install a11y-moda && a11y-moda init cursor`,
  done. No human navigation through GitHub UI.

[0.3.1]: https://github.com/light-design-tw/a11y-moda/releases/tag/v0.3.1

## [0.3.0] — 2026-05-08

**BREAKING**: Playwright is no longer installed by default. The default
install (`pip install a11y-moda`) now ships only `lint` + `rules`
subcommand dependencies (~30MB). To use `scan` / `site` / `--render` /
`--render-crawl` / `--probe-modals`, install the `[scan]` extra:

```
pip install 'a11y-moda[scan]'
playwright install chromium
```

Existing users who upgrade and then run `--render` will see a clear
install message printed to stderr; the CLI does not auto-install.

### Reframing — knowledge service

a11y-moda repositions from "audit CLI" to **"audit CLI + queryable MODA
rule knowledge service"**. The new `rules` subcommand exposes the
internal rule registry as a queryable API for AI agents (any IDE /
agent that can call CLI tools), so the agent can lookup MODA rules
**before** writing accessibility-sensitive code instead of only after
lint complains. Cross-platform by design — works with Cursor, GitHub
Copilot, Aider, Claude Code, Cline, Continue, custom agents.

### Added

- **`a11y-moda rules` subcommand group** — query MODA rule metadata.
  Three subcommands: `list`, `show`, `search`. JSON / Markdown output.
  Filters: `--level`, `--topic`, `--source` (freego/extension),
  `--scope` (scan/lint), `--search`. English keyword aliases for
  search (`button` / `form` / `image` / `dialog` / etc. map to zh-TW
  desc substrings).
- **`a11y-moda explain <RULE_ID>`** — short alias for `rules show`.
- **9-field rule metadata** — `rule_id`, `guideline`, `level`,
  `level_name`, `desc`, `source`, `runtime_authoritative`, `wcag_url`
  (WAI Quickref anchor), `topic` (codes/ subdir), `scope` (list of
  stages: scan/lint).
- **`examples/cursor/.cursorrules`** — Cursor integration.
- **`examples/copilot/.github/copilot-instructions.md`** — GitHub
  Copilot Chat integration.
- **`examples/aider/.aider.conf.yml`** — Aider integration with
  `lint-cmd:` hook.
- **`examples/generic-agent/AGENT.md`** — platform-agnostic
  instructions for any LLM agent (Cline, Continue, RooCode, custom).
- **SKILL.md** — `argument-hint`, knowledge-query section, MODA 編碼
  速查 (HM/GN/CS/AR/FA/SC + C/E suffix decoder).
- Workflow positioning expanded from T1–T7 to T0–T7 (T0 = pre-write
  rule lookup).

### Changed (BREAKING)

- `pyproject.toml` `dependencies` no longer includes `playwright`.
  Moved to `optional-dependencies.scan` and `optional-dependencies.all`.
- CLI `scan` / `site` early-exit with friendly install message when
  `--render` / `--render-crawl` selected and Playwright not importable.
  `lint` and `rules` unaffected.

### Notes

- **Why no MCP server yet**: `rules` subcommand + system-prompt
  examples (Layer 2 of cross-IDE strategy) ship first to validate the
  "edit-time query" workflow with the lowest-risk approach. MCP server
  (Layer 1, native tool integration) deferred to v0.4.0 pending real
  usage signal.
- **Why no auto-install**: industry consensus (pytest plugins, ruff,
  black, even Playwright itself) is to print a clear install command
  and let the user run it. Auto-install causes permission, network,
  and reproducibility issues. AI agents that read stderr will run the
  printed command on the user's behalf.
- **Knowledge query is proactive, not reactive**: the design intent
  is for agents to query rules BEFORE generating JSX, not just after
  lint reports an issue. Reactive lookup also works (`explain
  <RULE_ID>` after seeing a `fail`), but the bigger UX win is writing
  compliant code from the start.

[0.3.0]: https://github.com/light-design-tw/a11y-moda/releases/tag/v0.3.0

## [0.2.1] — 2026-05-08

Patch — sharper definition of `lint` `fail` vs `caveat`. Triggered by
real-world dogfood: a `<div onClick={onClose} role="dialog">` modal
backdrop fired `fail` for `GN1210100E` ("missing keyboard handler"),
but the keyboard close path lived in a sibling `<button aria-label="關閉">`
plus a top-of-component `useHotkeys("esc", onClose)` — both invisible
to single-file AST. Marking such cases `fail` is wrong: AST literally
cannot prove the violation, only suggest review.

### Changed
- `RuleMeta` gains `runtime_authoritative: bool = False`. Rules whose
  verdict requires rendered DOM, computed CSS, focus traversal, or
  cross-file event wiring (which AST cannot reach) set this to `True`.
- `lint` runner now downgrades `fail` → `caveat` for any rule with
  `runtime_authoritative=True`, appending an explanatory note to the
  message: 「lint 無法跨檔/runtime 確認，請人工或 a11y-moda scan 驗證」.
  `scan` is unaffected — it has Playwright + computed style and can
  emit `fail` authoritatively for the same rules.
- Marked `runtime_authoritative=True`:
  - `GN1210100E` — onClick / mouse handler missing keyboard equivalent
    (cross-file `useHotkeys` / sibling button invisible to AST)
  - `FA2141104E` — `<style>` outline:none without `:focus` rule
    (external CSS files invisible to lint)
- Other lint rules already emit `info` or `caveat` and are unaffected.

### Notes
- This is a **definition fix**, not a tuning knob. `lint`'s `fail`
  status now means "AST proved a violation"; ambiguous cases are
  `caveat` regardless of runtime severity. Users who want hard
  keyboard gating in CI should run `a11y-moda scan` (which has the
  evidence to fail).
- Per-project `--ignore` / config file is **not** added in this patch
  (YAGNI). Will revisit if real demand surfaces.
- Dogfood after patch: light-design AAA, 135 files, **0 fail / 31 caveat
  / 0 info** (real `<div onClick>` accordions in Footer + Faq were fixed
  to `<button type="button">` between releases; Modal backdrop cleanly
  downgrades to caveat with the new note).

[0.2.1]: https://github.com/light-design-tw/a11y-moda/releases/tag/v0.2.1

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

[Unreleased]: https://github.com/light-design-tw/a11y-moda/compare/v0.3.1...HEAD
[0.1.0]: https://github.com/light-design-tw/a11y-moda/releases/tag/v0.1.0
[0.1.0a1]: https://github.com/light-design-tw/a11y-moda/releases/tag/v0.1.0a1

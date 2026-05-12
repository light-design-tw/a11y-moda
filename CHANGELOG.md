# Changelog

All notable changes to `a11y-moda` are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [SemVer](https://semver.org/) — schema may shift before 1.0.

## [Unreleased]

## [0.4.2] — 2026-05-12

Probe correctness patch — fixes a pseudo-class misuse in
`tools/dialog_probe.py` and `tools/tab_walk.py` that caused
`CS2240700E` (and indirectly any Tab-walk-derived focus-visibility
check) to false-positive on every site that correctly set a
`:focus-visible` outline.

Found via dogfood after fixing light-design.com.tw's actual focus
issues — site author's `<main tabIndex={-1}>` + global outline rules
verified working in DevTools (outlineStyle=solid width=3px under
focus), but `a11y-moda` v0.4.1 still reported the rule as fail.

### Fixed

- **`tools/dialog_probe.py` `_SKIP_TARGET_FOCUS_JS`** — removed
  `getComputedStyle(target, ':focus-visible')`. The second argument
  to `getComputedStyle` accepts only **pseudo-elements** (`::before`,
  `::after`, `::marker`); passing a **pseudo-class** like
  `:focus-visible` is invalid and Chromium silently falls back to
  the non-focus computed style (Firefox returns null). When the
  target is currently focused (skip link Enter has moved focus to it
  via `tabindex="-1"`), reading the regular computed style already
  includes the `:focus`/`:focus-visible` cascade — that's the
  correct read.
- **`tools/tab_walk.py` `COLLECT_FOCUS_JS`** — same fix. Each Tab
  press makes the new element `document.activeElement`; reading
  regular computed style already reflects the focused-state cascade.
- **`CS2240700E` correctness restored** — sites with valid
  `:focus-visible` outline + `tabindex="-1"` skip targets now
  correctly pass instead of false-firing.

### Notes

- **Why this slipped past v0.4.0/0.4.1 dogfood** — light-design.com.tw
  had no skip-link target focus indicator in those versions, so the
  rule was firing on a real underlying issue and passing the eye
  test. Bug surfaced only after the site author shipped the actual
  fix. Lesson: probes need fixture-style positive controls in
  addition to dogfood, not just sites that currently violate.
- **Per-page nuance on light-design (post-0.4.2)** — homepage and
  pricing now PASS `CS2240700E` (probe correctly reads the new
  outline cascade); about-us / contact / works still report fail.
  This is a probe heuristic limitation, not a recurrence of the
  pseudo-class bug — `dialog_probe` runs after `carousel_probe`'s
  4.5s observation, and the page state (scroll position, focus
  location) sometimes prevents the Tab-from-body walk from reaching
  the skip link in 5 presses. Investigating in 0.4.3 (likely:
  scroll-to-top + focus-body before each probe).
- **Acknowledgement** — bug diagnosis comes from the
  light-design.com.tw author who verified outline was applied via
  Playwright at the same time `a11y-moda` was still reporting fail.
  Real-world dogfood found a class of bug that synthetic fixtures
  would have missed.

[0.4.2]: https://github.com/light-design-tw/a11y-moda/releases/tag/v0.4.2

## [0.4.1] — 2026-05-12

Patch fixing two real-audit gaps that v0.4.0 dogfood scan revealed:

1. `CS2240700E` (skip-link target focus) was emitting nothing on
   `light-design.com.tw` even though the MODA AAA report flagged
   exactly this pattern. Root cause: the `dialog_probe` correctly
   pressed Enter on the skip link, but browsers do not move keyboard
   focus on `<a href="#x">` activation unless the target carries
   `tabindex="-1"`. The probe's `opened` flag stayed False. The rule
   only fired when `opened=True AND visible_focus=False`, so the
   "Enter pressed but focus didn't move" case (the most common
   violation) was silently passed.

2. `--dark-mode` was a one-or-the-other switch — it scanned ONLY in
   dark mode, replacing the default light scan instead of adding to
   it. Most contrast bugs only appear in one variant; the other has
   to be re-scanned manually. Now `--dark-mode` runs both passes and
   merges, with dark-only issues prefixed `[深色模式]` so the merged
   report makes attribution obvious.

Coverage delta on the 9-finding MODA AAA audit (light-design.com.tw,
2026-05-12 dogfood): 5/9 stable HITs in v0.4.0 → 5/9 stable HITs in
v0.4.1, but the *quality* improved — `CS2240700E` is now a true
match and `GN2140300E` aligns to the MODA-flagged dark-mode contrast
segment instead of an unrelated light-mode segment. `GN1220200E`
(carousel pause) remains intermittent due to Wix Reviews lazy-mount
timing — pre-existing flake, not regressed by this release.

### Added

- **`DialogProbeResult.skip_link_found`** — distinguishes "probe
  found a skip link and pressed Enter" from "probe found nothing".
  Required so `CS2240700E` can fire on the "Enter pressed but focus
  didn't move" case without false-firing on pages that simply lack a
  skip link (the latter is `GN1240100E`'s domain).
- **`scanner.merge_dark_into_report` + `_merge_dark_into_page`** —
  combines a dark-mode `ScanReport` / `PageReport` into the
  corresponding light report. Dark-only issues (after exact
  `(rule_id, snippet, message)` dedup) get the `[深色模式]` prefix.

### Changed

- **`CS2240700E`** — now emits two distinct fail messages:
  - `Enter 後焦點未跳至目標元素` when the skip link was activated but
    `document.activeElement` did not become the target (most common
    violation — target lacks `tabindex="-1"`).
  - `焦點已跳至目標但目標元素無可見焦點指示` when focus did move but
    the target's `:focus-visible` style is empty (existing case,
    refined wording).
- **`--dark-mode` flag semantics** — was "scan only in dark"; is now
  "scan in light AND dark, merge results". Behavioral change for
  anyone scripting against the flag, but more useful in practice
  (dual coverage in one command). Help text updated.

### Notes

- **Flake disclosure** — `GN1220200E` (carousel pause) detection
  depends on Wix Reviews lazy-mounting before the 4.5s observation
  window expires. On `light-design.com.tw` this hits ~50% of runs.
  Not regressed by 0.4.1; will be addressed in a follow-up via
  pre-probe scroll + extended observation when no motion is detected
  in the first window.
- **Why 0.4.1 not 0.4.0.1** — `--dark-mode` semantic change is a
  user-visible behavior shift. SemVer-strict would call this minor,
  but pre-1.0 we keep it as patch since the flag was new in 0.4.0
  and the new behavior is what users actually wanted.
- **No README rewrite needed** — `--dark-mode` description in README
  already said "Run twice (light + dark) for full coverage" — the
  CLI now matches what the README promised.

[0.4.1]: https://github.com/light-design-tw/a11y-moda/releases/tag/v0.4.1

## [0.4.0] — 2026-05-12

Real-audit-driven release — first MODA AAA inspection report on
`light-design.com.tw` (sent 2026-04-30, returned 2026-05-12) flagged
9 findings that v0.3.4 missed. This release closes those gaps.

Two new rules + three new Playwright probes (focus-trap, skip-link,
carousel auto-rotation) + dark-mode emulation + one logic reversal.
No external dependency added — all gains come from `[scan]`'s existing
Playwright. LLM/VLM still not required for any of the new checks.

### Added

- **`GN1240300E`** (`rules/codes/aria/`, level A, WCAG 2.4.3) — flags
  suspected tab-pattern groups (3+ short-label siblings with
  `tab/filter/category` class hint or `aria-selected`/`data-tab`
  attributes) that lack `role=tablist`/`role=tab`. Surfaced as
  `caveat` because pure HTML can't confirm UX intent.
- **`GN1410200E`** (`rules/codes/aria/`, level A, WCAG 4.1.2) —
  cross-checks the same suspected tab pattern as GN1240300E from the
  ARIA name/role/value angle. Both rules can fire on the same group
  (complementary, not duplicate).
- **`tools/dialog_probe.py`** — Playwright probe: finds hamburger /
  modal triggers (`aria-haspopup`, `aria-expanded`, hamburger icon
  heuristic, hint-text), clicks each, walks Tab N times inside the
  opened container, reports whether focus stayed trapped or escaped.
  Also detects skip-link → target focus visibility. Result list
  exposed as `ctx.dialog_probes` (`DialogProbeResult` dataclass).
- **`tools/carousel_probe.py`** — Playwright probe: snapshots
  `transform` / `scrollLeft` of likely carousel containers, waits
  ~4.5s, snapshots again. DOM motion without user interaction = auto-
  rotating. Catches Wix / Webflow / hand-rolled carousels that don't
  use library class names (`swiper` / `slick` / `glide`). Result list
  exposed as `ctx.carousel_probes` (`CarouselProbeResult` dataclass).
- **`--dark-mode` flag** on `scan` and `site` — sets Playwright
  `color_scheme="dark"` so dark-themed sites render in their dark
  variant. Most contrast bugs in design systems live in the dark
  variant; default light scans miss them. Run twice (light + dark)
  for full coverage. Requires `--render`; warns if used without it.

### Changed

- **`CS1140101E`** (1.4.1) — now also fails when `dialog_probe`
  reports a menu/modal opened but focus escaped (in addition to the
  existing static `:focus` CSS check).
- **`GN1240301E`** (2.4.3) — now fails when any `dialog_probe` reports
  trigger opened a container but next Tab walked outside (focus-trap
  missing). Existing "more than half tab stops out of viewport" check
  retained.
- **`CS2240700E`** (2.4.7) — now fails when `dialog_probe` reports a
  skip-link target receives focus but has no visible focus indicator
  at the destination. Existing per-Tab-stop `:focus-visible` audit
  retained.
- **`HM1240404E`** (2.4.4) — **logic direction reversed**. Previously
  only checked links *with* a title and asked the LLM whether the
  title was redundant. Now also detects the inverse case (the one
  MODA flagged): repeated visible link text pointing at multiple
  different `href`s with no disambiguating `title` / `aria-label`.
  This direction is structural — runs without `--llm-*`. Original
  LLM-judged direction kept as a secondary check.
- **`GN1240500E`** (2.4.5) — no longer early-exits on the presence of
  `<nav>` alone. MODA 2.4.5 requires multiple ways to find content,
  so the rule now requires at least one of: programmatic nav, search,
  or sitemap-page link. Surfaces a `caveat` when only one mechanism
  exists and the missing one is sitemap (the case MODA flagged on
  light-design.com.tw — has `<nav>`, no `/sitemap` page).
- **`GN1220200E`** (2.2.2) — adds runtime auto-rotation detection via
  `carousel_probe`. Fails when DOM motion is observed without a
  pause/stop control nearby. Existing static class-name heuristic
  retained as `info`-level fallback for static-only scans.

### Notes

- **Why this release exists** — see
  `marketing/ithome-2026/aaa-audit-feedback-evidence.md` (parent
  monorepo). The first AAA inspection report became the test case for
  why automated tooling alone is insufficient and how to close the
  most common gaps. Five root-cause categories identified: (1) focus-
  trap unimplemented, (2) dark mode unscanned, (3) LLM rule logic
  reversed, (4) heuristic class allowlist too narrow, (5) rule scope
  misunderstood + 2 missing rules.
- **No new external dependencies** — all gains from `[scan]`'s
  existing Playwright. Standard install (`pip install a11y-moda`)
  remains ~30MB.
- **No VLM required** — every new check is pure Playwright + computed
  CSS + structural analysis. Existing LLM rules unchanged. Vision
  models not added to any code path.
- **Probe ordering** — in shared-page scans the order is now
  `contrast → tab_walk → carousel → dialog → form_probe`. Carousel
  needs ~4.5s of pristine page state to detect auto-rotation; dialog
  and form probes mutate state and run last.
- **Coverage delta on light-design.com.tw audit** — 6 of 9 findings
  now detectable automatically; remaining 3 (granular focus-trap
  details that depend on container detection accuracy) emit
  `caveat`-level prompts. Full re-scan after this release will
  confirm the precise coverage rate.

[0.4.0]: https://github.com/light-design-tw/a11y-moda/releases/tag/v0.4.0

## [0.3.4] — 2026-05-09

Documentation patch — sync `README.md` + `README.en.md` to reflect
features shipped in 0.2.0 / 0.2.1 / 0.3.0 / 0.3.1 / 0.3.2 that were
documented in CHANGELOG but never propagated to README. PyPI's package
page renders README, so three releases of new functionality were
invisible to anyone landing on https://pypi.org/project/a11y-moda/ —
they would still see the pre-0.2.0 "scan / site only" framing.

No code change. PyPI wheel is bit-for-bit equivalent to 0.3.3 except
for the README rendered on the package page.

### Changed (docs)

- **`README.md`** — restructured around the three-layer mental model
  (`lint` write-time / `rules` knowledge service / `scan` runtime).
  Adds dedicated sections for each command. Adds "lint vs scan"
  decision table. Splits install into standard (~30MB) and `[scan]`
  extra (~290MB) with the v0.3.0 BREAKING change called out at the
  top of Install. Verbose flag tables and the AAA mechanism breakdown
  collapsed into `<details>` so above-the-fold stays scannable. TOC
  added.
- **`README.en.md`** — mirror of the zh-TW restructure. Same sections
  in English, no `<details>` collapse (English README is shorter
  overall and serves as a pointer to the zh-TW for full detail).
- **Tagline** — both READMEs updated from "scan / site CLI" framing
  to "lint + scan + rule lookup" to match the v0.3.0 knowledge-service
  reframing.

### Notes

- **Why this took until 0.3.4** — diagnosed during a PyPI page review.
  Root cause: no release SOP enforced README sync alongside CHANGELOG
  bumps. Fixed in `freego_cli/CLAUDE.md` (parent monorepo doc) under
  the new "發版檢查清單 (release SOP)" section, and in this project's
  contributor memory as `feedback_release_readme_sync`.
- **Why a patch (not minor)** — the underlying CLI surface, rule set,
  and behaviour are unchanged from 0.3.3. Only the rendered package
  page on PyPI changes. SemVer-wise this is the smallest version bump
  that triggers a PyPI republish.

[0.3.4]: https://github.com/light-design-tw/a11y-moda/releases/tag/v0.3.4

## [0.3.3] — 2026-05-08

Engineering scaffolding patch — adds the `tests/` directory the
project shipped without through 0.1.0–0.3.2. No runtime / CLI / rule
behaviour changes. The package on PyPI is bit-for-bit equivalent
except for `tests/` (which is repo-only, not packaged).

Until this version every refactor relied on dogfood (manually scanning
real sites) to catch regressions. Now there is a CI gate.

### Added

- **`tests/test_smoke.py`** — 15 invariants covering CLI surface,
  bundled package-data, JSON contract, and prior-version regressions:
  - `--version` / top-level `--help` lists all subcommands
    (`lint` / `scan` / `site` / `rules` / `init` / `explain`)
  - `init claude-code|cursor|aider|copilot|agent` writes the right
    files to the right paths — including the `.aider.conf.yml` /
    `.cursorrules` dotfiles that v0.3.1 nearly missed bundling
  - `lint` emits parseable JSON with the documented `files` /
    `summary` shape; `HM1110100C` fires on `<img>` without `alt`
  - `lint` `runtime_authoritative` downgrade still active —
    `<div onClick>` triggers `GN1210100E` as `caveat` not `fail`
    (regression guard for v0.2.1)
  - `rules show` / `rules search` / `explain` return JSON with the
    documented 9-field schema; `explain` is byte-identical to
    `rules show`
- **`tests/test_lint_golden.py`** — snapshot-diff lint output against
  two frozen fixtures (`violations.tsx` + `page.html`). Catches
  refactor regressions in `rules/_lib/` helpers, tree-sitter grammar
  bumps, and rule auto-discovery import-depth typos. Snapshots store
  `(rule_id, status, line, col)` tuples — message text and absolute
  paths excluded as locale/machine-dependent.
- **`tests/regen_snapshots.py`** — single command to regenerate
  snapshots after intentional rule-logic changes. The diff between
  before/after `expected.json` becomes the changelog entry for the
  rule change.
- **`tests/README.md`** — when-snapshot-fails decision tree, fixture
  design rules, how to add a new fixture.
- **`[project.optional-dependencies] dev = ["pytest>=8,<10"]`** — test
  runner only; runtime install path unchanged.
- **`[tool.pytest.ini_options]`** — `testpaths = ["tests"]`,
  `addopts = "-ra --strict-markers"`.

### Changed

- **`.github/workflows/release.yml`** — replaced the inline 8-line
  smoke shell block with `pip install dist/*.whl && pip install pytest
  && pytest tests/`. The wheel — not an editable install — is what
  gets tested, so packaging regressions (missing package-data, broken
  entry points) fail CI before PyPI publish.

### Notes

- **Why no per-rule unit tests** — 143 brittle fixtures, 0 external
  contributors, would couple test files to MODA spec rewording. Tier
  2 golden-snapshot covers the same ground at 1/70th the maintenance
  cost. Documented in `tests/README.md`.
- **Why no scan / Playwright tests** — Chromium output drifts across
  versions, fixture maintenance hostile to CI runners. `scan` is
  already exercised continuously by dogfood (light-design.com.tw).
- **Why no LLM-rule (E rules) snapshot** — non-deterministic, would
  measure the mock instead of the rule.

## [0.3.2] — 2026-05-08

Description-only patch — no code change. Rewrites the bundled Claude
Code skill `description` field for higher trigger accuracy in
real-invocation conditions. Validated by N=3 × 30-prompt benchmark
using `claude -p` cold-context invocation against a real installed
skill in `~/.claude/skills/a11y-moda/`.

### Changed

- **Claude Code skill `description` rewritten** —
  `src/a11y_moda/_examples/claude-code-skill/SKILL.md` frontmatter.
  Existing installs upgrade by re-running `a11y-moda init claude-code
  --force`. Skill body (sections 1-12, REFERENCE.md) unchanged.

### Benchmark (real `claude -p`, n=3 × 30 prompts = 90 runs)

| Tier                       | v0.3.1 stock | v0.3.2 rewrite | Δ   |
|----------------------------|--------------|----------------|-----|
| 1 — must trigger (10)      | 6/10 (60%)   | 9/10 (93%)     | +3  |
| 2 — should trigger (10)    | 0/10 (0%)    | 8/10 (77%)     | +8  |
| 3 — must NOT trigger (10)  | 10/10 (0% FP)| 10/10 (0% FP)  | 0   |
| **Total**                  | **16/30**    | **27/30**      | **+11** |

90% pass rate. Zero false-positive regression.

### Why

v0.3.1 description listed trigger phrases but covered no implicit a11y
pain (keyboard 不到 / contrast / dialog ESC) and did not address
Claude's bias to (a) answer rule-content questions from training
memory or (b) bypass the skill and invoke `a11y-moda` directly via
Bash when the user names the CLI.

v0.3.2 rewrite addresses both:

- Explicit anti-pattern: "Do NOT answer from memory or run a11y-moda
  directly via Bash"
- Six numbered invoke clauses covering rule_id (with prefix pattern),
  CLI mention by name, a11y pain phrases, MODA / WCAG asks, pre-write
  element list, and vague target phrasings
- "Claude does not know MODA rule content, must look up" forces
  invocation on rule_id queries that previously bypassed (e.g.
  `HM1110100C 怎麼修?`)

### Notes

- Three remaining benchmark misses (`Tier 1 #4`, `Tier 2 #11 #19`)
  are structural: Claude has a strong direct-answer bias for
  design-feedback phrasings ("設計師說背景跟字太接近") and UX-pattern
  questions framed as general best practice. Adding more keywords
  beyond the v0.3.2 rewrite was estimated to break Tier 3's perfect
  no-false-positive score with diminishing returns. 90% / 0 FP is the
  ship threshold.
- Methodology and raw data live in the contributor scratch dir
  (`.scratch/`, gitignored): `eval_set.json` (30 prompts),
  `run_trigger_eval_win.py` (Windows-friendly streaming-event
  detection runner), and per-version raw JSON results.
- Benchmark was performed on `claude-opus-4-7[1m]`; trigger behavior
  may vary on other models. Real-conversation triggering tends to be
  higher than cold `claude -p` because conversation context primes
  skill-relevance scoring. Treat the 93% / 77% as a conservative
  floor.

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

[Unreleased]: https://github.com/light-design-tw/a11y-moda/compare/v0.4.2...HEAD
[0.3.4]: https://github.com/light-design-tw/a11y-moda/releases/tag/v0.3.4
[0.3.3]: https://github.com/light-design-tw/a11y-moda/releases/tag/v0.3.3
[0.3.2]: https://github.com/light-design-tw/a11y-moda/releases/tag/v0.3.2
[0.1.0]: https://github.com/light-design-tw/a11y-moda/releases/tag/v0.1.0
[0.1.0a1]: https://github.com/light-design-tw/a11y-moda/releases/tag/v0.1.0a1

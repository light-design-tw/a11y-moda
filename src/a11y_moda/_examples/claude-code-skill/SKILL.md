---
name: a11y-moda
description: Taiwan MODA accessibility — audit + rule knowledge (WCAG A/AA/AAA, zh-TW, 129 MODA rules). Do NOT answer from memory or run a11y-moda directly via Bash; invoke this skill when user (1) mentions any MODA rule_id like HM1110100C, GN1210100E, CS3140801C, AR2410301E (prefix HM/GN/CS/AR/FA/SC + digits + optional C/E suffix) — Claude does not know MODA rule content, must look up; (2) mentions a11y-moda CLI by name (lint, scan, site, rules, explain); (3) describes a11y pain — keyboard 不到 / Tab 鍵按不到 / 鍵盤無法操作 / screen reader 讀不到 / 對比不足 / color contrast / focus trap / ARIA missing / modal dialog ESC 關不掉 / Lighthouse a11y 分數低; (4) asks about MODA 標章, AAA 自評, 無障礙檢查, WCAG check, 政府網站無障礙, WCAG SC 對應規則; (5) about to write <button>/<a>/<form>/<input>/<img>/<dialog>/<table>/role=*/aria-* — call rules search BEFORE generating code; (6) says vague "確認無障礙" / "掃 a11y" / "audit accessibility" / "check a11y" with any URL or path — ask once if target unclear, then invoke.
argument-hint: "[query | <RULE_ID> | <URL> | <path>]"
allowed-tools:
  - Bash
  - Read
  - Glob
  - Edit
---

# a11y-moda — MODA WCAG Audit + Knowledge Skill

Two roles:

1. **Knowledge service** — query `a11y-moda rules` for MODA rule
   metadata BEFORE writing a11y-sensitive code. Proactive, no audit.
2. **Audit** — run `a11y-moda lint` (source) / `scan` (page) / `site`
   (whole site) to find violations in existing code.

The same `rule_id` namespace (HM/GN/CS/AR/FA/SC) spans both roles.

**For edge cases not covered here, Read `REFERENCE.md` in this skill directory.**

---

## 1. Pre-flight

Verify install:

```bash
command -v a11y-moda
```

If missing, tell user (don't try to install for them):

```
a11y-moda not installed. Install:
    pip install a11y-moda                # lint + rules subcommand only (~30MB)
    pip install 'a11y-moda[scan]'        # add browser-based scan/site
    playwright install chromium          # required for --render
```

Since v0.3.0, Playwright is an **optional** extra. Lint + rules
subcommand work with the lightweight install. Don't push users to
install `[scan]` unless they're asking for `scan` / `site` / `--render`.

---

## 2. Determine scope

| User says | Scope |
|---|---|
| "What MODA rules apply to `<button>`?" / "show HM1110100C" / "AAA rules for forms" / "WCAG 1.1.1 對應" | `rules` (§2a — knowledge query) |
| About to write a11y-sensitive JSX/HTML element | `rules` first (proactive lookup) → write code |
| "lint my source" / "check my JSX" / "before commit" / "while I'm coding" | `lint` (§2b) |
| One URL / one page / `/path` | `scan` (§2b) |
| "Whole site" / "every page" / "MODA 標章" | `site` (§2b) |
| Ambiguous, source repo present, no live URL given | Default `lint` first (fast feedback) |
| Ambiguous, URL or path given | Default `scan`; offer to escalate to `site` after results |

### 2a. Rules / knowledge query (since 0.3.0)

Two ways to use:

**Pre-write proactive** — before generating any of these JSX/HTML
elements, query MODA rules first to write compliant code from the start:

```
<button>, <a href|onClick>, <form>, <input>, <textarea>, <select>, <label>,
<img>, <video>, <audio>, <iframe>, <picture>, <source>,
<table> (data tables), <dialog>, <details>, <summary>,
<svg> (interactive only),
ANY element with role=*, aria-*, tabindex
```

Trigger: when about to write code matching above. Run:

```bash
a11y-moda rules search <element-keyword> --format json
# English aliases work: button, form, image, dialog, table, focus, aria...
```

**Reactive lookup** — user asks about a rule_id or WCAG SC:

```bash
a11y-moda rules show HM1110100C --format json
a11y-moda explain HM1110100C --format json    # short alias

a11y-moda rules search 1.1.1 --format json    # by WCAG SC
a11y-moda rules list --topic forms --level AA --format json
```

JSON includes: `rule_id`, `guideline`, `level`, `level_name`, `desc`,
`source` (freego/extension), `runtime_authoritative`, `wcag_url`,
`topic`, `scope` (scan/lint).

**MODA 編碼速查** — let LLM infer rule_id from element type:

```
HM = HTML / 內容結構       e.g. HM1110100C = SC 1.1.1 第 100 條 (img alt)
GN = 一般 / Gateway        e.g. GN1210100E = SC 2.1.1 (keyboard equiv)
CS = CSS / 樣式            e.g. CS1110113E (decorative img via CSS)
AR = ARIA                   e.g. AR2410300E (status / aria-live)
FA = Focus / Form A         e.g. FA2240701E (outline:none + :focus 替代)
SC = Success Criterion 級   一般少用，主要在 docs

C suffix = Freego 機器規則 / E suffix = extension 人工判斷
```

LLM 知道用戶寫 `<img>` → 推 `HM111` 開頭 → 跑 `a11y-moda rules search image --format json` 取確切細節。

### 2b. Lint scope (since 0.2.0)

`lint` is **source-level static analysis** — tree-sitter AST over JSX/TSX/JS/HTML. No browser, no LLM, no network. Fast (sub-second on typical components). Use when:

- User just edited / saved a JSX/TSX/HTML file
- User wants pre-commit / pre-build feedback
- Live URL not available yet
- CI gating before deploy

`lint` shares the **same `rule_id` namespace** as `scan` / `site` — issues from `lint` reference the same MODA codes.

```bash
a11y-moda lint <path-or-file> [--level AA|AAA] [--exclude '**/*.test.*'] [--strict]
```

`lint` skips: `--render`, `--allow-private-hosts`, `--probe-modals`, `--llm-*`, `--rps`, `--workers`, `--max-pages`, `--render-crawl`. None apply to AST analysis.

---

## 3. Detect environment

```bash
ls next.config.* vite.config.* astro.config.* nuxt.config.* svelte.config.* 2>/dev/null
```

Match → **SPA** → plan `--render` (and `--render-crawl` for `site`).

If no framework config but `package.json` lists `react` / `vue` / `svelte` / `next` / `vite` / `astro` → also SPA.

If pure static HTML / backend-rendered (Django / Rails / Flask / .html) → no `--render`.

For local URLs, check the dev server is actually running. **Validate `<PORT>` is digits-only before substitution** (it comes from a package.json scripts heuristic — don't trust it):

```bash
# <PORT> must match [0-9]+ — refuse and re-ask if it doesn't
curl -sS -o /dev/null -w "%{http_code}\n" "http://localhost:<PORT>/" 2>/dev/null
```

`Connection refused` → tell user to start the dev server first.

---

## 4. Pick flags (decision table)

Apply each row independently.

| Condition | Flag |
|---|---|
| SPA detected | `--render` (+ `--render-crawl` for `site`) |
| Local URL (localhost / 127.0.0.1 / RFC1918) | `--allow-private-hosts` |
| Target is a filesystem path or `file://` URL (build output, no dev server) | `--allow-file` (+ `--render` to actually render the file) |
| User mentions "AAA" / "AAA 自評" | `--level AAA` |
| User mentions "A only" | `--level A` |
| Default level | `--level AA` (MODA 標章 baseline) |
| User wants only actionable | `--fail-only` |
| Cross-checking with official Freego | `--freego-compat` |
| Skip E rules (machine-only) | `--freego-only` |
| Production scan, be polite | `--rps 1 --delay 0.5` |
| Site mode page cap (default 30) | `--max-pages N` |

### When to use `--allow-file`

User signals: "scan my build output", "audit dist/", "掃 build 結果", "static export", "no dev server", or pastes a path like `./dist/`, `D:\out\index.html`, `out/`.

`--allow-file` accepts:
- Plain paths: `./dist/`, `D:\out\index.html`, `/var/www/site/`
- `file://` URIs: `file:///D:/dist/index.html`

For `site` mode with a path/file://, the CLI walks the directory for `*.html` files (no sitemap, no link crawl) — that's the right behavior for SSG output. Always pair with `--render` if the build output is hydrated SPA (Next export, etc).

**NEVER** add `--probe-modals` unless URL is dev/staging AND user explicitly asks. On production it can trigger booking / billing / analytics events.

LLM flags (`--llm-*`): see §11 — default = don't add.

---

## 5. Output

Always `--format json`. Save to hidden subdir to keep user's repo clean.

**Security**: invoke `a11y-moda` directly from the Bash tool. **Never** build a command string and `eval` it — URL / rule_id / flag values can contain shell metacharacters (`; & | $() \``), which `eval` would execute. Always quote variable expansions (`"$VAR"`).

```bash
mkdir -p .a11y-moda/reports
TS=$(date +%Y%m%d-%H%M)
OUT=".a11y-moda/reports/${TS}-<scope>.json"

# Direct invocation. Quote URL and OUT. Pass flags as separate args, not as
# one concatenated string.
a11y-moda <scan|site> "<URL>" --level <LEVEL> <other flag args> \
  --format json -o "$OUT"
```

After running, persist the **parameters** (not an eval-able command) for §9 re-verify. Use literal lines, one key per line:

```bash
{
  echo "SCOPE=<scan|site>"
  echo "URL=<URL>"
  echo "LEVEL=<LEVEL>"
  echo "FLAGS=<other flag args, space-separated>"
  echo "TS=$TS"
} > .a11y-moda/last-run.txt
```

`<scope>` = `scan` or `site`. `<timestamp>` resolves to e.g. `20260507-1430`.

### Input validation (when filling `<...>` placeholders)

Before substituting any value into a Bash command, validate it matches the expected pattern. If validation fails, surface the value to the user and ask, do not invoke.

| Placeholder | Allowed pattern | Source |
|---|---|---|
| `<URL>` | starts with `http://`, `https://`, `file://`, OR a path under cwd / a known absolute prefix when `--allow-file` is on; no shell metacharacters | user input |
| `<scope>` | exactly `scan` or `site` | your own decision (§2) |
| `<LEVEL>` | exactly `A`, `AA`, or `AAA` | §3 |
| `<PORT>` (in dev server probe) | `[0-9]+` only | package.json scripts heuristic |
| `<RULE_ID>` (for `--ignore`) | `[A-Z]{2}[0-9]+[CE]?` | user mention |
| `<other flag args>` | only flags from §4 decision table | your own decision |
| Filesystem path | no `..` traversal escaping cwd, no shell metacharacters; for `--allow-file` path inputs, prefer absolute paths or paths under cwd | user input |

Reject anything that doesn't match. Don't try to "sanitize" — refuse and re-ask.

---

**On first scan**, add `.a11y-moda/` to `.gitignore` if it exists and the entry is missing:

```bash
[ -f .gitignore ] && grep -q '^\.a11y-moda/' .gitignore || echo '.a11y-moda/' >> .gitignore
```

(This is a literal string, no variable expansion — safe.)

Mention this once: "Added `.a11y-moda/` to `.gitignore` so scan reports stay out of commits."

---

## 6. Run

Print the exact command before running so user can copy-replay:

```
Running:
    a11y-moda scan http://localhost:3000/about \
      --level AA --render --allow-private-hosts \
      --format json -o .a11y-moda/reports/20260507-1430-scan.json
```

Use Bash tool. Tell user the expected duration if non-trivial:
- SPA single page: ~10-30 seconds
- Site mode + `--render`: serial Chromium, 30 pages ≈ 5-10 minutes

If errors → see `REFERENCE.md` §2 for error → action mapping.

---

## 7. Parse + triage

JSON shape (full schema in `docs/AI_INTEGRATION.md` §5):

```
scan: {url, status_code, fetch_error, issues: [...], summary: {fail, info, caveat}}
site: {site_summary, by_rule: {<rule_id>: {...}}, pages: [...]}

issue: {rule_id, guideline, level (1=A 2=AA 3=AAA), desc, message, snippet, status}
```

### Status triage (CRITICAL)

| Status | Action |
|---|---|
| `fail` | Surface; suggest fix |
| `caveat` / `needs_human` | Surface as "needs review"; **do NOT auto-suggest fixes** |
| `info` | Mention only if user asks |
| `pass` / `not_applicable` | Don't surface |

### Third-party caveat (special case)

If `message` starts with `[third-party: <origin>] `:
- Violation lives in code from `<origin>` (e.g. `googleapis.com`)
- User cannot fix in their codebase
- Correct advice: "Declare in MODA 申請備註欄 (WCAG 2.1 §5.4 Partial Conformance)"
- Group separately from code-fix items (see §8)

### LLM-unavailable caveats (filter out)

Caveats whose `message` contains `LLM unavailable` are the default behavior, NOT errors. Hide them from the main caveat list. Collapse into a single line:

> ℹ️ 額外 N 條規則因無 LLM 端點而未評估 (此為預設行為)。

Don't enumerate by `rule_id`. Don't suggest setting up an LLM. (See §11.)

---

## 8. Present (zh-TW Markdown template)

```markdown
## a11y-moda 掃描結果

**範圍**: <scan / site, N pages> · **等級**: <A/AA/AAA> · **時間**: <ISO8601>

| Status | Count |
|---|---|
| 🔴 fail (需修) | N |
| 🟡 caveat (需人工確認) | N |
| 🔵 third-party (需備註) | N |

### 🔴 必修 (fail)

按 WCAG 等級 + 影響頁面數排序，列前 5-10 條。

#### 1. `<RULE_ID>` (WCAG <SC>) · Level <A/AA/AAA>

<message>

範例：
\```html
<snippet>
\```

**建議修法**: <一句話建議>

(site mode：影響頁面 N 個)

---

### 🟡 需人工確認 (caveat)

依 rule_id 列出，**不主動建議修法**。

> ℹ️ 額外 N 條規則因無 LLM 端點而未評估 (此為預設行為)。

### 🔵 第三方資源 (需 MODA 備註)

| Origin | Rule | 出現位置 |
|---|---|---|
| googleapis.com | CS3140801C | /about, /contact |

**註**: 違規來自外部 CDN/library，無法在你的 codebase 修。MODA 申請時於備註欄聲明 (WCAG 2.1 §5.4 Partial Conformance)。

---

### 下一步建議

1. (基於結果) — 例如「先修 1.1.1 alt 缺失 (影響 12 頁)」
2. 修完後叫我重跑做 regression diff
3. (若 site mode 但 fail 集中少數規則) `--fail-only` + `--ignore <RULE_ID>`

完整 JSON: `.a11y-moda/reports/<filename>`
```

---

## 9. Fix → re-verify

When user says "I fixed X, re-check":

1. **Read** `.a11y-moda/last-run.txt` (Read tool) to recover SCOPE / URL / LEVEL / FLAGS
   - **Do NOT** `source` it, `eval` it, or pipe its contents into Bash. Parse it as
     plain text and validate each value against the patterns in §5 before reuse.
   - If any line is malformed (URL doesn't start with `http`, LEVEL not in `{A,AA,AAA}`,
     etc.) → refuse and tell user "previous-run record looks corrupted; please re-run with explicit URL"
2. Build a new `TS` and a new output path; invoke `a11y-moda` directly (same security rules as §5)
3. **Read both JSONs** (Read tool) — don't rely on `jq` / `diff` (Windows users typically lack both)
4. Diff in-context: extract `(rule_id, snippet, status)` tuples from `.issues`, sort, compare
5. Present three buckets:

```markdown
## Regression Check

- ✅ Fixed N: <rule_id list>
- ⚠️ Still failing M: <rule_id list>
- 🚨 New regressions K: <rule_id list>     ← if any, flag prominently
```

For full fix-loop details (site mode `pages_affected` diff, baseline naming convention), see `REFERENCE.md` §3.

---

## 10. Boundaries

| Task | Redirect to |
|---|---|
| Generic JSX lint (no MODA mapping) | `eslint-plugin-jsx-a11y` (use it alongside `a11y-moda lint` if user already has eslint) |
| LLM-based subjective source review | DopplerKuo's [`a11y-tw-audit-skill`](https://github.com/DopplerKuo/a11y-tw-audit-skill) (complements `a11y-moda lint` for hard-to-codify rules) |
| Generic axe-core (no MODA mapping) | `npx @axe-core/cli` |
| Screen reader testing | Manual NVDA / VoiceOver / TalkBack |
| Final MODA certification | Official [Freego](https://accessibility.moda.gov.tw/) |

When user asks for the above, name the alternative tool clearly.

---

## 11. LLM = invisible by default

**Treat LLM as if it does not exist.**

- Don't add `--llm-*` flags.
- Don't check `A11Y_LLM_*` env vars.
- Don't ask user about LLM.
- Don't volunteer LLM as setup option.

CLI handles LLM internally — if env vars are set globally, used silently. If not, ~70% of AAA rules + 100% of A/AA rules still run on DOM checks alone. Either way, skill behavior is identical.

Mention LLM **only** if user explicitly asks "how do I get fewer caveats" or "why are these caveats here". Then see `REFERENCE.md` §4.

---

## 12. When uncertain → Read REFERENCE.md

The companion file `REFERENCE.md` (in this skill directory) covers:

| Need | REFERENCE.md § |
|---|---|
| User asks something ambiguous (cron / baseline / ignore certain rules) | §1 Common requests |
| CLI errored and you don't recognize the message | §2 Error → action mapping |
| User asks about LLM / wants fewer caveats | §4 LLM details |
| Fix-loop edge case (site mode, missing baseline) | §3 Fix loop full |
| User wants MODA rule documentation | §5 Rule lookup |

For the canonical CLI/JSON/flag spec (not skill-specific), see `docs/AI_INTEGRATION.md` in the a11y-moda repo.

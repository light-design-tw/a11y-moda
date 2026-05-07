---
name: a11y-moda
description: Run a Taiwan MODA WCAG accessibility audit on a web page or whole site using the a11y-moda CLI. Triggers on requests like "check a11y", "audit accessibility", "WCAG check", "無障礙檢查", "MODA 標章驗證", "AAA 自評", and similar accessibility verification asks. Auto-detects SPA/dev-server context, picks correct CLI flags, parses JSON output, separates third-party caveats from fixable failures, and offers a fix → re-verify loop.
allowed-tools:
  - Bash
  - Read
  - Glob
  - Edit
---

# a11y-moda — MODA WCAG Audit Skill

Run the `a11y-moda` Python CLI against the user's web target, parse its JSON,
present findings in zh-TW Markdown, and offer a fix → re-verify loop.

**For edge cases not covered here, Read `REFERENCE.md` in this skill directory.**

---

## 1. Pre-flight

Verify install:

```bash
command -v a11y-moda
```

If missing, tell user (don't try to install for them):

```
a11y-moda not installed. Install with:
    pip install a11y-moda
    playwright install chromium    # one-time, required for --render
```

---

## 2. Determine scope

| User says | Scope |
|---|---|
| One URL / one page / `/path` | `scan` |
| "Whole site" / "every page" / "MODA 標章" | `site` |
| Ambiguous | Default `scan`; offer to escalate to `site` after results |

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
| User mentions "AAA" / "AAA 自評" | `--level AAA` |
| User mentions "A only" | `--level A` |
| Default level | `--level AA` (MODA 標章 baseline) |
| User wants only actionable | `--fail-only` |
| Cross-checking with official Freego | `--freego-compat` |
| Skip E rules (machine-only) | `--freego-only` |
| Production scan, be polite | `--rps 1 --delay 0.5` |
| Site mode page cap (default 30) | `--max-pages N` |

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
| `<URL>` | starts with `http://` or `https://`; no spaces | user input |
| `<scope>` | exactly `scan` or `site` | your own decision (§2) |
| `<LEVEL>` | exactly `A`, `AA`, or `AAA` | §3 |
| `<PORT>` (in dev server probe) | `[0-9]+` only | package.json scripts heuristic |
| `<RULE_ID>` (for `--ignore`) | `[A-Z]{2}[0-9]+[CE]?` | user mention |
| `<other flag args>` | only flags from §4 decision table | your own decision |

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
| JSX/TSX source-time lint | `eslint-plugin-jsx-a11y` |
| AI source review (no CLI) | DopplerKuo's [`a11y-tw-audit-skill`](https://github.com/DopplerKuo/a11y-tw-audit-skill) |
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

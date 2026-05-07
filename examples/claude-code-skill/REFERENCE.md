# a11y-moda Skill — Reference

> Loaded on-demand by Claude when SKILL.md flow needs more detail. Don't read this proactively — only when SKILL.md §12 directs you here.

---

## §1 Common requests (edge cases)

Only the genuinely ambiguous cases. Common requests like "scan this URL" are
covered by SKILL.md §1-§8 directly.

| User says | Action |
|---|---|
| "check a11y" with no URL | Ask: "Which URL? For local dev: `http://localhost:<PORT>/<path>`" |
| "ignore Google CSE issues" | Add `--ignore CS3140801C --ignore CS3140802C --ignore CS2140401C` (the three Freego-compat rules). Note that these auto-downgrade to caveat in default mode anyway |
| "cron / scheduled scan" | Suggest GitHub Actions cron + `a11y-moda site` + JSON artefact upload. Don't try to set up locally |
| "compare with last week's scan" | If `.a11y-moda/reports/<OLDER_DATE>-*.json` exists, diff against it. If not, explain a baseline must be captured first |
| "scan all my client sites" | Ask which sites; loop `a11y-moda scan` per URL; combine reports. **Confirm before scanning third-party sites** (rate-limit + ToS) |
| "make this rule pass" pointing at one issue | If `fail` → suggest specific code change. If `caveat` → ask why (don't blindly suppress); third-party caveats are usually correct |
| "AAA 自評 20 題對照" | Run `site --level AAA`, then map results to MODA's 20 self-eval questions. Mention 18/20 automated, 2 informative caveat |
| "freego-compat 是什麼" | Explain: aligns reporting format for 3 specific CSS rule_ids (CS2140401C/CS3140801C/CS3140802C) so output cross-checks against the official Freego tool |

---

## §2 Error → action mapping

| CLI output | Cause | Action |
|---|---|---|
| `refused unsafe URL` | URL is localhost / RFC1918 without `--allow-private-hosts` | Add `--allow-private-hosts` and re-run |
| `Executable doesn't exist` | Playwright Chromium not installed | Tell user: `playwright install chromium` |
| `Connection refused` (in fetch_error) | Dev server not running on that port | Tell user to start dev server first |
| `discovered 0 URL(s)` (site mode) | sitemap.xml missing AND BFS found nothing | Try `--source crawl --render-crawl` (JS-injected links); if still empty, fall back to user-provided URL list |
| HTTP 403 / 429 in `fetch_error` | Rate-limited or bot-blocked | Add `--rps 1 --delay 1` and retry; if persists, target may need authenticated scan (not supported) |
| HTTP 5xx in `fetch_error` | Target server error | Not our problem; report to user, don't auto-retry |
| `caveat: LLM unavailable` | No LLM env vars (default) | NOT an error. Filter from main report (SKILL §7). Don't suggest setup unless user asks |
| `caveat: LLM error: <msg>` | LLM endpoint configured but returned error | Mention to user once: "LLM at `<base_url>` returned `<msg>`; affected N rules fell back to caveat" |
| Skill fails to find `a11y-moda` binary | Not installed / not on PATH | Tell user: `pip install a11y-moda` (mention venv if they're in one) |

---

## §3 Fix loop (full)

Brief version in SKILL.md §9. This is the complete sequence.

### Single page (scan)

1. **Baseline**: `a11y-moda scan "$URL" --level AA --format json -o .a11y-moda/reports/<TS>-baseline.json`
2. **User applies fix** (edits code, deploys, restarts dev server)
3. **Re-scan**: same command, save to `.a11y-moda/reports/<NEW_TS>-after.json`
4. **Read both** with Read tool
5. **Diff in-context**:
   - Extract `(rule_id, snippet, status)` tuples from `.issues` of each
   - Sort both lists
   - Set difference: `before` − `after` = fixed; `after` − `before` = new
   - Same `rule_id`+`snippet` in both = still failing
6. **Present** three buckets (fixed / still / new regressions). Flag regressions prominently.

### Site mode

Same loop but additionally:
- Diff `site_summary.fail` (overall count delta)
- Diff `by_rule.<rule_id>.pages_affected` lists (which pages newly affected vs newly clean)
- Per-page: same single-page diff method

### Baseline naming convention

Use stable suffixes: `-baseline.json` for first capture, `-after.json` / `-after2.json` etc for iterations. Makes manual review obvious.

LLM cache (`~/.cache/a11y-moda/llm/`) makes re-runs cheap — only changed snippets re-judge.

---

## §4 LLM details (only when user asks)

Mention LLM **only** if user explicitly asks one of:
- "How do I get fewer caveats?"
- "Why are these caveats here?"
- "Set up LLM for a11y-moda"

### Quick answer

`a11y-moda` runs ~70% of AAA rules + 100% of A/AA rules without any LLM. The remaining E (extension / human-judgement) rules — form-label semantics, heading nesting, alt-text quality — produce `caveat: LLM unavailable` when no LLM endpoint is configured.

To enable, set env vars (any OpenAI-compatible endpoint):

```bash
export A11Y_LLM_BASE_URL=http://localhost:8000/v1   # local: vLLM / Ollama / LM Studio
                                                     # cloud: https://api.openai.com/v1
export A11Y_LLM_KEY=sk-...                           # use "sk-noauth" for keyless local
export A11Y_LLM_MODEL=qwen3-vl-8b                    # or gpt-4o-mini, claude-3-5-haiku, etc
```

Place in `~/.config/a11y-moda/.env` (global) or `./.env` (per-project).

### Cache behavior

- Path: `~/.cache/a11y-moda/llm/` (cross-platform — Python `Path.home()` resolves correctly on Windows: `C:\Users\<u>\.cache\a11y-moda\llm`)
- Hashed by (system_prompt, user_prompt, max_tokens, temperature)
- Same content → 0 API calls on re-run
- Delete the cache dir to force re-judge

### Vision (VLM) capability

Some rules use vision models (e.g. GN1240500E — sitemap detection from screenshot). The CLI auto-probes whether the configured model supports vision on first call; result cached at `~/.cache/a11y-moda/llm/_vision_capability.json`.

If user's model is text-only (e.g. `gpt-4o-mini` text mode), vision rules silently fall back to caveat. Tell user a vision-capable model (`gpt-4o`, `qwen3-vl-*`, `claude-3-5-sonnet`) is needed for those rules.

### Per-call override

Skill should NOT use `--llm-*` flags. But if user provides them inline ("use gpt-4o for this scan"), pass through:

```bash
a11y-moda scan ... --llm-base-url https://api.openai.com/v1 --llm-model gpt-4o
```

---

## §5 MODA rule lookup

For each `rule_id` in fail / caveat output, link to the official MODA documentation. The `rule_id` format encodes the topic:

| Prefix | Topic | Example |
|---|---|---|
| `HM` | HTML semantics / structure | `HM1110100C` (img alt) |
| `GN` | General / global | `GN2240600E` (heading descriptiveness) |
| `CS` | CSS / presentation | `CS2240700E` (focus visible) |
| `AR` | ARIA | `AR3130600E` (landmark) |
| `FA` | Form / accessibility | `FA2410303E` (form ARIA) |
| `SC` | Specific component | `SC2141004E` (responsive text) |

Suffix `C` = machine check (covered by Freego too).
Suffix `E` = extension / human-judgement rule (we automated; Freego just lists them).

> **Same numeric ID can have BOTH suffixes**, representing different layers of the same topic. Example:
> - `HM1110100C` — `<img>` has an `alt` attribute (machine check: presence)
> - `HM1110100E` — the alt text is descriptive and accurate (human/LLM judgement: quality)
>
> They're **distinct rules** that can pass / fail independently. Don't conflate.

Official docs: https://accessibility.moda.gov.tw/ (search by rule_id)

---

## §6 Comparison with adjacent tools

If user asks "should I use a11y-moda or X":

| Tool | Best for | Mention if user is |
|---|---|---|
| `a11y-moda` (this) | MODA-aligned audit, AAA self-eval, site crawl, JSON for AI | Pre-MODA submission, post-deploy monitoring, AI workflow |
| `eslint-plugin-jsx-a11y` | JSX/TSX source-time lint, IDE feedback | Writing React code |
| `axe-core` / `@axe-core/cli` | Generic WCAG runtime, browser ext | Wanting non-MODA generic a11y |
| Pa11y | Headless WCAG runtime, similar to axe | Same as axe-core |
| DopplerKuo `a11y-tw-audit-skill` | Claude Code skill, LLM judges JSX source | Source review during dev (complements us) |
| Official Freego | MODA certification submission | **Required** for actual standard certification |

These are complementary, not competing. Full integration narrative in `docs/AI_INTEGRATION.md` §12.

# a11y-moda

Python CLI for **Taiwan MODA accessibility certification** (無障礙標章 A / AA / AAA).

> ⚠️ **Unofficial / community tool.** Not affiliated with, endorsed by, or sponsored by Taiwan's Ministry of Digital Affairs (MODA / 數位發展部). Results are for developer convenience and do not replace official MODA review. The official tool is **[Freego](https://accessibility.moda.gov.tw/)**.
>
> 本工具為**非官方**社群開源專案，與數位發展部 (MODA) 無從屬關係，不替代官方 Freego 與正式審查流程。

The official tool — [Freego](https://accessibility.moda.gov.tw/) — is a Java GUI without CLI, Docker, or API support. `a11y-moda` is a CLI complement designed for **CI/CD pipelines** and **AI-assisted scanning workflows**. It implements MODA's published accessibility rule codes (HM / GN / CS / AR / FA / SC) and maps each finding to the corresponding MODA rule ID and WCAG 2.1 success criterion.

LLM-assisted (OpenAI-compatible endpoint) for human-judgement rules (E codes). Works with OpenAI, Anthropic, OpenRouter, Ollama, vLLM, LM Studio, llama.cpp server — anything exposing `/v1/chat/completions`.

## Features

- Static scan (httpx + BeautifulSoup) or rendered scan (Playwright / headless Chromium) for SPAs.
- A / AA / AAA level filtering.
- Site crawl: sitemap.xml first, BFS fallback.
- Output: JSON / Markdown / HTML (HTML always renders by-rule, by-WCAG, by-URL views).
- LLM judge cache on disk — safe to re-run, only changed rules re-call the model.
- Vision-capable models can verify image / layout rules from screenshots.
- Optional `--freego-compat` mode aligns reporting with the official MODA tool for cross-checking.

## MODA AAA self-eval coverage (20/20)

Implements every question on MODA's AAA self-evaluation form. The official tool covers **0** of these E (人工 / human-judgement) rules — submitters declare each one manually. We automate **18 / 20** end-to-end and surface the remaining **2** as informative caveats for human verification.

Mechanism breakdown:

| Mechanism | Count | Rules |
|---|---|---|
| **Pure DOM** (no external deps, ms-level) | 9 | Q2 GN1110111E (CAPTCHA alt) · Q3 GN3120600 (video detection + caveat) · Q6 AR3130600E (landmark) · Q7 HM1130110E (complex table) · Q8 GN1210101E (keyboard reachable) · Q10 GN1240100E (skip link) · Q13 HM3240800E (breadcrumb) · Q14 CS2141204E (em units) · Q18 HM2130500E (autocomplete) |
| **LLM (text)** — OpenAI-compatible | 5 | Q1 HM1110103E (long alt) · Q4 HM1130104E (heading nesting) · Q5 GN2240600E (descriptive headings) · Q9 HM1240402E (image-link wording) · Q17 GN1330201E (required field labelling) |
| **VLM (vision)** — multimodal | 1 | Q11 GN1240500E (sitemap detection from homepage screenshot) |
| **Browser probe** (Playwright, no LLM) | 5 | Q12 CS2240700E (focus visible) · Q15 GN2140300E (AA contrast 4.5:1) · Q16 GN3140600E (AAA contrast 7:1) · Q19 GN3330602E (modal-aware form detection) · Q20 GN2330300E (empty submit → focus on first invalid required) |

**70 % of the 20 rules run without any LLM/VLM call** — only 6 / 20 require external model access. Disable LLM and 14 rules still produce verdicts. LLM / VLM endpoints can point to a local model (Ollama, vLLM, LM Studio, qwen3-vl-8b, etc.) so request data never leaves your network.

> Total registered rules across the package: **129** (covering Freego's machine-checked C rules plus extension E rules). The table above is the AAA self-eval subset.

## Install

```bash
pip install -e .
playwright install chromium    # required for --render and Playwright-based probes
```

Python ≥ 3.10.

## Quick start

Scan one URL:

```bash
a11y-moda scan https://example.com --level AA
```

Crawl + scan a whole site, render JS, use a local VLM, write HTML report:

```bash
a11y-moda site https://example.com \
  --level AAA --max-pages 30 --render \
  --llm-base-url http://localhost:8000/v1 --llm-model qwen3-vl-8b \
  --format html -o report.html
```

LLM endpoint via env (used when `--llm-*` flags omitted):

```bash
export A11Y_LLM_BASE_URL=https://api.openai.com/v1
export A11Y_LLM_KEY=sk-...
export A11Y_LLM_MODEL=gpt-4o-mini
```

## Command reference

```
a11y-moda scan <URL>     scan a single page
a11y-moda site <URL>     discover and scan a whole site
```

Common options:

| Flag | Default | Note |
|---|---|---|
| `--level A\|AA\|AAA` | `AA` | scan level |
| `--render` | off | use headless Chromium for JS-rendered pages |
| `--max-pages N` | 30 | upper bound for `site` |
| `--source sitemap\|crawl\|auto` | `auto` | URL discovery strategy |
| `--workers N` | 4 | parallel workers (static scans only; render is serial) |
| `--rps N` | 0 | global rate cap (req/s); 0 = unlimited |
| `--ignore RULE_ID` | — | repeatable; skip specific rule IDs |
| `--freego-only` | off | only rules covered by the official tool's machine checks |
| `--freego-compat` | off | match the official tool's reporting for CS2140401C / CS3140801C / CS3140802C |
| `--format json\|md\|html` | `json` | output format (also auto-detected from `-o` extension) |
| `-o FILE` | stdout | bare filename → `./reports/FILE` |

## How rules work

Each MODA rule_id is one Python file under `src/a11y_moda/rules/codes/<theme>/<RULE_ID>.py`. The package auto-discovers every rule via `pkgutil.iter_modules` — registration is automatic via the `@register` decorator.

Skeleton:

```python
from ....models import Level
from ...base import Rule, RuleMeta, register
from ...helpers import should_skip, truncate

@register
class MyRule(Rule):
    meta = RuleMeta(rule_id="XX1234567E", guideline="1.1.1", level=Level.A,
                    desc="...", source="extension")
    def _check(self, soup, report, *, html, url, ctx) -> None:
        ...
        report.add(self._issue(message="...", snippet="...", status="fail"))
```

`source = "freego"` → rule covered by the official MODA tool's machine checks.
`source = "extension"` → an E (人工 / manual) rule we automated programmatically.

## Project status

Pre-1.0. Rule coverage tracked against MODA's published rule set; LLM-assisted rules require external LLM access. Output schema may change before 1.0.

## License

[MIT](LICENSE)

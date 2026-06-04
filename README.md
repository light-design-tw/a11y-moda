# a11y-moda

[![PyPI](https://img.shields.io/pypi/v/a11y-moda)](https://pypi.org/project/a11y-moda/)
[![Python](https://img.shields.io/pypi/pyversions/a11y-moda)](https://pypi.org/project/a11y-moda/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/light-design-tw/a11y-moda/blob/main/LICENSE)

> 台灣 MODA 無障礙檢測 + 規則查詢 CLI · WCAG A / AA / AAA · zh-TW · CI / AI 友善

**繁體中文** · [English](https://github.com/light-design-tw/a11y-moda/blob/main/README.en.md)

> ⚠️ **非官方社群工具。** 與數位發展部 (MODA / 數位發展部) 無從屬關係，不替代官方 [Freego](https://accessibility.moda.gov.tw/) 與正式審查流程。本工具僅為開發者便利之用。

## 目錄

- [為什麼做這個](#為什麼做這個)
- [安裝](#安裝)
- [30 秒上手](#30-秒上手)
- [`lint` — 寫程式時掃](#lint--寫程式時掃-原始碼-ast-無-playwright)
- [`rules` / `explain` — 查 MODA 規則](#rules--explain--查-moda-規則)
- [`scan` / `site` — 部署前 / 上線後掃](#scan--site--部署前--上線後掃-渲染-dom)
- [lint vs scan 怎麼選](#lint-vs-scan-怎麼選)
- [AI 協作整合 (Claude Code / Cursor / Copilot / Aider)](#ai-協作整合-claude-code--cursor--copilot--aider)
- [MODA AAA 自評涵蓋率 (20/20)](#moda-aaa-自評涵蓋率-2020)
- [指令參考](#指令參考)
- [規則怎麼運作](#規則怎麼運作)
- [專案狀態](#專案狀態)

## 為什麼做這個

MODA 官方工具 [Freego](https://accessibility.moda.gov.tw/) 是 Java GUI，沒有 CLI、Docker、API 介面。`a11y-moda` 補這個缺口，給 **CI/CD pipeline** 跟 **AI 協作開發** 用。實作 MODA 公布的規則編碼 (HM / GN / CS / AR / FA / SC)，每筆 issue 標注對應 MODA rule_id 跟 WCAG 2.1 success criterion。

工具分三層，對應開發流程不同階段：

| 命令 | 階段 | 機制 | 依賴 |
|---|---|---|---|
| **`lint`** | 寫程式時 / CI | 原始碼 tree-sitter AST | 純 Python，~30MB |
| **`rules` / `explain`** | 寫程式前 / agent 查表 | 規則 metadata 查詢 | 純 Python，~30MB |
| **`scan` / `site`** | 部署前 / 上線後 | 渲染 DOM + 對比度 + focus trap + 輪播自轉 + 深色模式 | + Playwright，~290MB |

人工判斷類規則 (E codes) 接 OpenAI 相容 API。OpenAI、Anthropic、OpenRouter、Ollama、vLLM、LM Studio、llama.cpp server — 任何吐 `/v1/chat/completions` 的端點都接得起來。LLM 端點可指本地模型，request 不離開內網。

## 安裝

```bash
# 標準安裝 — lint + rules + explain + init 全可用 (~30MB)
pip install a11y-moda

# 加上 scan / site / --render — 含 Playwright (~290MB)
pip install 'a11y-moda[scan]'
playwright install chromium
```

Python ≥ 3.10。

> ⚠️ **since v0.3.0 BREAKING** — Playwright 不再預設安裝。如果你只用 `lint` / `rules` (大多數 CI 用例)，標準安裝就夠。要跑 `scan` / `site` / `--render` / `--render-crawl` / `--probe-modals` 才需要 `[scan]` extra。

> ⚠️ `pip install 'a11y-moda[scan]'` **不會自動下載 Chromium**。第一次跑 `--render` 前必須執行 `playwright install chromium`，否則會噴 `Executable doesn't exist` 錯誤。

從 source 開發安裝：

```bash
git clone https://github.com/light-design-tw/a11y-moda
cd a11y-moda
pip install -e '.[scan,dev]'
playwright install chromium
```

## 30 秒上手

```bash
# 寫程式時 — 掃 React / Vue / HTML 原始碼
a11y-moda lint src/

# 查規則 — agent 寫 code 前先查 MODA 規範
a11y-moda rules search button
a11y-moda explain HM1110100C

# 部署前 — 掃 build output
a11y-moda scan ./dist/index.html --allow-file --render

# 上線後 — 掃整站
a11y-moda site https://example.com --level AA --max-pages 30
```

---

## `lint` — 寫程式時掃 (原始碼 AST，無 Playwright)

純 tree-sitter AST 靜態分析。**無 LLM、無瀏覽器、無網路**。快、可重複、CI 友善。50 條規則 ported from `scan` rule set，跨 JSX / TSX / TS / JS / HTML。

```bash
a11y-moda lint src/                          # 掃整個目錄
a11y-moda lint src/ --strict                 # 任何 issue 都 exit 非 0 (CI gate)
a11y-moda lint src/ --fail-only              # 只看 fail，忽略 caveat / info
a11y-moda lint src/ --exclude '**/*.test.*'  # 額外排除 (gitignore-style glob)
a11y-moda lint src/ --format json -o lint.json
```

預設尊重 `.gitignore`，內建排除 `node_modules` / `.next` / `dist` / `build` / `.git` / `.cache`。`--no-gitignore` 關掉。

**三態 status**：
- `fail` — AST 確證違規 (例 `<img>` 沒 alt)
- `caveat` — 需人工 / runtime 驗證 (例 `<div onClick>` 是不是 modal 背景)
- `info` — 樣式偏好

**Wrapper component 啟發**：首字大寫 JSX (`<Button>` / `<Dialog>`) 自動降級違規為 `caveat`，因為 shadcn / Radix / HeadlessUI 通常把 a11y 委派給底層 primitive。

**`runtime_authoritative` 降級 (since v0.2.1)**：跨檔 / 跨組件才能驗的規則 (例 `useHotkeys` 在外層、`outline:none` 在外部 CSS)，lint 不會叫 `fail`，會降 `caveat` 並附人工複查提示。`scan` 對同條規則照常 `fail` (有 Playwright 就有證據)。

CI 整合範例：

```yaml
# GitHub Actions
- run: pip install a11y-moda
- run: a11y-moda lint src/ --fail-only --strict
```

## `rules` / `explain` — 查 MODA 規則

Knowledge service：把規則 metadata 暴露為 CLI API，給 AI agent 在**寫 code 之前**查 MODA 規範用。133 條規則全可查。

```bash
a11y-moda rules list                         # 列全部 133 條
a11y-moda rules list --level AA              # 篩等級
a11y-moda rules list --topic forms           # 篩主題
a11y-moda rules list --source extension      # freego (機器) / extension (人工判斷) / moda-tw (在地化)
a11y-moda rules list --scope lint            # scan / lint (適用範圍)

a11y-moda rules search button                # 英文 keyword (內建 alias 對照表)
a11y-moda rules search 對比度
a11y-moda rules search dialog modal

a11y-moda rules show HM1110100C              # 完整 metadata (JSON)
a11y-moda explain HM1110100C                 # rules show 的短別名
```

每筆回 9 個欄位：`rule_id`, `guideline`, `level`, `level_name`, `desc`, `source`, `runtime_authoritative`, `wcag_url` (W3C WAI Quickref 連結), `topic`, `scope`。

**設計意圖**：agent 寫 `<button>` / `<dialog>` / `<form>` 前先 `rules search` 查相關規則，**寫對的而不是寫錯了再修**。Reactive lookup (`explain` 看 lint 報告後查解釋) 也行，但 proactive query 才是大 UX 贏。

## `scan` / `site` — 部署前 / 上線後掃 (渲染 DOM)

需要 `pip install 'a11y-moda[scan]'`。實際渲染 DOM、量對比度、走 Tab focus、模擬表單送出。

```bash
# 單頁
a11y-moda scan https://example.com --level AA

# 整站，渲染 JS，本地 VLM，HTML 報告
a11y-moda site https://example.com \
  --level AAA --max-pages 30 --render \
  --llm-base-url http://localhost:8000/v1 --llm-model qwen3-vl-8b \
  --format html -o report.html

# 同一網站再掃一次深色模式 (since v0.4.0)
a11y-moda site https://example.com --render --dark-mode \
  --level AA --format html -o report-dark.html

# 掃 build 出來的本地檔案 (Astro / Next export / Hugo / Eleventy / SvelteKit-static)
a11y-moda scan ./dist/index.html --allow-file --render
a11y-moda site ./dist --allow-file --render --level AA --format html -o dist-audit.html
```

`--allow-file` opt-in 才放行 `file://`。預設關閉，避免外部 redirect 騙工具讀本地檔。Windows 反斜線路徑 (`D:\dist\index.html`) 跟 POSIX 路徑都接受。

**`--dark-mode` (since v0.4.0；v0.4.1 改為自動雙跑)** — 自動跑 **light + dark 兩次**並合併結果。深色主題下才出現的 issue 會在 message 加上 `[深色模式]` 前綴標示。設計系統的對比度 bug 多半藏在深色變體，預設 light 掃描看不到。需搭配 `--render`。

**`--legacy-tls` (since v0.4.6)** — 部分 gov.tw / 企業舊系統還在用 TLS 1.0 + 弱 cipher，Python 3.12+ 預設嚴格握手會炸 `SSLV3_ALERT_HANDSHAKE_FAILURE` 或 `UNSAFE_LEGACY_RENEGOTIATION_DISABLED`。加 `--legacy-tls` 改用 relaxed `SSLContext`（TLS 1.0 floor、SECLEVEL=1、unsafe renegotiation 允許），憑證仍驗證。預設關閉。

```bash
a11y-moda scan https://舊系統.gov.tw --legacy-tls --level AA
```

**新增的 runtime probe (since v0.4.0)** — `--render` 模式下自動跑：
- **焦點陷阱偵測** (`tools/dialog_probe.py`) — 自動找 hamburger / dialog trigger，按 Tab N 次驗證焦點是否被 trap 在開啟容器內。MODA 對 1.4.1 / 2.4.3 / 2.4.7 的人工審查最常打回的點。
- **跳到主要內容偵測** — 自動找 skip link、按 Enter，驗證跳轉目標元素有可見焦點指示。
- **輪播自轉偵測** (`tools/carousel_probe.py`) — 觀察 `transform` / `scrollLeft` 變化判斷是否自動輪播 (~4.5 秒)，無需 class name 白名單，可抓 Wix / Webflow / 自製輪播。

LLM endpoint 用環境變數 (沒給 `--llm-*` flag 時 fallback)：

```bash
export A11Y_LLM_BASE_URL=https://api.openai.com/v1
export A11Y_LLM_KEY=sk-...
export A11Y_LLM_MODEL=gpt-4o-mini
```

LLM 結果存本地 cache (`~/.cache/a11y-moda/llm/`)，重跑安全，只有改動的規則重打模型。

## lint vs scan 怎麼選

| 你想做… | 用 | 為什麼 |
|---|---|---|
| 寫 code 時即時檢查 | `lint` | 純 AST 毫秒級，IDE 整合無痛 |
| CI gate (PR check) | `lint --strict` | 不需 Chromium，CI 安裝快 |
| Agent 寫 code 前查規範 | `rules search` / `explain` | Knowledge service，proactive |
| 掃 build output (Astro / Next export) | `scan --allow-file` | 已知 HTML，要 Playwright 量對比度 |
| 整站爬取 + 真實渲染 | `site --render` | SPA / 動態 JS / 對比度都需要 |
| 對比度 (4.5:1 / 7:1) 嚴格驗證 | `scan --render` | AST 看不到 computed CSS |
| Tab 順序 / focus 走訪 | `scan --render` | 需要實際 DOM + tab walk probe |

簡單規則：**寫程式時 `lint`，部署 / 驗收時 `scan`**。同一個 rule_id namespace，issue 可交叉對照。

## AI 協作整合 (Claude Code / Cursor / Copilot / Aider)

a11y-moda 設計上對 AI agent 友善 — 穩定 JSON schema、`status` enum 三態 (`fail` / `caveat` / `pass`)、第三方資源 `[third-party: <origin>]` 前綴等都有規範。讓 AI 邊寫 code 邊掃 a11y、邊修邊重驗，並在寫之前查規則。

**一鍵安裝整合 (since v0.3.1)**：

```bash
a11y-moda init claude-code        # → ~/.claude/skills/a11y-moda/
a11y-moda init cursor             # → ./.cursorrules
a11y-moda init copilot            # → ./.github/copilot-instructions.md
a11y-moda init aider              # → ./.aider.conf.yml
a11y-moda init agent              # → stdout (paste 進你的 agent system prompt)
a11y-moda init --list             # 列所有可裝的 IDE / agent
a11y-moda init <ide> --print      # 預覽不寫入
a11y-moda init <ide> --force      # 覆蓋既有檔案
```

完整文件：

| 文件 | 用途 |
|---|---|
| [`docs/AI_INTEGRATION.md`](./docs/AI_INTEGRATION.md) | 通用 AI agent 整合指南 (任何能呼 CLI 的 LLM)。含 JSON schema、flag 決策樹、各 IDE 範本 |
| [`src/a11y_moda/_examples/`](./src/a11y_moda/_examples/) | 5 個 IDE / agent 整合範本 (claude-code-skill / cursor / copilot / aider / generic-agent)，由 `a11y-moda init` 自動分發 |

> Claude Code skill 從 v0.3.2 起 description 改寫過，trigger 準確率經 90 次冷啟動 benchmark 量測達 90% (vs v0.3.1 的 53%)。已裝過的用戶請跑 `a11y-moda init claude-code --force` 升級。

## MODA AAA 自評涵蓋率 (20/20)

實作 MODA AAA 自評表全部 20 題。官方工具對這些 E (人工判斷) 規則的覆蓋率是 **0** — 送件人要逐題手動勾選。本工具自動化 **18 / 20**，剩下 **2** 以 informative caveat 標記，提供人工複查線索。

**20 條中 70% 不需要任何 LLM/VLM 呼叫** — 只有 6/20 需要外部模型。LLM 全關，14 條規則照樣有判斷結果。LLM / VLM 端點可指向本地模型 (Ollama, vLLM, LM Studio, qwen3-vl-8b 等)，request 不離開內網。

<details>
<summary><strong>展開 — 20 條規則機制拆解</strong></summary>

| 機制 | 數量 | 規則 |
|---|---|---|
| **純 DOM** (無外部依賴，毫秒級) | 9 | Q2 GN1110111E (CAPTCHA alt) · Q3 GN3120600 (影片偵測 + caveat) · Q6 AR3130600E (landmark) · Q7 HM1130110E (複雜表格) · Q8 GN1210101E (鍵盤可達) · Q10 GN1240100E (skip link) · Q13 HM3240800E (麵包屑) · Q14 CS2141204E (em 單位) · Q18 HM2130500E (autocomplete) |
| **LLM (文字)** — OpenAI 相容 | 5 | Q1 HM1110103E (長文 alt) · Q4 HM1130104E (標題巢狀) · Q5 GN2240600E (描述性標題) · Q9 HM1240402E (圖連結文字) · Q17 GN1330201E (必填欄位標示) |
| **VLM (視覺)** — 多模態 | 1 | Q11 GN1240500E (從首頁截圖偵測網站地圖) |
| **瀏覽器 probe** (Playwright，無 LLM) | 5 | Q12 CS2240700E (focus visible) · Q15 GN2140300E (AA 對比 4.5:1) · Q16 GN3140600E (AAA 對比 7:1) · Q19 GN3330602E (modal-aware 表單偵測) · Q20 GN2330300E (空送出 → focus 第一個必填無效欄位) |

</details>

> 套件總註冊規則數：**133** (涵蓋 Freego 的 C 類機器檢查 + 我們補的 E 類擴充規則 + MODA-Taiwan 在地化規則；v0.4.4 新增 `moda-tw` source 分類與 `H309204` / `MT309203` 兩條 AAA 標章常用稽核項)。AAA 自評只是子集；`lint` 涵蓋其中 50 條 source-checkable 規則。

## MODA-Taiwan 在地化規則 (`source="moda-tw"`，since v0.4.4)

MODA AAA 標章評核常引用的稽核項中，部分**不在 WCAG normative 文字裡**，也不在 MODA 公布的 E/C 主體系中 — 例如 accesskey 鍵盤快捷鍵 (Alt+U/C/N) 與「網站導覽」頁面的 Firefox 操作說明。這些屬於 MODA 110.07 規範的舊版 90 條檢測碼 (H 體系) + reviewer 在地稽核慣例，但拿著只實作 WCAG E/C 的工具去檢一定是 false negative，標章送件時會被打回。

`moda-tw` source tier 補這個缺口。預設開啟，不需 flag。送件 AAA 標章時建議連這層一起跑。`--freego-only` 會排除這層 (該 flag 是用來對齊官方 Freego 工具輸出的)。

| Rule ID | Level | 對應 WCAG | 檢什麼 |
|---|---|---|---|
| `H309204` | AAA | 2.4.1 (Bypass Blocks) | 頁面是否提供常用區塊 accesskey (典型 U=右上、C=中央、N=搜尋)；含孤兒 anchor 檢 (`<a accesskey href="#X">` 但無對應 `id`/`name`) |
| `MT309203` | AAA | — (純 MODA 在地慣例) | 網站導覽 (sitemap) 頁面是否含 accesskey 對應表 + Firefox 操作說明 (`Shift+Alt+key`)；**v0.4.5 新增**：表格描述文字 vs 同頁 accesskey 元素 `aria-label` / 報讀文字一致性比對，不一致 → fail。只在 URL / title / H1 偵測為 sitemap 頁時觸發 |

**Rule ID 命名**：`H309204` 是 MODA 90 條檢測碼第 H309204 條 (有官方依據)。`MT309203` 開頭 `MT` 表示「MODA-Taiwan extension by a11y-moda」(無 MODA 公布編號，本工具為標章審查實務新增)。

**crawler 配合 (since v0.4.4)**：`a11y-moda site` 現會在 sitemap.xml 探索後額外 HEAD-probe `/sitemap` `/Sitemap` `/sitemap.html` `/site-map` 四個常見 HTML 路徑並 prepend 進 URL 清單。sitemap.xml 通常不列「網站導覽」HTML 頁 (因屬 meta 而非內容)，加這個 probe 才能讓 `MT309203` 在全自動掃描下生效。

## 指令參考

```
a11y-moda lint <paths...>     原始碼 AST 掃描 (純 Python)
a11y-moda scan <URL>          單頁渲染 DOM 掃描 (需 [scan])
a11y-moda site <URL>          整站爬取 + 渲染 (需 [scan])
a11y-moda rules <command>     查 MODA 規則 metadata
a11y-moda explain <RULE_ID>   = rules show
a11y-moda init <ide>          安裝 IDE / agent 整合範本
```

<details>
<summary><strong>展開 — `scan` / `site` flag 表</strong></summary>

| Flag | 預設 | 說明 |
|---|---|---|
| `--level A\|AA\|AAA` | `AA` | 掃描等級 |
| `--render` | off | 用 headless Chromium 渲染 JS 頁面 |
| `--render-crawl` | off | 探索階段也用 Chromium (SPA 必要) |
| `--max-pages N` | 30 | `site` 上限 |
| `--source sitemap\|crawl\|auto` | `auto` | URL 探索策略 |
| `--workers N` | 4 | 並行 worker (僅靜態掃描；render 強制序列化) |
| `--rps N` | 0 | 全域速率上限 (req/s)，0 = 不限 |
| `--ignore RULE_ID` | — | 可重複；跳過指定 rule_id |
| `--freego-only` | off | 只跑官方工具有的機器檢查規則 (排除 extension + moda-tw) |
| `--freego-compat` | off | 對齊官方工具回報 (CS2140401C / CS3140801C / CS3140802C) |
| `--allow-file` | off | 放行 `file://` 與本地路徑 (build output 用) |
| `--probe-modals` | off | 模擬點擊偵測 modal / dialog |
| `--dark-mode` | off | 模擬 `prefers-color-scheme=dark`，掃深色變體對比度 (需 `--render`) |
| `--format json\|md\|html` | `json` | 輸出格式 (也會從 `-o` 副檔名自動判斷) |
| `-o FILE` | stdout | 純檔名 → `./reports/FILE` |

</details>

<details>
<summary><strong>展開 — `lint` flag 表</strong></summary>

| Flag | 預設 | 說明 |
|---|---|---|
| `--strict` | off | 任何 issue (含 info) 都 exit 非 0；CI gate 用 |
| `--fail-only` | off | 只輸出 `fail` tier，忽略 `caveat` / `info` |
| `--exclude PATTERN` | — | 可重複；gitignore-style glob 排除 |
| `--no-gitignore` | off | 不讀 `.gitignore` |
| `--format json\|md` | `json` | 輸出格式 |
| `-o FILE` | stdout | 同上 |

</details>

<details>
<summary><strong>展開 — `rules` 子命令 + `init` flag</strong></summary>

`rules`:

| Subcommand | 用途 |
|---|---|
| `rules list` | 列全部規則 (可 filter) |
| `rules show <RULE_ID>` | 完整 9 欄位 metadata |
| `rules search <KEYWORD>` | 關鍵字搜尋 (英文 alias 對照 zh-TW desc) |

`rules list / search` 共用 filter：`--level` / `--topic` / `--source` / `--scope` / `--format json|md`。

`init`:

| Flag | 用途 |
|---|---|
| `<ide>` | claude-code / cursor / copilot / aider / agent |
| `--list` | 列所有可裝的 IDE / agent |
| `--print` | 印到 stdout 不寫檔 |
| `--dest PATH` | 覆寫預設安裝路徑 |
| `--force` | 覆蓋既有檔 (預設拒寫，避免破壞手改檔) |

</details>

## 規則怎麼運作

每個 MODA rule_id 一個 Python 檔，放 `src/a11y_moda/rules/codes/<主題>/<RULE_ID>.py`。套件用 `pkgutil.iter_modules` 自動探索；用 `@register` decorator 自動註冊，不用改清單。

<details>
<summary><strong>展開 — 規則檔樣板</strong></summary>

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

`source = "freego"` → 對應官方工具有的機器檢查規則
`source = "extension"` → E (人工判斷) 規則被我們程式化的版本
`source = "moda-tw"` → MODA-Taiwan 在地化規則 — AAA 標章稽核常引用、但 WCAG E/C 主體系未收的項目 (例：H309204 accesskey 快捷鍵、MT309203 sitemap 操作說明)。`--freego-only` 會排除

</details>

`lint` 規則放 `src/a11y_moda/lint/codes/<主題>/<RULE_ID>.py`，layout 跟 `rules/codes/` 平行。

## 專案狀態

Pre-1.0。規則覆蓋率對齊 MODA 公布的規則集；LLM 類規則需外部 LLM 接取。1.0 前輸出 schema 可能會變動。

完整變更紀錄見 [CHANGELOG.md](./CHANGELOG.md)。

## License

[MIT](https://github.com/light-design-tw/a11y-moda/blob/main/LICENSE)

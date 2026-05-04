# a11y-moda

> 台灣 MODA 無障礙標章送審用的 Python CLI · WCAG A / AA / AAA · zh-TW 報告

**繁體中文** · [English](./README.en.md)

> ⚠️ **非官方社群工具。** 與數位發展部 (MODA / 數位發展部) 無從屬關係，不替代官方 [Freego](https://accessibility.moda.gov.tw/) 與正式審查流程。本工具僅為開發者便利之用。

## 為什麼做這個

MODA 官方工具 [Freego](https://accessibility.moda.gov.tw/) 是 Java GUI，沒有 CLI、Docker、API 介面。`a11y-moda` 補這個缺口，給 **CI/CD pipeline** 跟 **AI 協作開發** 用。實作 MODA 公布的規則編碼 (HM / GN / CS / AR / FA / SC)，每筆 issue 標注對應 MODA rule_id 跟 WCAG 2.1 success criterion。

人工判斷類規則 (E codes) 接 OpenAI 相容 API。OpenAI、Anthropic、OpenRouter、Ollama、vLLM、LM Studio、llama.cpp server — 任何吐 `/v1/chat/completions` 的端點都接得起來。

## 功能

- 靜態掃描 (httpx + BeautifulSoup) 或渲染掃描 (Playwright / headless Chromium，給 SPA 用)
- A / AA / AAA 等級過濾
- 全站爬取：先 sitemap.xml，找不到就 BFS
- 輸出：JSON / Markdown / HTML (HTML 一律渲染依規則 / 依 WCAG / 依 URL 三種 view)
- LLM 判斷結果存本地 cache — 重跑安全，只有改動的規則重打模型
- 視覺模型 (VLM) 從截圖驗證版面 / 圖片類規則
- `--freego-compat` 對齊官方工具回報格式，便於交叉比對

## MODA AAA 自評涵蓋率 (20/20)

實作 MODA AAA 自評表全部 20 題。官方工具對這些 E (人工判斷) 規則的覆蓋率是 **0** — 送件人要逐題手動勾選。本工具自動化 **18 / 20**，剩下 **2** 以 informative caveat 標記，提供人工複查線索。

機制拆解：

| 機制 | 數量 | 規則 |
|---|---|---|
| **純 DOM** (無外部依賴，毫秒級) | 9 | Q2 GN1110111E (CAPTCHA alt) · Q3 GN3120600 (影片偵測 + caveat) · Q6 AR3130600E (landmark) · Q7 HM1130110E (複雜表格) · Q8 GN1210101E (鍵盤可達) · Q10 GN1240100E (skip link) · Q13 HM3240800E (麵包屑) · Q14 CS2141204E (em 單位) · Q18 HM2130500E (autocomplete) |
| **LLM (文字)** — OpenAI 相容 | 5 | Q1 HM1110103E (長文 alt) · Q4 HM1130104E (標題巢狀) · Q5 GN2240600E (描述性標題) · Q9 HM1240402E (圖連結文字) · Q17 GN1330201E (必填欄位標示) |
| **VLM (視覺)** — 多模態 | 1 | Q11 GN1240500E (從首頁截圖偵測網站地圖) |
| **瀏覽器 probe** (Playwright，無 LLM) | 5 | Q12 CS2240700E (focus visible) · Q15 GN2140300E (AA 對比 4.5:1) · Q16 GN3140600E (AAA 對比 7:1) · Q19 GN3330602E (modal-aware 表單偵測) · Q20 GN2330300E (空送出 → focus 第一個必填無效欄位) |

**20 條中 70% 不需要任何 LLM/VLM 呼叫** — 只有 6/20 需要外部模型。LLM 全關，14 條規則照樣有判斷結果。LLM / VLM 端點可指向本地模型 (Ollama, vLLM, LM Studio, qwen3-vl-8b 等)，request 不離開內網。

> 套件總註冊規則數：**129** (涵蓋 Freego 的 C 類機器檢查 + 我們補的 E 類擴充規則)。上表只是 AAA 自評子集。

## 安裝

```bash
pip install -e .
playwright install chromium    # --render 跟 Playwright probe 都要這個
```

Python ≥ 3.10。

## 快速開始

掃單一 URL：

```bash
a11y-moda scan https://example.com --level AA
```

爬取整站 + 渲染 JS + 用本地 VLM + 輸出 HTML 報告：

```bash
a11y-moda site https://example.com \
  --level AAA --max-pages 30 --render \
  --llm-base-url http://localhost:8000/v1 --llm-model qwen3-vl-8b \
  --format html -o report.html
```

LLM endpoint 用環境變數 (沒給 `--llm-*` flag 時 fallback)：

```bash
export A11Y_LLM_BASE_URL=https://api.openai.com/v1
export A11Y_LLM_KEY=sk-...
export A11Y_LLM_MODEL=gpt-4o-mini
```

## 指令參考

```
a11y-moda scan <URL>     掃單頁
a11y-moda site <URL>     探索並掃整站
```

常用選項：

| Flag | 預設 | 說明 |
|---|---|---|
| `--level A\|AA\|AAA` | `AA` | 掃描等級 |
| `--render` | off | 用 headless Chromium 渲染 JS 頁面 |
| `--max-pages N` | 30 | `site` 上限 |
| `--source sitemap\|crawl\|auto` | `auto` | URL 探索策略 |
| `--workers N` | 4 | 並行 worker (僅靜態掃描；render 強制序列化) |
| `--rps N` | 0 | 全域速率上限 (req/s)，0 = 不限 |
| `--ignore RULE_ID` | — | 可重複；跳過指定 rule_id |
| `--freego-only` | off | 只跑官方工具有的機器檢查規則 |
| `--freego-compat` | off | 對齊官方工具回報 (CS2140401C / CS3140801C / CS3140802C) |
| `--format json\|md\|html` | `json` | 輸出格式 (也會從 `-o` 副檔名自動判斷) |
| `-o FILE` | stdout | 純檔名 → `./reports/FILE` |

## 規則怎麼運作

每個 MODA rule_id 一個 Python 檔，放 `src/a11y_moda/rules/codes/<主題>/<RULE_ID>.py`。套件用 `pkgutil.iter_modules` 自動探索；用 `@register` decorator 自動註冊，不用改清單。

樣板：

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

## 專案狀態

Pre-1.0。規則覆蓋率對齊 MODA 公布的規則集；LLM 類規則需外部 LLM 接取。1.0 前輸出 schema 可能會變動。

## License

[MIT](LICENSE)

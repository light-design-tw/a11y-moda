# 115.11 規範遷移計畫（110.07 → 115.11 / WCAG 2.2）

來源：MODA 無障礙網路空間服務網「函頒文件」公告 — 115年11月30日起正式實施修正版「網站無障礙規範(115.11)」（數位政府字第11540006711號令，115.5.29 發布）。對照基準：WCAG 2.2（W3C Recommendation, 2024-12-12）。

產出時間：2026-06-18
碼表基準：`docs/eval-codes.json`（110.07，240 碼）vs 115.11 規範全文（246 碼）vs 現行實作（~135 碼）

> 路徑慣例：規則檔位於 `src/a11y_moda/rules/codes/<主題>/<RULE_ID>.py`，一個 rule_id 一個檔。

---

## 背景

| 項目 | 110.07（現行） | 115.11（修正版） |
|---|---|---|
| 對齊 WCAG | 2.1 | **2.2** |
| 指引數 | 12 | 13 |
| 成功準則 | 78 | 87 |
| 檢測碼 + 稽核評量碼 | 240（C 31 / E 209） | 246（C 29 / E 217） |
| 標章檢測上線 | — | **2026-11-30** |

- 自 **2026-11-30** 起，新案標章檢測改用 115.11，同日**停止受理 110.7 標章申請**。
- **2026-11-29（含）前取得之無障礙認證標章，效期仍 3 年有效** → 既有標章不受換版影響。
- a11y-moda 定位為**協助工具**，碼表一律跟隨 MODA 公布版本；本計畫即接軌 115.11。

---

## 版本 diff 總覽

| 類別 | 條數 | 說明 |
|---|---|---|
| 兩版皆有（沿用） | 222 | rule_id 不變，現有規則直接續用 |
| **115.11 真新增** | **24**（C 3 / E 21） | 扣除 `XX3141099C/E`（碼表格式說明，非可檢測規則）→ **真規則 22 條** |
| 110.07 移除 / 改名 | 18 | 詳 Part B |

> ⚠️ 切勿用「115.11 有、我們沒有 = 124 條」當遷移量。其中 **101 條是 110.07 既有、本工具本來就未實作**（工具僅實作 110.07 的子集 ~135/240 ≈ 56%），與換版無關 → 歸入 Part C backlog，非 115.11-blocking。真正因換版而生的新工作 = Part A 的 22 條。

機制圖例（沿用 `rules_coverage_gap.md`）：

- 🟢 **純 DOM** — BeautifulSoup / regex，無外部依賴
- 🟡 **Browser** — Playwright 探測（computed style、tab walk、box 量測、responsive）
- 🔵 **LLM 文字** — OpenAI 相容 endpoint 語意判斷
- 🟣 **VLM 視覺** — 多模態模型看截圖判斷

---

## Part A — 115.11 真新增 22 條（換版必做）

### A-1. WCAG 2.2 新增成功準則

| rule_id | WCAG 2.2 SC | 等級 | 機制 | 復用現有機具 |
|---|---|---|---|---|
| FA2241100E | 2.4.11 焦點不被遮（最低） | AA | 🟡 | **需擴 tab_walk**：加 focused bbox + sticky 偵測（現有 FocusStop 無座標）|
| CS3241200E | 2.4.12 焦點不被遮（增強） | AAA | 🟡 | scroll-padding 靜態查＝弱代理、易誤判；嚴謹需 runtime 量遮蔽 |
| CS3241300E | 2.4.13 焦點外觀 | AAA | 🟡 | **需擴 tab_walk**：outline 幾何＋顏色→面積/對比（現有只有 `has_visible_outline` bool）|
| CS3241301E | 2.4.13 焦點外觀 | AAA | 🟡 | 同上（框線對比 / 粗細）|
| GN3241302E | 2.4.13 焦點外觀 | AAA | 🟡 | 同上（作者提供之可見焦點框線）|
| FA2250700E | 2.5.7 拖曳動作 | AA | 🟡 | 新 probe（偵測 drag handler + 單指替代），中等成本 |
| CS2250800E | 2.5.8 目標尺寸（最低 24px） | AA | 🟡 | 新 probe（量 click target box），簡單 |
| GN1320600E | 3.2.6 一致的協助 | A | 🔵 | **復用 judge**（跨頁定位 contact/help 機制） |
| GN1330700E | 3.3.7 冗餘輸入 | A | 🔵 弱 | 多步流程，自動化有限，建議 caveat-only |
| HM2330800E | 3.3.8 可及的驗證（最低） | AA | 🟢 | 檢查 `autocomplete` 標記 |
| FA2330801E | 3.3.8 / 3.3.9 可及的驗證 | AA | 🟢 | 檢查阻擋貼上 / 重新輸入限制 |
| GN3330900E | 3.3.9 可及的驗證（增強） | AAA | 手動 | 流程性，caveat-only |

### A-2. 既有 SC 之新失敗碼 / 機器碼

| rule_id | WCAG SC | 等級 | 機制 | 備註 |
|---|---|---|---|---|
| **HM1130104C** | 1.3.1 / 4.1.2 | A | 🟢 | 可見表單控制需有 `<label>` 或 `title`，**新機器碼** |
| **HM1130105C** | 1.3.1 | A | 🟢 | 表單以 `<fieldset>` 分群 + `<legend>` 說明，**新機器碼** |
| FA1130114E | 1.3.1 | A | 🟢 | 排版表格誤用 `th`/`caption`/`summary` |
| FA1130204E | 1.3.2 | A | 🔵 | 線性化後是否保持有意義序列 |
| FA1210102E | 2.1.1 | A | 🟡 | 指標專屬事件導致鍵盤失效 |
| FA1210401E | 2.1.4 | AA | 🟡 | 字元快捷鍵無法關閉 / 重新對應 |
| FA1220102E | 2.2.1 | A | 🟡 | 伺服器端逾時自動轉址 |
| FA2240701E | 2.4.7 | AA | 🟡 | outline / border 消除可見焦點框線 |
| GN2141009E | 1.4.10 | AA | 🟡 | 320px reflow 水平捲動 — **需新 reflow probe**（無現成 responsive probe）|
| GN3210301E | 2.1.3 | AAA | 🟡 | 全功能鍵盤可操作 — 疑與 GN1210101E（2.1.1 純 DOM）高度重疊，**待驗可能 skip** |

### A-3. Part A 工程量（2026-06-18 修正：原估「8 條復用」過樂觀）

實查 probe 基建後重估。tab_walk 的 `FocusStop` 只帶 `has_visible_outline`(bool) + `in_viewport`(bool) — 無 outline 幾何/對比、無 bbox；且**無 responsive/reflow probe**。focus「有無指示」已由 CS2240700E（2.4.7）覆蓋。故 🟡 多數不是純復用：

| 類別 | 條數 | 規則 |
|---|---|---|
| 🟢 純 DOM 低成本 | ~6 | HM1130104C / HM1130105C（已做）、FA1130114E、HM2330800E、FA2330801E |
| 🟡 **擴 tab_walk**（FocusStop 加 outline 幾何 + bbox，一次擴餵 4 條）| 4 | FA2241100E（2.4.11）＋ 2.4.13 ×3 |
| 🟡 **新 probe** | ~4 | GN2141009E（reflow）、CS2250800E（目標尺寸）、FA2250700E（拖曳）、CS3241200E（遮蔽 runtime）|
| 🟡 既有 DOM/computed 可判 | ~4 | FA1210102E、FA1210401E、FA1220102E、FA2240701E（多為靜態可偵）|
| 🔵 LLM | 3 | FA1130204E、GN1320600E、GN1330700E（弱）|
| 手動 / caveat | 2 | GN3330900E 等流程性 |

> 修正結論：純 DOM cheap win 已做完（上一輪 2 條：HM1130105C、ME1320200C）。剩餘 🟡 多需**擴 tab_walk**（加 FocusStop 欄位）或**新 probe**，會動到掃描各層的 state 透傳 — 需逐層驗證 ＋ 發版前 `--render` dogfood，非「順手復用」。優先「擴 tab_walk 一次出 4 條」CP 值最高。

---

## Part B — 110.07 移除 / 改名 18 條

| 判定 | rule_id | SC | 處理 |
|---|---|---|---|
| ✅ **確定移除** | HM1410100C | 4.1.1 | WCAG 2.2 官方移除 4.1.1 Parsing → 刪規則 |
| 🔄 改名 / 併號 | GN1210101E → FA1210102E | 2.1.1 | 對映後遷移 |
| 🔄 改名 / 併號 | GN3210300E → GN3210301E | 2.1.3 | 對映後遷移 |
| 🔄 改名 / 併號 | FA2210401E、GN2210400E → FA1210401E | 2.1.4 | 兩碼併入一碼 |
| ❓ 待人工核 | CS2140400C、CS2140402C（1.4.4）、CS3140804E（1.4.8）、FA2141104E、GN2141100E（1.4.11）、GN1220203E（2.2.2）、GN1240301E（2.4.3）、GN3120601E（1.2.6）、HM1110102C、HM1110108E（1.1.1）、HM1130108E（1.3.1）、HM3240904E（2.4.9）、HM3330500C（3.3.5） | 多 | 同 SC 無對應新碼，可能併入沿用碼或真廢 → 開 115.11 附件逐條核 |

> 方法驗證：HM1410100C 對得上 WCAG 2.2 正式廢除 4.1.1，佐證 diff 可信。

---

## Part C — 既有 backlog 101 條（非 115.11-blocking）

110.07 既有、115.11 仍在、本工具尚未實作的 101 條。**與換版無關**，但反映可擴張的覆蓋空間。

| 機制 | 條數 | 可否自動化 |
|---|---|---|
| 🟢 純 DOM | 39 | 純程式可補 |
| 🟡 Browser | 30 | probe 可補 |
| 🔵 LLM | 17 | ✅ AI 協助 |
| 🟣 VLM | 15 | ✅ AI 協助 |

- **AI（LLM+VLM）可協助 = 32 / 101（31%）**；理論上 101 條皆可自動化（39 DOM + 30 probe + 32 AI）。
- 分級：A 38 / AA 17 / **AAA 46**；type：E 98 / **C 3**（機器碼，cheap win）。
- LLM 可協助者集中於 SC 3.1.x（閱讀程度 / 語言，AAA）、3.3.4（錯誤預防，AA）、1.1.1（替代文字語意）；VLM 集中於 1.2.x 影音與視覺判斷。
- 觀察：**LLM / VLM 的擴張價值在 AAA 語意 / 視覺層**；A/AA 骨幹多以 DOM + probe 即可覆蓋。

---

## 建議排序

1. **cheap wins（純 DOM 機器碼）** — 已做（HM1130105C、ME1320200C）。見下方「實作進度」。
2. **擴 tab_walk 一次出 4 條**（CP 值最高）：FocusStop 加 outline 幾何 + bbox → 焦點外觀 2.4.13 ×3 + 焦點不被遮 2.4.11。碰 state-threading，需逐層驗 + `--render` dogfood。
3. **新 probe**：reflow 320px（GN2141009E）、目標尺寸（2.5.8）、拖曳（2.5.7）、遮蔽 runtime（2.4.12）。
3b. **既有 DOM/computed 可判**：FA1210102E / FA1210401E / FA1220102E / FA2240701E（靜態偵）；GN3210301E 先驗與 GN1210101E 重疊。
4. **LLM**：一致的協助（3.2.6）。
5. **移除 / 改名對帳**：Part B（含 13 條待核）。
6. **backlog 擴張**（獨立 roadmap，非換版必要）：Part C 的 32 條 AI 可協助項，優先 AA（17 條）。

> 發版注意：本遷移屬使用者可見的規則集變動，依 `CLAUDE.md` 發版 SOP 處理（CHANGELOG / README / 版本號避開 MCP 保留號）。

---

## 實作進度

| rule_id | SC | 機制 | 狀態 |
|---|---|---|---|
| HM1130104C | 1.3.1 | 🟢 DOM | 既已實作（先前已在 `forms/`），無需動工 |
| **HM1130105C** | 1.3.1 | 🟢 DOM | ✅ 新增 `forms/HM1130105C.py` — 同名 radio/checkbox 群組未以 `<fieldset>` 分群則 fail；與 HM1130103C（fieldset 須有 legend）職責互補不重疊 |
| **ME1320200C** | 3.2.2 | 🟢 DOM | ✅ 新增 `media/ME1320200C.py` — `<a>` 指向 .doc/.docx/.xls/.xlsx/.ppt/.pptx 等專屬格式則 fail；僅看 path 副檔名（查詢字串型下載 handler 不誤判） |
| CS3140800C | 1.4.8 | 🟡 **改判 Browser** | 單一樣式表下前景+背景色限制，需 computed CSS 串接判定，純靜態 DOM 易誤判 → 移到「復用 probe」階段（接 css_utils / contrast），非 cheap win |
| HM1110103C | 1.1.1 | 🔵 **改判 LLM/caveat** | 「字符圖案 / emoji 挪用文字外型作表意」無法以機器決定性判斷「是否作表意」→ 不適合純 DOM，改走語意判斷或 caveat，非 cheap win |
| **FA2241100E** | 2.4.11 | 🟡 Browser | ✅ 新增 `focus/FA2241100E.py` — 擴 tab_walk 偵測 sticky/fixed 遮蔽；聚焦元件**全遮**(obscured_fully)則 fail（部分遮蔽留 2.4.12）|
| **CS3241301E** | 2.4.13 | 🟡 Browser | ✅ 新增 `focus/CS3241301E.py` — outline < 2px → fail（焦點框線強度）；box-shadow only → caveat。指示「有無」仍由 CS2240700E(2.4.7) 負責 |
| CS3241300E | 2.4.13 | 🟡 **暫緩** | 雙色焦點對比 — 需相鄰色對比量測，現有 probe 無法可靠提供（避免噪音 / 與 2.4.7 重複）|
| GN3241302E | 2.4.13 | 🟡 **暫緩** | 作者提供框線 — author-vs-UA 判別不可靠，暫緩 |
| **CS2250800E** | 2.5.8 | 🟡 Browser | ✅ 新增 `responsive/CS2250800E.py` — 復用 `tab_stops.bbox`（不需新 probe）；寬與高皆 < 24px 才 fail（避免行內文字連結誤判）|
| **GN2141009E** | 1.4.10 | 🟡 Browser | ✅ 新增 `tools/reflow_probe.py` + `responsive/GN2141009E.py` — **新 probe**：viewport 縮 320px 量 scrollWidth>clientWidth → 水平捲動 fail。新增 `RuleContext.reflow` 欄位，**scanner 兩路徑都接** |
| FA2250700E | 2.5.7 | 🟡 **暫緩** | 拖曳替代 — 偵測 drag handler + 判斷單指替代訊號太弱、FP 高，暫緩 |
| **FA1220102E** | 2.2.1 | 🟢 DOM | ✅ 新增 `meta/FA1220102E.py` — `<meta http-equiv=refresh>` 計時(delay>0)轉向/重整 → fail；instant(0) 不誤判 |
| **FA1210102E** | 2.1.1 | 🟢 DOM | ✅ 新增 `keyboard/FA1210102E.py` — 僅綁指標啟動事件(onmousedown/up、pointer、touch、dblclick)且無 onclick/鍵盤 → fail。排除 hover 降 FP；僅 inline handler |
| FA1210401E | 2.1.4 | 🔵 **暫緩** | 字元快捷鍵能否關閉/重對應 = 純 JS，靜態 DOM 偵測不到 |
| FA2240701E | 2.4.7 | 🟡 **暫緩** | outline 移除 — runtime CS2240700E 已涵蓋（且更準），靜態版易誤判且重複 |
| **CS3241200E** | 2.4.12 | 🟡 Browser | ✅ 新增 `focus/CS3241200E.py` — 改以**復用 obscured**（任一點被遮）取代原先 scroll-padding 弱代理；任何部分被遮即 fail（對比 2.4.11 僅全遮）。localhost 固定列遮蔽頁 e2e 驗證觸發 |
| **FA1130114E** | 1.3.1 | 🟢 DOM | ✅ 新增 `tables/FA1130114E.py` — role=presentation/none 排版表格仍帶 th/caption/非空 summary → fail（與 HM1130107E 互補）|
| **HM2330800E** | 3.3.8 | 🟢 DOM | ✅ 新增 `forms/HM2330800E.py` — type=email/password 缺 autocomplete（未設/off）→ fail；與 HM2130500E（1.3.5 token 合法性）互補 |
| **FA2330801E** | 3.3.8/3.3.9 | 🟢 DOM | ✅ 新增 `forms/FA2330801E.py` — password/text 等以 inline onpaste 阻擋貼上 → fail（僅 inline handler）|

> tab_walk 擴充（FocusStop 加 outline 幾何 + bbox + obscured/obscured_fully）為單一 producer，自動流向 standalone + shared 兩路徑，**無新 ctx 欄位**（騎既有 `tab_stops` 通道）。reflow 則新增 `RuleContext.reflow` 欄位 — 屬真 state threading，已於 scanner 兩路徑（standalone L162 / shared L205）各自 populate 並用 localhost 固定寬頁 end-to-end 驗證兩路徑都觸發。

> 驗證：cheap-win 兩條（HM1130105C / ME1320200C）= auto-discovery 註冊 + 單元正反例 + 靜態 AAA 掃描無例外無誤報。focus 兩條（FA2241100E / CS3241301E）= 單元正反例 + scanner 兩路徑(L161/L201)透傳確認 + pytest 17 綠 + **light-design --render AAA dogfood 0 例外 0 誤報**。cheap-win `source="freego"`；focus rules `source="extension"`（E 碼）。

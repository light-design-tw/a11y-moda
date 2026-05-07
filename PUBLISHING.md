# Publishing `a11y-moda` to PyPI

完整步驟，從零到可被 `pip install a11y-moda`。**第一次走 0–5 全做，之後每次發版只跑步驟 5–7。**

---

## TL;DR (熟手版)

```bash
# 平常發版 (前提: trusted publisher 已設、CHANGELOG 已更新)
git tag v0.1.0
git push origin v0.1.0
# GitHub Actions 自動 build + 上 PyPI + 開 GitHub Release
```

---

## 0. 一次性帳號設定

### 0.1 PyPI / TestPyPI 帳號

1. 註冊 https://pypi.org/account/register/
2. 註冊 https://test.pypi.org/account/register/ (TestPyPI 是獨立帳號系統)
3. 兩邊都開 2FA (PyPI 強制要求)

### 0.2 確認 package 名稱可用

開 https://pypi.org/project/a11y-moda/ → 404 = 可註冊。已被搶 = 改名 (例如 `moda-a11y` / `a11y-moda-cli`)。

### 0.3 (建議) 申請 PyPI Trusted Publisher

走 OIDC，不需要存 API token 在 GitHub Secrets。

**PyPI 端**：https://pypi.org/manage/account/publishing/ → Add a new pending publisher

| 欄位 | 值 |
|---|---|
| PyPI Project Name | `a11y-moda` |
| Owner | `light-design-tw` (或你的 GitHub user/org) |
| Repository name | `a11y-moda` |
| Workflow name | `release.yml` |
| Environment name | `pypi` |

**TestPyPI 端**同樣設一份，environment 用 `testpypi`。

> 「Pending publisher」表示 project 還沒上 PyPI。第一次發版上去後會自動轉成正式 publisher。

### 0.4 GitHub repo 設 environment

GitHub repo → Settings → Environments → New environment

- 建 `pypi` 跟 `testpypi` 兩個 environment (名字必須跟 PyPI 端設的一致)
- `pypi` 建議勾「Required reviewers」(自己當 reviewer)，避免誤觸發 push 真 PyPI

---

## 1. 本地 build + 驗證 (上 PyPI 前必跑)

```bash
cd a11y_moda
pip install --upgrade build twine
python -m build              # 產 dist/a11y-moda-0.1.0.tar.gz + .whl
twine check dist/*           # 驗 README markdown 渲染、metadata 完整性
```

`twine check` 出 `PASSED` 才繼續。常見 fail：

- `Long description does not contain a body` → README.md 開頭有 BOM 或編碼錯
- `unrecognized field` → pyproject.toml metadata key 拼錯
- `link to nonexistent` → README 相對連結 (已修)

### 1.1 解開 wheel 看內容

```bash
python -m zipfile -l dist/a11y_moda-0.1.0-py3-none-any.whl
```

確認：
- `a11y_moda/cli.py` `rules/codes/...` 都有 (143 個 rule 檔)
- 沒帶 `__pycache__` / `.pyc`
- 沒帶 `tests/` `reports/` 之類雜物

---

## 2. 上 TestPyPI 試一次 (強烈建議)

```bash
twine upload --repository testpypi dist/*
# Username: __token__
# Password: <TestPyPI API token, pypi-...>
```

裝起來測：

```bash
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            a11y-moda
a11y-moda scan https://example.com --level AA
```

`--extra-index-url` 必加，不然依賴 (httpx / playwright) 在 TestPyPI 找不到會炸。

開 https://test.pypi.org/project/a11y-moda/ 肉眼確認：

- README 渲染正常 (中文不亂碼、表格完整、連結點得開)
- License = MIT
- Classifiers / keywords 出現
- 左側 sidebar 三條 URL (Homepage / Issues / Documentation) 都點得開

不滿意 → 改 → bump 版本 (`0.1.0a1` → `0.1.0a2`)，TestPyPI 同版號不能覆蓋上傳。

---

## 3. 設 GitHub Actions release workflow

存到 `.github/workflows/release.yml`：

```yaml
name: Release

on:
  push:
    tags:
      - "v*.*.*"

jobs:
  build:
    name: Build distribution
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Build sdist + wheel
        run: |
          pip install --upgrade build twine
          python -m build
          twine check dist/*
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  publish-pypi:
    name: Publish to PyPI
    needs: build
    runs-on: ubuntu-latest
    environment: pypi               # 對應 PyPI Trusted Publisher 設定
    permissions:
      id-token: write               # OIDC 必要
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      - uses: pypa/gh-action-pypi-publish@release/v1
        # 不用填 username/password — OIDC 自動換 token

  github-release:
    name: Create GitHub Release
    needs: publish-pypi
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      - name: Extract changelog section
        id: changelog
        run: |
          version="${GITHUB_REF_NAME#v}"
          awk "/^## \[${version}\]/{flag=1; next} /^## \[/{flag=0} flag" CHANGELOG.md > release_notes.md
      - uses: softprops/action-gh-release@v2
        with:
          body_path: release_notes.md
          files: dist/*
          generate_release_notes: false   # 用 CHANGELOG 內容，不要 GitHub 自動 generate
```

> **repo 結構提醒**：a11y-moda repo (準備拆出去發 MIT) 是獨立 git，`.github/workflows/` 放在那 repo 根目錄。**不是** monorepo `freego_cli/.github/workflows/`。

---

## 4. (可選) TestPyPI 自動化 workflow

`release-test.yml`：每次 push `main` 或 PR 到 `main` 都打 TestPyPI，driver 用 `0.1.0.devN` 版號 (N = run number)：

```yaml
on:
  push:
    branches: [main]

jobs:
  publish-test:
    runs-on: ubuntu-latest
    environment: testpypi
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - name: Inject dev version
        run: |
          sed -i "s/^version = .*/version = \"0.1.0.dev${{ github.run_number }}\"/" pyproject.toml
      - run: pip install build && python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
        with:
          repository-url: https://test.pypi.org/legacy/
```

選擇性。每 push 一個 dev 版上 TestPyPI，方便外部測試者 `pip install --pre a11y-moda --index-url https://test.pypi.org/simple/`。

---

## 5. 發版流程 (每次)

```bash
# 1. 確認 main 乾淨、CI 綠
git status
git pull

# 2. 更新 CHANGELOG.md：把 [Unreleased] 內容移到新版本標題下，加日期
$EDITOR CHANGELOG.md

# 3. bump 版號 (pyproject.toml + CHANGELOG.md 對齊)
$EDITOR pyproject.toml          # version = "0.2.0"

# 4. commit + tag
git add pyproject.toml CHANGELOG.md
git commit -m "chore(release): v0.2.0"
git tag v0.2.0
git push origin main v0.2.0     # tag push 觸發 release.yml
```

**等 GitHub Actions 跑完** (~3 分鐘)：

1. Build job → 產 dist
2. Publish to PyPI job → **環境會卡住等 reviewer approve** (如果有設 required reviewer) → 你去 GitHub Actions UI 按 Approve
3. PyPI 收到後立即生效，`pip install a11y-moda==0.2.0` 馬上可裝
4. GitHub Release 自動產，附 sdist + wheel

---

## 6. 發版後驗證

```bash
# 開新 venv，避免 cache 假象
python -m venv /tmp/verify && source /tmp/verify/bin/activate
pip install a11y-moda==0.2.0
a11y-moda --version             # 確認 entry point 對
a11y-moda scan https://example.com --level AA
```

PyPI 頁面 https://pypi.org/project/a11y-moda/ 確認：
- 新版號標 Latest
- Release history 多一筆
- Documentation / Changelog URL 點得開 (Changelog 應跳到新版區塊)

---

## 7. 撤回 / 修補

PyPI **不允許覆蓋同版號**。錯版本只能：

- **yank**：https://pypi.org/manage/project/a11y-moda/release/0.2.0/ → 「Yank release」。已裝的人不影響，但 `pip install a11y-moda` 不會挑到 yanked 版
- **發 patch 版**：`0.2.1` 修掉問題重發

`pip install` 短時間內可能還會選到舊快取，等 ~5 分鐘 PyPI CDN 同步。

---

## 常見地雷

| 症狀 | 原因 / 修法 |
|---|---|
| `HTTPError: 403 Invalid or non-existent authentication` | PyPI Trusted Publisher 沒設好 / environment 名稱不對 / `id-token: write` permission 沒加 |
| `File already exists` | 同版號重傳。bump 版號 |
| README 在 PyPI 顯示 raw markdown | `pyproject.toml` 沒 `readme = "README.md"`，或 README 開頭有 BOM |
| `pip install` 後跑 `--render` 噴 `Executable doesn't exist` | 已加 friendly error。使用者照提示跑 `playwright install chromium` |
| Wheel 裡面少 rule 檔 | `[tool.setuptools.packages.find]` 沒抓到。檢查 `where = ["src"]` 跟 src layout |
| 中文 description 在 PyPI 搜尋搜不到 | 正常。PyPI search 對 CJK 支援差。用英文 keywords + classifier 補 |

---

## 參考

- PyPA Trusted Publisher: https://docs.pypi.org/trusted-publishers/
- `pypa/gh-action-pypi-publish`: https://github.com/pypa/gh-action-pypi-publish
- Keep a Changelog: https://keepachangelog.com/
- PEP 639 (License metadata): https://peps.python.org/pep-0639/

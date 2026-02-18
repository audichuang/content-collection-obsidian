---
name: content-collection
description: "Save URLs, articles, tweets, and text snippets to Obsidian vault via Fast Note Sync. Use when user shares a link, asks to save/collect/bookmark content. Trigger keywords: 收藏, 存起來, save, bookmark, collect, 幫我記, 加入收藏."
---

# Content Collection — 內容收藏到 Obsidian

將 URL、文章、推文或文字片段儲存為 Obsidian Markdown 筆記。

## 環境設定

> **Doppler 配置**: 所有腳本需加前綴 `doppler run -p finviz -c dev --`

| 環境變數 | 說明 |
|----------|------|
| `FAST_NOTE_URL` | Fast Note Sync 伺服器 URL |
| `FAST_NOTE_TOKEN` | API Token |
| `FAST_NOTE_VAULT` | Vault 名稱 |

## 分類

可用分類（依內容選擇最合適的一個）：

`Article` · `Video` · `Tweet` · `Tutorial` · `Resource` · `Personal` · `Other`

## 網站類型判斷

**直接儲存連結**（純文字 HTTP 可抓取）：

* GitHub、Medium、Blog、新聞網站、YouTube、Twitter/X 等

**必須用瀏覽器擷取內容**（JS 動態渲染，HTTP 抓不到正文）：

* `xiaohongshu.com`、`xhslink.com`（小紅書）
* 其他開啟後頁面是空白或需登入才能看到內容的網站

## 瀏覽器擷取模式（小紅書等 JS 網站）

當 URL 屬於需要瀏覽器擷取的網站時，**在呼叫 save\_collection.py 之前**，先完成以下步驟：

### 步驟 1：開啟瀏覽器並導航

使用 browser tool，指定 profile `openclaw`，開啟目標 URL：

* action: `start`，profile: `openclaw`
* action: `navigate`，url: `<目標URL>`

### 步驟 2：等待並取得內容

頁面載入後：

* action: `snapshot`（取得 ARIA 內容樹，包含標題、正文、作者、標籤）
* 若內容不完整，可用 action: `act`，method: `scroll` 向下捲動後再次 snapshot

### 步驟 3：萃取關鍵內容

從 snapshot 中整理：

* **標題**：筆記的文章標題（50 字元以內）
* **作者**：發文者名稱（若有）
* **正文**：主要文字內容
* **標籤**：頁面上的 hashtag 或分類標籤

### 步驟 4：組裝 `--content` 參數

將萃取內容格式化為可讀文字傳入腳本，例如：

```
作者：@作者名稱

正文內容...（完整貼入）

標籤：標籤1 標籤2

來源：https://xiaohongshu.com/...
```

> **重點**：`--content` 要包含完整正文，讓 Obsidian 筆記有實際可讀內容，而不只是 URL。

## 工作流程

### 1. 收到內容

使用者分享 URL 或文字 → 判斷是否需要瀏覽器擷取（見上方「網站類型判斷」）。

**標題規則**：

* 中文或英文，視內容語言而定
* 50 字元以內
* 簡潔描述內容主題

**分類規則**：

* URL 含 twitter.com/x.com → `Tweet`
* YouTube/Bilibili 連結 → `Video`
* xiaohongshu.com/xhslink.com → `Article`（預設）
* 教學類內容 → `Tutorial`
* 其他依內容判斷

### 2. 儲存筆記

**一般網站**（直接儲存連結）：

```bash
doppler run -p finviz -c dev -- python3 ~/GoogleDrive/Github/skills/content-collection-obsidian/scripts/save_collection.py \
  --title "標題" \
  --category Article \
  --content "原始內容或 URL"
```

**小紅書等 JS 網站**（先擷取內容，再儲存）：

先完成「瀏覽器擷取模式」步驟，取得正文後：

```bash
doppler run -p finviz -c dev -- python3 ~/GoogleDrive/Github/skills/content-collection-obsidian/scripts/save_collection.py \
  --title "從頁面萃取的標題" \
  --category Article \
  --content "作者：@xxx

正文內容完整貼入...

標籤：xxx xxx

來源：https://xiaohongshu.com/..."
```

成功後腳本會輸出 `note_path`，你需要記住它（用於後續改分類）。

### 3. 回報結果

告訴使用者：

* ✅ 已收藏
* 標題和分類
* 若是瀏覽器擷取，簡短說明抓到的內容摘要
* 如需更改分類，告訴我分類名稱即可

### 4. 更改分類（可選）

使用者要求改分類時：

```bash
doppler run -p finviz -c dev -- python3 ~/GoogleDrive/Github/skills/content-collection-obsidian/scripts/update_category.py \
  --path "collections/2026-02-18-標題.md" \
  --category Tutorial
```

## 首次使用

首次使用技能時，先執行確保索引頁面存在：

```bash
doppler run -p finviz -c dev -- python3 ~/GoogleDrive/Github/skills/content-collection-obsidian/scripts/ensure_index.py
```

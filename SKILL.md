***

name: content-collection
description: "Save URLs, articles, tweets, and text snippets to Obsidian vault via Fast Note Sync. Use when user shares a link, asks to save/collect/bookmark content. Trigger keywords: 收藏, 存起來, save, bookmark, collect, 幫我記, 加入收藏."
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Content Collection — 內容收藏到 Obsidian

將 URL、文章、推文或文字片段儲存為 Obsidian Markdown 筆記。

> **這是編排技能**：協調 `saving-to-obsidian` 和 `uploading-to-minio` 原子技能完成收藏流程。

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

當 URL 屬於需要瀏覽器擷取的網站時，**在存入 Obsidian 之前**，先完成以下步驟：

### 步驟 1：開啟瀏覽器並導航

使用 browser tool，指定 profile `openclaw`，開啟目標 URL：

* action: `start`，profile: `openclaw`
* action: `navigate`，**targetUrl**: `<目標URL>`（注意：參數名稱是 `targetUrl`，不是 `url`）

### 步驟 2：處理登入彈窗

頁面載入後通常會出現「马上登录即可」登入提示彈窗（左側邊欄），處理方式：

1. 先嘗試 action: `press`，key: `Escape` 看能否關閉
2. 若仍存在，在 snapshot 中找彈窗的關閉按鈕（叉叉圖示，通常是 `img [cursor=pointer]` 位於彈窗旁邊）並 click
3. **若彈窗只佔左側欄但右側文章內容仍可見，可直接忽略彈窗，繼續進行擷取**——小紅書的登入牆通常不會完全遮蔽文章右側內容區塊

### 步驟 3：判斷貼文類型

取得 snapshot 後，判斷這是哪種貼文：

**A. 純文字貼文**：snapshot 中可以看到文章正文文字 → 直接從 snapshot 萃取內容

**B. 圖片型貼文**（小紅書最常見）：snapshot 中文章內容區只有 img 元素，找不到正文文字，且能看到投影片計數器如 `generic: 1/5` → 必須逐張截圖讀取

### 步驟 4A：純文字貼文 — 從 snapshot 萃取

從 snapshot 中整理：

* **標題**：筆記的文章標題（50 字元以內）
* **作者**：發文者名稱（若有）
* **正文**：主要文字內容
* **標籤**：頁面上的 hashtag 或分類標籤

### 步驟 4B：圖片型貼文 — 逐張截圖讀取

小紅書圖片貼文的文字印在圖片裡，ARIA snapshot 無法抓到，必須用視覺讀取每張截圖：

1. action: `screenshot` — 截第 1 張圖，用視覺讀取圖中文字
2. 在 snapshot 中找到「下一張」箭頭按鈕：位於投影片計數器（如 `generic: 1/5`）旁邊，通常是 `img [ref=eXXX] [cursor=pointer]`（計數器右側那個）
3. action: `click ref=eXXX` 切換到下一張
4. 重複截圖 + 點擊，直到計數器顯示最後一張（如 `5/5`）
5. 將所有圖片中讀取到的文字整合成完整內容

> **注意**：投影片區域通常有兩個箭頭按鈕（上一張/下一張），點擊計數器**右側**那個按鈕才是前進到下一張。

**截圖檔案規則**：

* browser tool 截圖會暫存於 `~/.openclaw/media/browser/<uuid>.png`（系統自動管理）
* **不要將截圖複製或移動到 `~/skills/` 下**
* 若要將圖片嵌入 Obsidian 筆記，使用 `uploading-to-minio` 技能上傳，再嵌入（見下方流程）

### 步驟 5：整理內容（摘要 + 結構化）

從截圖或 snapshot 中萃取內容後，必須整理成兩個部分：

**A. 摘要** —— 1-3 句話說明這篇的核心結論/要點：

* 「讀完學到什麼？」或「核心觀點是什麼？」

**B. 詳細內容** —— 結構化整理，不是逐張複述：

```
作者：@作者名稱

## 要點一：標題

說明文字...

## 要點二：標題

說明文字...

標籤：標籤1 標籤2
```

> **重點**：不要寫「第 1 張圖寫了 xxx、第 2 張圖寫了 xxx」，而是把所有圖片內容融合整理成有邏輯的篇章，用標題分節。

## 工作流程

### 1. 收到內容

使用者分享 URL 或文字 → 判斷是否需要瀏覽器擷取（見上方「網站類型判斷」）。

**標題規則**：中文或英文，視內容語言而定，50 字元以內，簡潔描述內容主題。

**分類規則**：

* URL 含 twitter.com/x.com → `Tweet`
* YouTube/Bilibili 連結 → `Video`
* xiaohongshu.com/xhslink.com → `Article`（預設）
* 教學類內容 → `Tutorial`
* 其他依內容判斷

### 2. 上傳圖片（如需要）

若有截圖需要嵌入筆記，先上傳到 MinIO：

```bash
doppler run -p minio -c dev -- python3 ~/skills/uploading-to-minio/scripts/upload_file.py \
  截圖1.png 截圖2.png --prefix "xiaohongshu/2026-02-19"
```

取得回傳的圖片 URL 備用。

### 3. 組裝 Markdown 並存入 Obsidian

用 AI 組裝完整的 Markdown 內容（含 YAML frontmatter），再呼叫 `saving-to-obsidian`：

**Markdown 格式**：

```markdown
---
title: "標題"
category: Article
date: YYYY-MM-DD
source: "https://example.com"
type: collection
---

> 摘要：核心要點 1-3 句話

## 要點一

詳細內容...

## 要點二

詳細內容...

![圖片 1](http://minio-url/img1.png)

---

來源：https://example.com
```

**存入命令**：

```bash
doppler run -p finviz -c dev -- python3 ~/skills/saving-to-obsidian/scripts/save_note.py \
  --content "組裝好的完整 Markdown" \
  --path "collections/YYYY-MM-DD-標題.md"
```

### 4. 回報結果

告訴使用者：

* ✅ 已收藏
* 標題和分類
* 若是瀏覽器擷取，簡短說明抓到的內容摘要
* 如需更改分類，告訴我分類名稱即可

### 5. 更改分類（可選）

使用者要求改分類時：

```bash
doppler run -p finviz -c dev -- python3 ~/skills/saving-to-obsidian/scripts/update_frontmatter.py \
  --path "collections/2026-02-18-標題.md" \
  --updates '{"category": "Tutorial"}'
```

## 首次使用

首次使用技能時，先建立索引頁面：

```bash
doppler run -p finviz -c dev -- python3 ~/skills/saving-to-obsidian/scripts/ensure_index.py --folder collections
```

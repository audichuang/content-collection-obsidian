***

name: content-collection
description: "Save URLs, articles, tweets, and text snippets to Obsidian vault via Fast Note Sync. Use when user shares a link, asks to save/collect/bookmark content. Trigger keywords: 收藏, 存起來, save, bookmark, collect, 幫我記, 加入收藏."
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Content Collection — 內容收藏到 Obsidian

將 URL、文章、推文或文字片段儲存為 Obsidian Markdown 筆記。

> **這是編排技能**：協調 `fetch-xiaohongshu`、`saving-to-obsidian` 和 `uploading-to-minio` 原子技能完成收藏流程。

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

當 URL 屬於需要瀏覽器擷取的網站時，**呼叫 `fetch-xiaohongshu` 原子技能**來完成內容與圖片擷取。

### 小節 A：呼叫 fetch-xiaohongshu（純資料擷取）

依照 `fetch-xiaohongshu` 技能說明執行，取得：

```json
{
  "title": "貼文標題",
  "author": "作者名稱",
  "desc": "貼文說明文字",
  "tags": ["標籤1", "標籤2"],
  "imageCount": 5,
  "images": ["http://minio/img1.webp", ...],
  "localFiles": ["/tmp/xhs_img_1.webp", ...]
}
```

> `fetch-xiaohongshu` 負責：開啟瀏覽器、登入處理、Canvas 圖片擷取、上傳 MinIO。**此技能不做任何內容解讀。**

### 小節 B：逐張視覺讀取圖片（此步驟在本 session 執行）

> ⚠️ **必須在本 agent session 親自執行，不可委派給 Bash subagent。**
> 原因：`Read` 工具讀取圖片需要 AI 的視覺能力（multimodal），Bash subagent 沒有。

對 `localFiles` 中的每個路徑，使用 `Read` 工具讀取：

```
Read /tmp/xhs_img_1.webp
Read /tmp/xhs_img_2.webp
...（共 imageCount 張）
```

讀取每張圖片後，記錄：
- 圖片中的主要文字、標題、條列重點
- 數據、圖表資訊
- 這張圖在貼文中的角色（封面、步驟 N、總結等）

### 小節 C：合成內容（摘要 + 結構化）

所有圖片讀取完成後，將 `desc` + 每張圖片的視覺內容整合：

**A. 摘要** —— 1-3 句話說明核心結論：

* 「讀完學到什麼？」或「核心觀點是什麼？」

**B. 詳細內容** —— 結構化整理，按主題分節（不是逐張複述）：

```
作者：@作者名稱

## 要點一：標題

說明文字...

## 要點二：標題

說明文字...

標籤：標籤1 標籤2
```

> `desc` 通常是概述，圖片才是詳細展開。若圖片有連續步驟（Step 1/2/3），保留邏輯順序。

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

* **小紅書**：`fetch-xiaohongshu` 已完成圖片擷取與上傳，直接使用回傳的 `images` URL 陣列。
* **其他網站有截圖需要嵌入**：

```bash
doppler run -p minio -c dev -- python3 ~/skills/uploading-to-minio/scripts/upload_file.py \
  截圖1.png 截圖2.png --prefix "collections/$(date +%Y-%m-%d)"
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

***

name: content-collection
description: "Save URLs, articles, tweets, and text snippets to Obsidian vault via Fast Note Sync. Use when user shares a link, asks to save/collect/bookmark content. Trigger keywords: 收藏, 存起來, save, bookmark, collect, 幫我記, 加入收藏."
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Content Collection — 內容收藏到 Obsidian

將 URL、文章、推文或文字片段儲存為 Obsidian Markdown 筆記。

> **這是編排技能**：協調 `fetch-xiaohongshu`、`uploading-to-minio`、`saving-to-obsidian` 原子技能完成收藏流程。

## 分類

可用分類（依內容選擇最合適的一個）：

`Article` · `Video` · `Tweet` · `Tutorial` · `Resource` · `Personal` · `Other`

## 網站類型判斷

**直接儲存連結**（純文字 HTTP 可抓取）：

* GitHub、Medium、Blog、新聞網站、YouTube、Twitter/X 等

**必須用瀏覽器擷取內容**（JS 動態渲染）：

* `xiaohongshu.com`、`xhslink.com`（小紅書）

---

## 小紅書工作流程

### A. 呼叫 fetch-xiaohongshu（純抓取）

依照 `fetch-xiaohongshu` 技能說明執行，取得：

```json
{
  "title": "貼文標題",
  "author": "作者名稱",
  "desc": "貼文說明文字",
  "tags": ["標籤1", "標籤2"],
  "imageCount": 5,
  "localFiles": ["/tmp/xhs_img_1.webp", "/tmp/xhs_img_2.webp", "..."]
}
```

> `fetch-xiaohongshu` 只負責抓取，**不讀圖、不上傳**。

### B. 逐張視覺讀取圖片

> ⚠️ **必須在本 agent session 執行，不可委派給 Bash subagent。**
> `Read` 工具讀取圖片需要 AI 視覺能力，Bash subagent 沒有。

對 `localFiles` 中每個路徑使用 `Read` 工具逐張讀取：

```
Read /tmp/xhs_img_1.webp  → 記錄圖片內容
Read /tmp/xhs_img_2.webp  → 記錄圖片內容
...（共 imageCount 張）
```

每張記錄：主要文字、標題、條列重點、數據圖表、在貼文中的角色。

### C. 合成完整內容

將 `desc` + 所有圖片視覺內容整合：

**摘要**：1-3 句話說明核心結論（「讀完學到什麼？」）

**詳細內容**（結構化，按主題分節，不逐張複述）：

```
作者：@作者名稱

## 要點一：標題
說明文字...

## 要點二：標題
說明文字...

標籤：標籤1 標籤2
```

### D. 上傳圖片到 MinIO

```bash
doppler run -p minio -c dev -- python3 ~/skills/uploading-to-minio/scripts/upload_file.py \
  /tmp/xhs_img_1.webp /tmp/xhs_img_2.webp ... \
  --prefix "xiaohongshu/$(date +%Y-%m-%d)"
```

取得回傳 JSON，提取每個物件的 `url` 欄位備用。

### E. 組裝 Markdown 並存入 Obsidian

組裝完整 Markdown（含 YAML frontmatter）：

```markdown
---
title: "標題"
category: Article
date: YYYY-MM-DD
source: "https://xhslink.com/..."
type: collection
---

> 摘要：核心要點 1-3 句話

作者：@作者名稱

## 要點一：標題

詳細內容...

## 要點二：標題

詳細內容...

![圖片 1](http://minio-url/img1.webp)
![圖片 2](http://minio-url/img2.webp)

---

來源：https://xhslink.com/...
```

存入命令：

```bash
doppler run -p finviz -c dev -- python3 ~/skills/saving-to-obsidian/scripts/save_note.py \
  --content "組裝好的完整 Markdown" \
  --path "collections/YYYY-MM-DD-標題.md"
```

---

## 一般網站工作流程

### 1. 收到內容

使用者分享 URL 或文字 → 判斷是否需要瀏覽器擷取。

**標題規則**：中文或英文，50 字元以內。

**分類規則**：

* URL 含 twitter.com/x.com → `Tweet`
* YouTube/Bilibili → `Video`
* xiaohongshu.com/xhslink.com → `Article`
* 教學類內容 → `Tutorial`
* 其他依內容判斷

### 2. 上傳圖片（如有截圖需嵌入）

```bash
doppler run -p minio -c dev -- python3 ~/skills/uploading-to-minio/scripts/upload_file.py \
  截圖.png --prefix "collections/$(date +%Y-%m-%d)"
```

### 3. 組裝 Markdown 並存入 Obsidian

同小紅書流程的步驟 E。

### 4. 回報結果

* ✅ 已收藏、標題、分類
* 若是瀏覽器擷取，簡短說明內容摘要
* 如需更改分類告知即可

### 5. 更改分類（可選）

```bash
doppler run -p finviz -c dev -- python3 ~/skills/saving-to-obsidian/scripts/update_frontmatter.py \
  --path "collections/2026-02-18-標題.md" \
  --updates '{"category": "Tutorial"}'
```

## 首次使用

```bash
doppler run -p finviz -c dev -- python3 ~/skills/saving-to-obsidian/scripts/ensure_index.py --folder collections
```

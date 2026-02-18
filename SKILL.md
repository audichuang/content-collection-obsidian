***

name: content-collection
description: "Save URLs, articles, tweets, and text snippets to Obsidian vault via Fast Note Sync. Use when user shares a link, asks to save/collect/bookmark content. Trigger keywords: 收藏, 存起來, save, bookmark, collect, 幫我記, 加入收藏."
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

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

## 工作流程

### 1. 收到內容

使用者分享 URL 或文字 → 你來判斷標題和分類。

**標題規則**：

* 中文或英文，視內容語言而定
* 50 字元以內
* 簡潔描述內容主題

**分類規則**：

* URL 含 twitter.com/x.com → `Tweet`
* YouTube/Bilibili 連結 → `Video`
* 教學類內容 → `Tutorial`
* 其他依內容判斷

### 2. 儲存筆記

```bash
doppler run -p finviz -c dev -- python3 ~/GoogleDrive/Github/skills/content-collection-obsidian/scripts/save_collection.py \
  --title "標題" \
  --category Article \
  --content "原始內容或 URL"
```

成功後腳本會輸出 `note_path`，你需要記住它（用於後續改分類）。

### 3. 回報結果

告訴使用者：

* ✅ 已收藏
* 標題和分類
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

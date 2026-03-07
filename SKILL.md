---
name: content-collection-obsidian
description: "當使用者要求收藏、整理外部內容（小紅書貼文、文章、推文、連結等）到 Obsidian 時使用此技能。善用 redbook CLI 擷取小紅書內容（含影片），用 Gemini API 分析影片重點，透過 saving-to-obsidian 腳本存入筆記。觸發關鍵字：收藏, 存起來, 整理貼文, 小紅書收藏, bookmark, collect, 加入收藏."
---

# Content Collection — 內容收藏到 Obsidian

將 URL、文章、推文或文字片段收藏為 Obsidian Markdown 筆記。

> **編排技能**：協調 `redbook` CLI、`saving-to-obsidian` 技能腳本（`upload_file.py` / `save_note.py` / `list_vault.py`）、`analyze_video.py` 完成收藏流程。
> **注意：`saving-to-obsidian` 是腳本工具，不是 MCP Server。**

## 收藏流程檢核表

### 小紅書內容

```
- [ ] 1. 確認來源為小紅書 URL（含 xsec_token）
- [ ] 2. redbook read --json <url> → 取得完整 JSON
- [ ] 3. 從 JSON 提取：title, desc, type, user.nickname, image_list, tag_list
- [ ] 4. 判斷 type：若為 "video" → 下載影片 + 執行步驟 6
- [ ] 5. 下載所有圖片：curl -o /tmp/xhs_img_N.webp <image_list[N].url_default>
- [ ] 6. 【影片限定】下載影片：curl -o /tmp/video.mp4 <video.media.stream 最高畫質 master_url>
- [ ] 7. 【影片限定】取得影片內容理解：doppler run -p api-key -c dev -- uv run ~/skills/content-collection-obsidian/scripts/analyze_video.py /tmp/video.mp4 → 閱讀輸出，理解影片內容
- [ ] 8. 上傳所有媒體到 Obsidian Vault（upload_file.py）
- [ ] 9. 整理重點：閱讀 desc 原文（影片類再加上步驟 7 的分析），用自己的話撰寫摘要與重點整理
- [ ] 10. 組裝 Markdown（套用下方模板）→ 存入 Obsidian（save_note.py）
- [ ] 11. 回報：✅ 標題 / 分類 / 路徑
```

### 一般網站

```
- [ ] 1. 確認來源類型（一般 URL / Twitter / YouTube 等）
- [ ] 2. HTTP 抓取或瀏覽器擷取內容
- [ ] 3. 整理內容 → 選擇分類 + 撰寫摘要（1-3 句）
- [ ] 4. 如有圖片需嵌入 → 下載並上傳到 Obsidian Vault
- [ ] 5. 組裝 Markdown（套用下方模板）→ 存入 Obsidian
- [ ] 6. 回報：✅ 標題 / 分類 / 路徑
```

## 分類規則

| 來源 | 分類 |
|------|------|
| 小紅書圖文 | `Article` |
| 小紅書/YouTube 影片 | `Video` |
| Twitter / X | `Tweet` |
| 教學類內容 | `Tutorial` |
| 其他依內容判斷 | `Resource` / `Personal` / `Other` |

收藏路徑：`collections/<Category>/YYYY-MM-DD-<標題>.md`

## 小紅書工作流程

### 步驟 1-3：用 redbook 擷取內容

```bash
# 取得完整 JSON（URL 必須帶 xsec_token，否則回傳空）
redbook read --json "https://www.xiaohongshu.com/explore/xxxxx?xsec_token=ABxxx"

# 瀏覽推薦列表（帶 xsec_token 的 URL 在搜尋結果中）
redbook feed --json
redbook search --json "關鍵字"
```

`redbook read --json` 回傳 JSON 結構：

| 欄位 | 說明 |
|------|------|
| `title` | 標題 |
| `desc` | 描述文字（主要內容） |
| `type` | `"normal"` = 圖文，`"video"` = 影片 |
| `user.nickname` | 作者名稱 |
| `image_list[]` | 圖片陣列，每張有 `url_default` |
| `tag_list[]` | 標籤陣列 |
| `video.media.stream` | 影片串流（`h264` / `h265`），每個含 `master_url`、`width`、`height`、`size` |
| `interact_info` | 互動數據：`liked_count`、`collected_count`、`comment_count` |

### 步驟 4-6：下載媒體

```bash
# 下載圖片（逐張）
curl -o /tmp/xhs_img_1.webp "image_list[0].url_default 的值"

# 下載影片（優先選 h265 最高畫質，即 stream_type 115）
curl -o /tmp/video.mp4 "video.media.stream.h265[最大 size].master_url"
```

### 步驟 7：取得影片內容理解（type == "video" 時必做）

> **此步驟的目的是讓你（AI agent）理解影片內容。**
> `analyze_video.py` 的輸出是你的**參考素材**，不是直接貼入筆記的內容。
> 你應該閱讀分析結果，理解影片在講什麼，然後在步驟 9 中**用自己的話整理重點**寫進文章。
>
> **圖文類也一樣**：閱讀 `desc` 原文後，在步驟 9 中用自己的話整理重點，不要只搬運原文。

```bash
doppler run -p api-key -c dev -- uv run \
  ~/skills/content-collection-obsidian/scripts/analyze_video.py \
  /tmp/video.mp4
```

> 自訂提示：加 `--prompt "列出影片中提到的所有工具和產品"`
> 換模型：加 `--model gemini-3-pro-preview`

### 步驟 8：上傳媒體到 Obsidian

使用 `saving-to-obsidian` 技能的 `upload_file.py`：

```bash
doppler run -p storage -c dev -- python3 \
  ~/skills/saving-to-obsidian/scripts/upload_file.py \
  /tmp/xhs_img_1.webp /tmp/video.mp4 \
  --prefix "assets/xiaohongshu/$(date +%Y-%m-%d)/<NOTE_ID>"
```

回傳 JSON 陣列，每個物件含 `path`（Obsidian 內路徑）。

### 步驟 9-10：組裝 Markdown 並存入

**嚴格使用以下模板**，將 `{{ }}` 替換為實際值。
**所有類型（圖文 / 影片）都必須有完整的摘要與重點整理。**

```markdown
---
title: "{{ title }}"
category: {{ Category }}
date: {{ YYYY-MM-DD }}
created: "{{ YYYY-MM-DD HH:mm:ss }}"
source: "{{ 原始 URL }}"
type: collection
author: "{{ user.nickname }}"
tags: [{{ tag_list 逗號分隔 }}]
---

> {{ 摘要：2-4 句核心要點，概述這篇內容在講什麼、為什麼值得收藏 }}

作者：@{{ user.nickname }}

## 重點整理

{{ 閱讀原文 desc（影片類再加上 analyze_video.py 的分析結果）後，用自己的話整理內容重點：
- 主題概述（1-2 句話說明核心主旨）
- 關鍵要點（條列式，3-7 點）
- 重要細節、數據或結論（如有）
不要照搬原文，要用自己的話重新組織。 }}

{{ 以下為影片內嵌（type == "video" 時才加） }}
![[{{ upload_file.py 回傳的影片 path }}]]

## 圖片

![[{{ upload_file.py 回傳的圖片 path 1 }}]]
![[{{ upload_file.py 回傳的圖片 path 2 }}]]

## 原文參考

{{ desc 完整描述文字，原封不動保留 }}

---

互動：❤️ {{ liked_count }} · ⭐ {{ collected_count }} · 💬 {{ comment_count }}
來源：{{ 原始 URL }}
```

存入 Obsidian：

```bash
doppler run -p storage -c dev -- python3 \
  ~/skills/saving-to-obsidian/scripts/save_note.py \
  --content "組裝好的完整 Markdown" \
  --path "collections/{{ Category }}/{{ YYYY-MM-DD }}-{{ title }}.md"
```

## 查詢 Vault 結構

```bash
doppler run -p storage -c dev -- python3 \
  ~/skills/saving-to-obsidian/scripts/list_vault.py --depth 2
```

## 注意事項

* `redbook read` 的 URL **必須帶 `xsec_token`**，否則回傳空 JSON。token 從 `redbook search/feed --json` 結果取得
* 影片類（`type == "video"`）**必須**用 `analyze_video.py` 產出 AI 摘要
* 圖片不需視覺讀取 — `redbook read --json` 的 `desc` 已包含所有文字資訊
* 影片下載優先選 h265 最高畫質（`stream_type 115`），若無則選 h264
* 所有腳本路徑都在 `~/skills/` 下，用 `doppler run` 注入環境變數

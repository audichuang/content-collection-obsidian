# Content Collection Obsidian — OpenClaw Skill

將 URL、文章、推文或文字片段收藏為 Obsidian Markdown 筆記的 OpenClaw 技能。

## 架構

本 SKILL 是純編排技能，不含自有腳本。協調以下原子技能完成收藏流程：

| 原子技能 | 職責 |
|----------|------|
| `fetch-xiaohongshu` | 瀏覽器擷取小紅書貼文內容與圖片 |
| `uploading-to-minio` | 圖片上傳至 MinIO 物件儲存 |
| `saving-to-obsidian` | Markdown 筆記寫入 Obsidian |

## 使用方式

在 Telegram/WhatsApp 中直接對 OpenClaw 發送 URL 或說「幫我收藏」。

## 環境變數（透過 Doppler）

| 變數 | 說明 |
|------|------|
| `FAST_NOTE_URL` | Fast Note Sync 伺服器 URL |
| `FAST_NOTE_TOKEN` | API Token |
| `FAST_NOTE_VAULT` | Vault 名稱 |

## Obsidian 設定

需安裝 [Dataview](https://github.com/blacksmithgu/obsidian-dataview) 插件以顯示索引頁面的表格視圖。

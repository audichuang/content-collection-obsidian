# Content Collection Obsidian — OpenClaw Skill

將 URL、文章、推文或文字片段收藏為 Obsidian Markdown 筆記的 OpenClaw 技能。

## 架構

```
SKILL.md                ← Agent 指引
scripts/
├── save_collection.py  ← 儲存筆記 (POST /api/note)
├── update_category.py  ← 更改分類 (PATCH /api/note/frontmatter)
└── ensure_index.py     ← 建立 Dataview 索引頁
```

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

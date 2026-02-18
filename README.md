# Content Collection Bot (Obsidian)

Save links and notes to Obsidian via Telegram. Send a URL or text, and the bot uses Claude AI to generate a title, pick a category, and save it to your Obsidian vault via [Fast Note Sync](https://github.com/haierkeys/fast-note-sync-service).

## Features

* Send a URL — auto-generates a title and category, saves to Obsidian
* Send text + URL — uses your text as the title
* Send plain text — saves it as a note with AI-generated title
* Reply with a number — quickly change the category
* Auto-creates a Dataview table page for browsing all saved items
* Special support for Twitter/X links

## How It Works

```
User sends Telegram message
         │
         ▼
  ┌─────────────┐
  │  Claude AI   │  ← generates title & category
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  Fast Note   │  ← saves .md file with YAML frontmatter
  │  Sync API    │
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  Obsidian    │  ← Dataview renders the table view
  │  Vault       │
  └─────────────┘
```

Each saved item becomes a Markdown file:

```markdown
---
title: "Claude Code 開源 AI 編碼工具"
category: Article
date: 2026-02-18
source: "https://github.com/anthropics/claude-code"
type: collection
---

https://github.com/anthropics/claude-code
```

Browse all items in Obsidian via the auto-generated `_index.md` Dataview table.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot token from @BotFather |
| `ANTHROPIC_API_KEY` | Claude API key |
| `FAST_NOTE_URL` | Fast Note Sync server URL |
| `FAST_NOTE_TOKEN` | Fast Note Sync API token |
| `FAST_NOTE_VAULT` | Vault name (default: `Obsidian`) |
| `CATEGORIES` | Comma-separated categories (default: `Article,Video,Tweet,Tutorial,Resource,Personal,Other`) |
| `NOTE_FOLDER` | Folder in vault (default: `collections`) |

## Deploy

1. Set up environment variables (e.g., via Railway, Doppler, or `.env`)
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python bot.py`

For Railway deployment, the included `Procfile` and `runtime.txt` handle configuration automatically.

## Prerequisites

* [Fast Note Sync](https://github.com/haierkeys/fast-note-sync-service) server running
* [Obsidian Fast Note Sync Plugin](https://github.com/haierkeys/obsidian-fast-note-sync) installed
* [Dataview](https://github.com/blacksmithgu/obsidian-dataview) plugin installed in Obsidian

## Credits

Inspired by [content-collection-skill](https://github.com/ccccccarachen/content-collection-skill) (Notion version).

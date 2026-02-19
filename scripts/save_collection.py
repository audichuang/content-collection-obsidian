#!/usr/bin/env python3
"""
save_collection.py — 儲存收藏筆記到 Obsidian via Fast Note Sync

環境變數（由 doppler 注入）:
  FAST_NOTE_URL    — 伺服器 URL
  FAST_NOTE_TOKEN  — API Token
  FAST_NOTE_VAULT  — Vault 名稱

用法:
  doppler run -p finviz -c dev -- python3 scripts/save_collection.py \
    --title "文章標題" --category Article --content "https://example.com"

  # 完整格式（含摘要、圖片、來源）:
  doppler run -p finviz -c dev -- python3 scripts/save_collection.py \
    --title "標題" --category Article \
    --summary "這篇文章的核心要點..." \
    --content "詳細內容" \
    --images "url1,url2" \
    --source "https://example.com"
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone


def api_request(method: str, endpoint: str, data: dict) -> dict:
    """呼叫 Fast Note Sync REST API"""
    base_url = os.environ["FAST_NOTE_URL"].rstrip("/")
    token = os.environ["FAST_NOTE_TOKEN"]

    url = f"{base_url}/api{endpoint}"
    payload = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        method=method,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
    )

    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description="儲存收藏筆記到 Obsidian")
    parser.add_argument("--title", "-t", required=True, help="筆記標題")
    parser.add_argument("--category", "-c", required=True, help="分類")
    parser.add_argument("--summary", "-s", default="", help="摘要（1-3 句話說明核心要點）")
    parser.add_argument("--content", required=True, help="詳細內容")
    parser.add_argument("--images", default="", help="圖片 URL，多張用逗號分隔")
    parser.add_argument("--source", default="", help="原始來源 URL")
    parser.add_argument("--folder", default="collections", help="Vault 內的資料夾 (預設: collections)")
    args = parser.parse_args()

    # 檢查環境變數
    for var in ("FAST_NOTE_URL", "FAST_NOTE_TOKEN", "FAST_NOTE_VAULT"):
        if not os.environ.get(var):
            print(f"錯誤: 需要設定 {var}", file=sys.stderr)
            sys.exit(1)

    vault = os.environ["FAST_NOTE_VAULT"]

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")

    # 清理標題作為檔名
    safe_title = re.sub(r'[\\/*?:"<>|]', "", args.title)[:60].strip()
    note_path = f"{args.folder}/{date_str}-{safe_title}.md"

    # 判斷是否為 URL
    content = args.content.strip()
    source = args.source.strip() if args.source else ""

    # 如果 content 本身就是 URL 且沒有指定 --source，自動當作 source
    is_url = bool(re.match(r"https?://", content))
    if is_url and not source:
        source = content

    # 組裝 YAML frontmatter
    fm = [
        "---",
        f'title: "{args.title}"',
        f"category: {args.category}",
        f"date: {date_str}",
    ]
    if source:
        fm.append(f'source: "{source}"')
    fm += ["type: collection", "---"]

    # 組裝內文：摘要 → 詳細內容 → 圖片 → 來源
    body_parts = []

    # 1. 摘要
    if args.summary:
        body_parts.append("> " + args.summary.replace("\n", "\n> "))
        body_parts.append("")

    # 2. 詳細內容（如果 content 不是單純的 URL）
    if not is_url or source != content:
        body_parts.append(content)
        body_parts.append("")

    # 3. 嵌入圖片
    image_urls = [u.strip() for u in args.images.split(",") if u.strip()] if args.images else []
    if image_urls:
        for i, url in enumerate(image_urls, 1):
            body_parts.append(f"![圖片 {i}]({url})")
            body_parts.append("")

    # 4. 來源
    if source:
        body_parts.append(f"---\n\n來源：{source}")
        body_parts.append("")

    md_content = "\n".join(fm) + "\n\n" + "\n".join(body_parts) + "\n"

    try:
        result = api_request("POST", "/note", {
            "vault": vault,
            "path": note_path,
            "content": md_content,
        })
        data = result.get("data", {})
        # 輸出 JSON 供 Agent 解析
        print(json.dumps({
            "success": True,
            "note_path": note_path,
            "title": args.title,
            "category": args.category,
            "date": date_str,
            "version": data.get("version", "?"),
        }))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(json.dumps({"success": False, "error": f"HTTP {e.code}: {body}"}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()

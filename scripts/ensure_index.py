#!/usr/bin/env python3
"""
ensure_index.py — 確保 Dataview 索引頁面存在

在 collections/ 資料夾建立 _index.md，包含 Dataview 查詢，
用表格方式呈現所有收藏筆記。

用法:
  doppler run -p finviz -c dev -- python3 scripts/ensure_index.py
"""

import json
import os
import sys
import urllib.request
import urllib.error


INDEX_CONTENT = """---
title: Collections Index
type: index
---

# 📚 Content Collections

```dataview
TABLE category AS "分類", date AS "日期", source AS "來源"
FROM "collections"
WHERE type = "collection"
SORT date DESC
```
"""


def main():
    for var in ("FAST_NOTE_URL", "FAST_NOTE_TOKEN", "FAST_NOTE_VAULT"):
        if not os.environ.get(var):
            print(f"錯誤: 需要設定 {var}", file=sys.stderr)
            sys.exit(1)

    base_url = os.environ["FAST_NOTE_URL"].rstrip("/")
    token = os.environ["FAST_NOTE_TOKEN"]
    vault = os.environ["FAST_NOTE_VAULT"]
    folder = os.environ.get("NOTE_FOLDER", "collections")

    url = f"{base_url}/api/note"
    payload = json.dumps({
        "vault": vault,
        "path": f"{folder}/_index.md",
        "content": INDEX_CONTENT.strip() + "\n",
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
    )

    try:
        with urllib.request.urlopen(req) as resp:
            json.loads(resp.read().decode("utf-8"))
            print("✅ 索引頁面已建立/更新: {folder}/_index.md".format(folder=folder))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"❌ HTTP {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

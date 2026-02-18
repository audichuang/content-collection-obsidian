#!/usr/bin/env python3
"""
update_category.py — 更新收藏筆記的分類 via Fast Note Sync

使用 PATCH /api/note/frontmatter 直接修改 frontmatter，
不需要重新上傳整篇內容。

用法:
  doppler run -p finviz -c dev -- python3 scripts/update_category.py \
    --path "collections/2026-02-18-標題.md" --category Tutorial
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error


def main():
    parser = argparse.ArgumentParser(description="更新筆記分類")
    parser.add_argument("--path", "-p", required=True, help="Vault 內的筆記路徑")
    parser.add_argument("--category", "-c", required=True, help="新分類")
    args = parser.parse_args()

    for var in ("FAST_NOTE_URL", "FAST_NOTE_TOKEN", "FAST_NOTE_VAULT"):
        if not os.environ.get(var):
            print(f"錯誤: 需要設定 {var}", file=sys.stderr)
            sys.exit(1)

    base_url = os.environ["FAST_NOTE_URL"].rstrip("/")
    token = os.environ["FAST_NOTE_TOKEN"]
    vault = os.environ["FAST_NOTE_VAULT"]

    url = f"{base_url}/api/note/frontmatter"
    payload = json.dumps({
        "vault": vault,
        "path": args.path,
        "updates": {"category": args.category},
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        method="PATCH",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            print(json.dumps({
                "success": True,
                "path": args.path,
                "new_category": args.category,
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

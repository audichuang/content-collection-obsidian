#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["google-genai"]
# ///
"""
analyze_video.py — 用 Gemini API 分析影片內容

環境變數（由 Doppler 注入）:
  GOOGLE_API_KEY — Gemini API Key

用法:
  doppler run -p api-key -c dev -- uv run analyze_video.py /path/to/video.mp4
  doppler run -p api-key -c dev -- uv run analyze_video.py /path/to/video.mp4 --json
  doppler run -p api-key -c dev -- uv run analyze_video.py /path/to/video.mp4 --prompt "列出影片中提到的所有工具"
  doppler run -p api-key -c dev -- uv run analyze_video.py /path/to/video.mp4 --model gemini-3-pro-preview
"""

import argparse
import json
import os
import sys
import time

from google import genai


def main():
    parser = argparse.ArgumentParser(
        description="用 Gemini API 分析影片內容，輸出中文摘要"
    )
    parser.add_argument("video", help="影片檔案路徑（mp4 等）")
    parser.add_argument(
        "--prompt",
        default="請用繁體中文詳細摘要這支影片的重點內容，包含：\n1. 主題概述（1-2 句話）\n2. 關鍵要點（條列式）\n3. 重要細節或數據",
        help="自訂分析提示（預設：中文摘要）",
    )
    parser.add_argument(
        "--model",
        default="gemini-3-flash-preview",
        help="Gemini 模型名稱（預設: gemini-3-flash-preview）",
    )
    parser.add_argument("--json", action="store_true", dest="json_output", help="以 JSON 格式輸出")
    args = parser.parse_args()

    # 驗證影片檔案
    if not os.path.isfile(args.video):
        print(f"錯誤：找不到檔案 {args.video}", file=sys.stderr)
        sys.exit(1)

    # 取得 API key（由 Doppler 注入）
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("錯誤：請用 doppler run -p api-key -c dev -- 執行此腳本", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # 上傳影片到 Gemini File API
    file_size = os.path.getsize(args.video)
    print(f"上傳影片中... ({file_size / 1024 / 1024:.1f} MB)", file=sys.stderr)

    uploaded = client.files.upload(file=args.video)
    print(f"上傳完成: {uploaded.name}", file=sys.stderr)

    # 等待檔案處理完成（影片需要轉碼）
    file_ref = uploaded
    while file_ref.state and file_ref.state.name == "PROCESSING":
        print("等待影片處理中...", file=sys.stderr)
        time.sleep(3)
        file_ref = client.files.get(name=uploaded.name)

    if file_ref.state and file_ref.state.name != "ACTIVE":
        print(f"錯誤：檔案處理失敗，狀態: {file_ref.state}", file=sys.stderr)
        sys.exit(1)

    print("檔案已就緒", file=sys.stderr)

    # 分析影片
    print(f"分析中（模型: {args.model}）...", file=sys.stderr)
    response = client.models.generate_content(
        model=args.model,
        contents=[file_ref, args.prompt],
    )

    text = response.text

    # 輸出
    if args.json_output:
        result = {
            "model": args.model,
            "video": os.path.basename(args.video),
            "video_size_mb": round(file_size / 1024 / 1024, 2),
            "analysis": text,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(text)

    # 清理上傳的檔案
    try:
        client.files.delete(name=uploaded.name)
        print("已清理上傳的暫存檔案", file=sys.stderr)
    except Exception:
        pass


if __name__ == "__main__":
    main()

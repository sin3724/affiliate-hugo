#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv, os, re, sys
from pathlib import Path
from datetime import datetime

CSV_PATH = "materials_fc2.csv"   # --csv で上書き可
OUT_DIR  = "content/posts"       # --out で上書き可

ARTICLE_ID_RE = re.compile(r"/article/(\d+)/")

def get_arg(opt, default):
    if opt in sys.argv:
        i = sys.argv.index(opt)
        if i+1 < len(sys.argv):
            return sys.argv[i+1]
    return default

def safe_filename(s: str) -> str:
    s = re.sub(r'[\\/:*?"<>|]', "-", s)
    s = re.sub(r"\s+", "-", s).strip("-")
    return s[:80] if len(s) > 80 else s

def extract_article_id(url: str) -> str:
    m = ARTICLE_ID_RE.search(url or "")
    return m.group(1) if m else ""

def yaml_quote(s: str) -> str:
    # YAML用にダブルクォートをエスケープ
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'

def build_body_md(title, thumbnail, aff_url):
    parts = []
    if thumbnail:
        parts.append(f"[![{title}]({thumbnail})]({aff_url})\n")
    parts.append(f"[▶︎ 動画を見る]({aff_url})")
    return "\n".join(parts) + "\n"

def main():
    csv_path = Path(get_arg("--csv", CSV_PATH))
    out_dir  = Path(get_arg("--out", OUT_DIR))
    limit    = int(get_arg("--limit", "0"))  # 0=制限なし

    if not csv_path.exists():
        print("CSV not found:", csv_path)
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)

    n = 0
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title      = (row.get("title") or "").strip()
            thumbnail  = (row.get("thumbnail") or "").strip()
            product    = (row.get("product_url") or "").strip()
            aff_url    = (row.get("aff_url") or row.get("detail_url") or product).strip()

            if not title or not product:
                continue

            aid = extract_article_id(product)
            base_name = f"fc2-{aid}" if aid else safe_filename(title)
            md_path = out_dir / f"{base_name}.md"

            fm = []
            fm.append("---")
            fm.append("title: " + yaml_quote(title))
            fm.append("date: " + datetime.now().strftime('%Y-%m-%dT%H:%M:%S+09:00'))
            fm.append("draft: false")
            if thumbnail:
                fm.append("thumbnail: " + yaml_quote(thumbnail))
            fm.append("product_url: " + yaml_quote(product))
            fm.append("aff_url: " + yaml_quote(aff_url))
            fm.append("tags: [FC2, 収集]")
            fm.append("---\n")

            body = build_body_md(title, thumbnail, aff_url)

            with md_path.open("w", encoding="utf-8") as out:
                out.write("\n".join(fm))
                out.write(body)

            n += 1
            print("[OK]", md_path)
            if limit and n >= limit:
                break

    print(f"✅ 生成完了: {n} files -> {out_dir}")

if __name__ == "__main__":
    main()

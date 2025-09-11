#!/usr/bin/env bash
set -u
IMG_DIR="static/img"
made=0
while IFS= read -r -d '' f; do
  w="${f%.*}.webp"
  [ -f "$w" ] && continue
  if command -v cwebp >/dev/null 2>&1; then
    cwebp -q 80 "$f" -o "$w" >/dev/null 2>&1 || true
    [ -f "$w" ] && made=$((made+1))
  else
    echo "cwebp が見つかりません。`brew install webp` を実行してください。"
    exit 1
  fi
done < <(find "$IMG_DIR" -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) -print0)
echo "[DONE] created $made webp files"

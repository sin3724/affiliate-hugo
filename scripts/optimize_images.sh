#!/usr/bin/env bash
set -euo pipefail
IMG_DIR="static/img"

# JPEG最適化（可逆に近い軽量圧縮）
find "$IMG_DIR" -type f \( -iname '*.jpg' -o -iname '*.jpeg' \) -print0 \
 | xargs -0 -I{} jpegoptim --strip-all --all-progressive --max=82 "{}"

# PNG最適化
find "$IMG_DIR" -type f -iname '*.png' -print0 \
 | xargs -0 -I{} pngquant --skip-if-larger --force --ext .png "{}"

# EXIF除去（念のため）
find "$IMG_DIR" -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) -print0 \
 | xargs -0 -I{} exiftool -overwrite_original -all= "{}"

# WebP化（既にあるものはスキップ）
while IFS= read -r -d '' f; do
  w="${f%.*}.webp"
  [ -f "$w" ] && continue
  cwebp -q 80 "$f" -o "$w" >/dev/null 2>&1 || true
done < <(find "$IMG_DIR" -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) -print0)

echo "[DONE] optimize -> $(date)"

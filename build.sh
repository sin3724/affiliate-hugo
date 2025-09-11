#!/usr/bin/env bash
set -euo pipefail
echo "[1/3] Generate posts (skip if not needed)"
if [ -f scripts/generate_posts.py ]; then
  python scripts/generate_posts.py
else
  echo "  (generate_posts.py なし → スキップ)"
fi
echo "[2/3] Hugo build"
hugo --minify
echo "[3/3] Build artifacts"
du -sh public || true

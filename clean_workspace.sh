#!/usr/bin/env bash
# clean_pycache.sh — remove Python bytecode caches in ./src
set -euo pipefail

ROOT="${1:-./src}"

if [[ ! -d "$ROOT" ]]; then
  echo "Directory not found: $ROOT" >&2
  exit 1
fi

echo "Removing __pycache__ directories under $ROOT..."
find "$ROOT" -type d -name "__pycache__" -print -exec rm -rf {} +

echo "Removing *.pyc and *.pyo files under $ROOT..."
find "$ROOT" -type f \( -name "*.pyc" -o -name "*.pyo" \) -print -delete

echo "Done."
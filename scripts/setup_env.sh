#!/usr/bin/env bash
# Create a Python venv with Manim + font tools in the given work dir (default: current dir).
# Needs: uv (or python3 -m venv), ffmpeg, cairo + pango (brew install cairo pango pkg-config). No LaTeX needed.
set -euo pipefail
WD="${1:-.}"
cd "$WD"
if command -v uv >/dev/null; then
  uv venv -q --python 3.12 .venv
  uv pip install -q --python .venv/bin/python manim fonttools brotli numpy pillow
else
  python3 -m venv .venv && .venv/bin/pip install -q manim fonttools brotli numpy pillow
fi
.venv/bin/manim --version
command -v ffmpeg >/dev/null || echo "WARNING: ffmpeg missing (brew install ffmpeg)"

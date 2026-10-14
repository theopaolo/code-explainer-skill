#!/usr/bin/env python3
"""Build the publishable page from the site source.

Usage:
  python build_site.py site/index.src.html --out site/explainer.html \
      [--font 400=path/Regular.woff2 --font 600=path/Semibold.woff2 --font-family "SNPro"] \
      [--chapters site/chapters.json]

- Inlines fonts as data URIs at the /*FONTS*/ marker (artifact CSP only allows Google Fonts externally).
- Replaces CHAPTERS_JSON and DURATION from chapters.json (+ explainer.mp4 duration via ffprobe).
- Syntax-checks the last inline <script> with `node --check` (or `bun build`), since a browser preview
  may not be available.
"""
import argparse
import base64
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--out", required=True)
    ap.add_argument("--font", action="append", default=[], help="WEIGHT=path.woff2")
    ap.add_argument("--font-family", default="ProjectFont")
    ap.add_argument("--chapters")
    a = ap.parse_args()

    src = Path(a.src).read_text()
    faces = ""
    for spec in a.font:
        w, p = spec.split("=", 1)
        b = base64.b64encode(Path(p).read_bytes()).decode()
        fmt = "woff2" if p.endswith("woff2") else "woff" if p.endswith("woff") else "opentype"
        faces += f'@font-face{{font-family:"{a.font_family}";font-weight:{w};font-style:normal;font-display:swap;src:url(data:font/{fmt};base64,{b}) format("{fmt}");}}\n'
    src = src.replace("/*FONTS*/", faces)

    chapters = []
    if a.chapters and Path(a.chapters).exists():
        chapters = json.loads(Path(a.chapters).read_text())
    src = src.replace("CHAPTERS_JSON", json.dumps(chapters, ensure_ascii=False))
    video = Path(a.out).parent / "explainer.mp4"
    if "DURATION" in src and video.exists():
        d = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)]))
        src = src.replace("DURATION", f"{int(d // 60)} min {int(d % 60):02d}")

    leftovers = sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", src)))
    if leftovers:
        print("WARNING: unfilled template placeholders:", ", ".join(leftovers))

    scripts = re.findall(r"<script>(.*?)</script>", src, re.S)
    if scripts:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
            f.write(scripts[-1])
        checker = ["node", "--check", f.name] if shutil.which("node") else ["bun", "build", f.name, "--outfile=/dev/null"]
        r = subprocess.run(checker, capture_output=True, text=True)
        if r.returncode:
            sys.exit("SCRIPT SYNTAX ERROR:\n" + r.stderr[-2000:])
        print("script syntax ok")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(src)
    print("wrote", a.out, f"{len(src) / 1024:.0f} KB")


if __name__ == "__main__":
    main()

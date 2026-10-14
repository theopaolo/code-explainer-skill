#!/usr/bin/env python3
"""Convert web fonts (woff/woff2) to OTF/TTF so Manim (Pango) can use the project's own font.
Usage: .venv/bin/python woff2_to_otf.py out_dir font1.woff2 font2.woff2 ...  (prints family/style names)"""
import sys
from pathlib import Path
from fontTools.ttLib import TTFont

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
for p in sys.argv[2:]:
    f = TTFont(p); f.flavor = None
    ext = ".otf" if "CFF " in f else ".ttf"
    dst = out / (Path(p).stem + ext); f.save(dst)
    print(dst, "| family:", f["name"].getDebugName(1), "| style:", f["name"].getDebugName(2))

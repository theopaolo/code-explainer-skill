#!/usr/bin/env python3
"""Render scenes in parallel, report narration drift, concat, encode under a size budget, write chapters.

Usage:
  python assemble.py scenes.py --scenes S01 S02 ... --labels "Introduction" "Le problème" ... \
      --out ../site/explainer.mp4 [--manim ../.venv/bin/manim] [--jobs 4] [--quality low|final] \
      [--max-mb 14.5] [--poster-at 30]

- low: 480p15 preview renders (fast; for checking frames + drift).
- final: 1080p30, then concat -> H.264 (tune=animation) + mono AAC 64k (speech) with CRF stepped
  up until the file fits --max-mb (artifact file limit is 15 MB). Falls back to 720p if needed.
Writes <out dir>/chapters.json = [[start_seconds, label], ...] and <out dir>/poster.jpg.
"""
import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene_file")
    ap.add_argument("--scenes", nargs="+", required=True)
    ap.add_argument("--labels", nargs="*", default=[])
    ap.add_argument("--out", required=True)
    ap.add_argument("--manim", default="manim")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--quality", choices=["low", "final"], default="final")
    ap.add_argument("--max-mb", type=float, default=14.5)
    ap.add_argument("--poster-at", type=float, default=30)
    ap.add_argument("--skip-render", action="store_true")
    a = ap.parse_args()

    sf = Path(a.scene_file).resolve()
    wd = sf.parent
    stem = sf.stem
    q = ["-ql"] if a.quality == "low" else ["--resolution", "1920,1080", "--frame_rate", "30"]
    sub = "480p15" if a.quality == "low" else "1080p30"
    media = wd / "media" / "videos" / stem / sub

    def render(s):
        log = wd / f"log_{s}.txt"
        r = subprocess.run([a.manim, *q, "--disable_caching", "--progress_bar", "none", "-v", "WARNING", str(sf), s],
                           cwd=wd, stdout=open(log, "w"), stderr=subprocess.STDOUT)
        return s, r.returncode, log

    if not a.skip_render:
        with ThreadPoolExecutor(a.jobs) as ex:
            results = list(ex.map(render, a.scenes))
        failed = [(s, log) for s, rc, log in results if rc]
        for s, log in failed:
            print(f"FAIL {s}\n" + "".join(open(log).readlines()[-12:]))
        if failed:
            sys.exit(1)
        late = [l.strip() for s in a.scenes for l in open(wd / f"log_{s}.txt") if l.startswith("LATE")]
        print("drift:", "none > 0.6 s" if not late else "\n  " + "\n  ".join(late))

    files = [media / f"{s}.mp4" for s in a.scenes]
    starts, t = [], 0.0
    for f in files:
        starts.append(round(t, 1))
        t += dur(f)
    print(f"total {int(t // 60)} min {int(t % 60):02d}")
    out = Path(a.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    if a.labels:
        (out.parent / "chapters.json").write_text(json.dumps([[s, l] for s, l in zip(starts, a.labels)], ensure_ascii=False))
    lst = media / "list.txt"
    lst.write_text("".join(f"file '{f.name}'\n" for f in files))
    if a.quality == "low":
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)], check=True)
        print("preview:", out)
        return
    for crf, scale in [(27, None), (29, None), (31, None), (29, "1280:-2"), (32, "1280:-2")]:
        vf = ["-vf", f"scale={scale}"] if scale else []
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), *vf,
                        "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-tune", "animation", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "64k", "-ac", "1", "-ar", "44100", "-movflags", "+faststart", str(out)], check=True)
        mb = out.stat().st_size / 1e6
        print(f"crf {crf} {scale or '1080p'} -> {mb:.1f} MB")
        if mb <= a.max_mb:
            break
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(a.poster_at), "-i", str(out), "-frames:v", "1", "-q:v", "4",
                    "-vf", "scale=1280:-1", str(out.parent / "poster.jpg")], check=True)


if __name__ == "__main__":
    main()

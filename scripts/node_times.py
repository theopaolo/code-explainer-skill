#!/usr/bin/env python3
"""Video timestamp for each diagram node = chapter start + start of the sentence that introduces it.

Usage: python node_times.py --narration narration.json --audio audio/ --chapters site/chapters.json \
         --map nodes.json --out site/node-times.json
nodes.json: {"node_id": ["s04_echantillonner", "Étape un"], ...}   (scene key, sentence fragment)
chapters.json order must match narration.json key order (assemble.py writes it that way).
--card-scenes s02_x s04_y ...: scenes that start with a silent chapter card (Narrated.card); their
sentence times are shifted by --card-len (default 3.0, = narrated.CARD_LEN).
"""
import argparse, json, re

ap = argparse.ArgumentParser()
for f in ("--narration", "--audio", "--chapters", "--map", "--out"):
    ap.add_argument(f, required=True)
ap.add_argument("--card-scenes", nargs="*", default=[])
ap.add_argument("--card-len", type=float, default=3.0)
a = ap.parse_args()
narr = json.load(open(a.narration))
ch = json.load(open(a.chapters))
starts = {k: ch[i][0] for i, k in enumerate(narr)}

def t(key, frag):
    sents = [s for s in re.split(r"(?<=[.:?!])\s+", narr[key]) if s]
    al = json.load(open(f"{a.audio}/{key}.align.json"))
    chars, t0 = "".join(al["characters"]), al["character_start_times_seconds"]
    pos = 0
    for s in sents:
        i = chars.find(s[:12], pos); i = pos if i < 0 else i
        if frag in s:
            off = a.card_len if key in a.card_scenes else 0.0
            return round(starts[key] + off + max(0, t0[i] - 0.3), 1)
        pos = i + len(s)
    raise SystemExit(f"fragment not found: {key} {frag!r}")

out = {node: t(*v) for node, v in json.load(open(a.map)).items()}
json.dump(out, open(a.out, "w"), indent=1)
print(out)

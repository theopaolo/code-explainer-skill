#!/usr/bin/env python3
"""ElevenLabs narration with character timestamps.

Usage:
  ELEVENLABS_API_KEY=... python tts.py --list-voices [--lang fr]
  ELEVENLABS_API_KEY=... python tts.py narration.json --voice <voice_id> --out audio/ [--only s01_intro s02_x] [--force]

narration.json: {"s01_intro": "text...", "s02_...": "..."}  (ordered = scene order)
Writes audio/<key>.mp3 and audio/<key>.align.json (ElevenLabs alignment: characters + start/end times).

Uses curl (python urllib often fails on macOS with CERTIFICATE_VERIFY_FAILED).
The key is read from the environment only; never write it to disk.
"""
import argparse
import base64
import json
import os
import pathlib
import subprocess
import sys

API = "https://api.elevenlabs.io/v1"


def curl(args):
    out = subprocess.run(["curl", "-s", *args], capture_output=True)
    return out.stdout


def list_voices(key, lang):
    d = json.loads(curl([f"{API}/voices", "-H", f"xi-api-key: {key}"]))
    if "voices" not in d:
        sys.exit(f"ERR {d}")
    for v in d["voices"]:
        langs = sorted({x.get("language") for x in v.get("verified_languages", []) if x.get("language")})
        if lang and lang not in langs and v.get("labels", {}).get("language") != lang:
            continue
        print(f'{v["voice_id"]}  {v["name"][:50]:50}  cat={v.get("category")}  langs={",".join(langs)}')
    print("\nNote: category=premade voices work on the free plan; library/professional voices need a paid plan.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("narration", nargs="?")
    ap.add_argument("--voice")
    ap.add_argument("--out", default="audio")
    ap.add_argument("--model", default="eleven_multilingual_v2")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--list-voices", action="store_true")
    ap.add_argument("--lang")
    ap.add_argument("--stability", type=float, default=0.5)
    ap.add_argument("--style", type=float, default=0.1)
    a = ap.parse_args()
    key = os.environ.get("ELEVENLABS_API_KEY") or os.environ.get("ELEVEN_KEY")
    if not key:
        sys.exit("Set ELEVENLABS_API_KEY in the environment.")
    if a.list_voices:
        return list_voices(key, a.lang)
    if not (a.narration and a.voice):
        sys.exit("narration.json and --voice are required")

    narr = json.loads(pathlib.Path(a.narration).read_text())
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    todo = {k: t for k, t in narr.items() if (not a.only or k in a.only) and (a.force or not (out / f"{k}.mp3").exists())}
    print(f"{len(todo)} segment(s), {sum(len(t) for t in todo.values())} characters (≈ credits on multilingual_v2)")
    for name, text in todo.items():
        body = json.dumps({"text": text, "model_id": a.model,
                           "voice_settings": {"stability": a.stability, "similarity_boost": 0.75, "style": a.style, "use_speaker_boost": True}})
        raw = curl(["-X", "POST", f"{API}/text-to-speech/{a.voice}/with-timestamps?output_format=mp3_44100_128",
                    "-H", f"xi-api-key: {key}", "-H", "Content-Type: application/json", "--data", body])
        try:
            d = json.loads(raw)
        except json.JSONDecodeError:
            sys.exit(f"ERR {name}: non-JSON response {raw[:200]!r}")
        if "audio_base64" not in d:
            # Common: paid_plan_required (library voice on free plan), quota_exceeded (per-key credit cap).
            sys.exit(f"ERR {name}: {json.dumps(d)[:400]}")
        (out / f"{name}.mp3").write_bytes(base64.b64decode(d["audio_base64"]))
        (out / f"{name}.align.json").write_text(json.dumps(d["alignment"]))
        print(f"ok {name} {d['alignment']['character_end_times_seconds'][-1]:.1f}s")


if __name__ == "__main__":
    main()

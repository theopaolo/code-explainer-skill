---
name: code-explainer
description: Turn how a codebase feature or algorithm works into a learning package — a navigable, interactive explainer website (published as an Artifact, demos running the project's real code) plus a 3Blue1Brown-style Manim video narrated with ElevenLabs, written in simplified technical language (ASD-STE100 rules, any language, French by default) with the technical terms and the "why" behind every design decision. Use this whenever the user asks to explain/document/teach how their app, pipeline or algorithm works with diagrams, an explainer site, interactive pages, an explainer or 3b1b-style video, narration/voice-over, ASD-STE100 or simplified technical writing — even if they only ask for one of these parts (e.g. "make a video explaining our matching algorithm", "explique en français comment l'app fait X avec des schémas").
---

# Code explainer: site + 3b1b video

Produces two linked deliverables from a codebase:

1. **An interactive explainer site**: an explorable pipeline overview synced with the video, then
   one chapter per concept/step, each with a demo driven by the project's real code, "why" blocks
   and a technical-terms table, plus a glossary. Published as an Artifact.
2. **A narrated explainer video** — Manim scenes in 3Blue1Brown style, ElevenLabs narration with
   character timestamps for sync, chapters linked from the site.

The reference build (PaletCam color extraction, French, 9 chapters, 11-min video) is in
`references/example/`. Its user feedback shaped this skill: the plain explanation alone was "too
short"; they wanted **why** each choice was made, **the technical names next to the simple
words**, real definitions of jargon ("what does quantized mean"), a native-accent voice, and a
video that stays clear but is good **learning material**.

## Inputs to settle first (ask only what you can't infer)

- **Subject**: which feature/algorithm, which entry files.
- **Language** (default French) and **audience** (the code's own author vs. newcomers).
- **ElevenLabs key**: take it from the message or env; pass it via the `ELEVENLABS_API_KEY`
  environment variable on the command line only. Never write it into files. Remind the user to
  revoke a temporary key at the end.
- **Design system**: the project's tokens/fonts (CLAUDE.md, tokens.css). The site and the video
  reuse them so the explainer looks like the product.
- Video length: default ~1 min per major concept (8–12 min total for a 4-step pipeline with
  theory). Offer a short cut if they want both.

## Workflow

Work in the session scratchpad (`work/` below), not in the repo, unless the user asks otherwise.
`scripts/`, `assets/` and `references/` below are this skill's folders (`~/.claude/skills/code-explainer/…`); call the scripts by that absolute path.

### 1. Understand the code (truth first)

- Read the docs **and the current code**. Docs drift: in the reference build, the deep-dive doc
  said pool 24 / 40 000 px / tone 0.85 while the code said 55 / 46 000 / 0.9. Use the code's
  values and tell the user which docs are stale.
- Collect the *reasons*: comments, ADRs, commit messages, test names. They feed the "why" blocks.
- Grep for any technique the user mentions before confirming it is used.

### 2. Get real data

- Bundle the real modules: write `work/lab-entry.js` that imports them, re-runs the pipeline
  keeping every intermediate stage, and ends with `globalThis.Lab = {...}`; run
  `scripts/bundle_lab.sh` from the project root. Example: `references/example/paletcam_lab_entry.js`.
- Run it headlessly (bun) on a few project sample inputs; dump JSON for the video
  (`ffmpeg -i x.jpg -f rawvideo -pix_fmt rgba x.rgba` avoids image npm deps).
- Pick 4–6 sample inputs that show the mechanism well; resize them for the site (≤ 720 px).

### 3. Outline + write (read `references/writing.md`)

- Chapters: Home → theory (the problems that motivate the design) → numbered steps → special
  modes → glossary. Each chapter: what → how (procedure) → **why** (decision, alternative,
  numbers, limits) → technical terms.
- Write the narration as `work/video/narration.json` (one key per scene, `s01_intro`, …), same
  terms as the site, numbers in words.

### 4. Narration audio (read `references/video.md` § Narration)

```bash
ELEVENLABS_API_KEY=… python scripts/tts.py --list-voices --lang fr
ELEVENLABS_API_KEY=… python scripts/tts.py work/video/narration.json --voice <id> --out work/video/audio
```

Tell the user the character count (≈ credits) before a long run. Handle `paid_plan_required`
(library voice on a free plan) and `quota_exceeded` (per-key credit cap) by asking the user;
don't silently fall back to an English voice for non-English text. If you must, say the accent will be off.

### 5. Video (read `references/video.md`)

```bash
bash scripts/setup_env.sh work            # .venv with manim, fonttools
work/.venv/bin/python scripts/woff2_to_otf.py work/video/fonts <project font .woff2 files>
cp scripts/narrated.py work/video/        # base class: at(), finish(), cap(), tech(), wipe()
```

Write `work/video/scenes.py` (one `Narrated` subclass per narration key). Then:

```bash
cd work/video
../.venv/bin/python scripts/assemble.py scenes.py --scenes S01 … --quality low --out preview.mp4 --manim ../.venv/bin/manim
#  → build frame sheets, Read them, fix overlaps and LATE drift > ~1 s
../.venv/bin/python scripts/assemble.py scenes.py --scenes S01 … --labels "Introduction" … \
    --out ../site/explainer.mp4 --manim ../.venv/bin/manim     # run in background (~15–20 min)
```

### 6. Site (read `references/site.md`)

Copy `assets/site-template.html` → `work/site/index.src.html`, fill chapters, adapt tokens/font,
write one demo per chapter using `Lab.*`. Under the home video, add the explorable pipeline
overview from `assets/pipeline-diagram.html`, with node timestamps from `scripts/node_times.py`.
Build:

```bash
python scripts/build_site.py work/site/index.src.html --out work/site/explainer.html \
  --font 400=<Regular.woff2> --font 600=<Semibold.woff2> --font-family "<Family>" --chapters work/site/chapters.json
```

Then check it in a real browser with `scripts/screenshot.mjs` (see `references/site.md` § Verification).

### 7. Publish

Publish `explainer.html` with the Artifact tool (`files`: lab.js, img/*, explainer.mp4,
poster.jpg). Republish the same path to keep the URL. Report: link (private until shared),
video length, voice used, what was verified (and what was not, e.g. no browser available),
docs found stale, and remind the user to revoke the key.

## Quality bar (check before publishing)

- Every number on screen / in text comes from the current code or a real run.
- Every chapter has: a demo, at least one "why" with an alternative, a technical-terms table.
- The home page has the pipeline overview, and every node has a video timestamp and a chapter link.
- Narration and site use the same terms; the glossary lists them.
- Text follows the plain style in `references/writing.md` (conclusion first, literal, no em dashes,
  no bold, no rhetorical "Pourquoi ?", paragraphs over bullets). The product name is the one the
  user uses, not the repo name: ask if unsure.
- Each chapter opens with a title card in the video and a sentence that names it.
- Video: no LATE > ~1.5 s, no overlapping text in the frame sheets, file ≤ 15 MB.
- The site works at phone width, in light and dark themes, and its script passes the syntax check.

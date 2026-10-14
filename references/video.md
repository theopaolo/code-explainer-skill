# The 3Blue1Brown-style video (Manim + ElevenLabs)

Full worked example: `references/example/paletcam_scenes.py` (13 scenes, ~11 min) built on
`paletcam_base.py` (color math, data loading, older helpers). Read a scene or two before writing
new ones — they show the patterns below in practice.

## Look

- Dark background (use the project's own darkest surface token), one accent color, the project's
  own font (convert woff2 → OTF with `scripts/woff2_to_otf.py`, register via `setup_project`).
- Things *appear when they are spoken*: Write / Create / GrowFromCenter / LaggedStart, then
  Transform between states. Avoid static slides.
- One idea on screen at a time; `wipe()` between sub-parts of a long scene.
- Show the real thing: real images from the project, real data dumped by running the real code,
  real constants. Numbers on screen must match the narration and the site.
- Technical names appear as small accent tags under the title (`tech()`), the "why" as a caption
  line (`cap()`), one caption at a time, bottom-left by default.

## Scene structure

- One scene per narration segment (`key` = narration.json key = audio file name).
- Typical segments: intro → theory problem(s) → each pipeline step (split long steps into 2 scenes,
  e.g. "stability" and "filters") → special modes → summary.
- Each scene: `self.at("fragment")` before the animation for that sentence, `self.finish()` at the end.
- Keep run_times short (0.4–1.4 s). Animations longer than the sentence make the next `at()` late.
- Chapter cards: set `card = (eyebrow, title, subtitle)` on the first scene of each chapter
  (`narrated.py`). It plays a silent 3 s title before the narration. Without it the user said the
  video "sounds like a single long speech" and they could not tell where a chapter ends. Sub-scenes
  of the same chapter get no card. Pass the same scenes to `node_times.py --card-scenes`.

## Data first

Before writing scenes, dump everything the video shows from the *real* code into JSON
(e.g. run the bundled lab with bun on decoded images: `ffmpeg -i img.jpg -f rawvideo -pix_fmt rgba`
gives raw pixels without extra npm deps). If a scene re-implements logic in Python (e.g. a greedy
selection to animate picks one by one), **verify it reproduces the JS output exactly** and say so.

## Layout gotchas seen in practice

- Frame is ±7.1 × ±4 units. Titles UL, tags under titles; keep plots below y ≈ 2.2 or they collide
  with the tag lines.
- `Text` has no auto-wrap: insert `\n` for captions longer than ~50 characters.
- No LaTeX installed → no MathTex. Unicode in `Text` is fine: √ ² ³ ≈ × ÷ ⌈ ⌉ ≫ Δ ₀₀ ±.
- `always_redraw` + `ValueTracker` for sliders and counters.
- Never call `.animate` on a mobject that is not in the scene — wrap new mobjects in FadeIn.
- Review frames before the final render: render `--quality low`, then
  `ffmpeg -i S05.mp4 -vf "fps=6/<dur>,scale=400:-1,tile=6x1" -frames:v 1 sheet.png` per scene and
  stack the sheets; look at them with the Read tool. Fix overlaps, then render final.

## Narration (ElevenLabs)

- `scripts/tts.py --list-voices --lang fr` to choose. Prefer a **native voice of the target
  language** (category professional/library). Premade English voices speaking French keep an
  English/British accent — the user noticed immediately.
- Free plan: library voices are refused via API (`paid_plan_required`). API keys can also have
  their **own credit cap** (`quota_exceeded … API key quota of 20`) even on a paid plan — ask the
  user to raise/remove it in ElevenLabs → API Keys.
- Always use the `/with-timestamps` endpoint: exact sentence starts beat estimating from length
  (silence detection fails: TTS pauses are too short).
- Model `eleven_multilingual_v2`. Settings that worked: stability 0.5, similarity 0.75, style 0.1.
- Pass the key via environment variable only. Never write it into files, the skill, or the site.

## Rendering + assembly

- `scripts/assemble.py scenes.py --scenes S01 … --labels … --out site/explainer.mp4`
  renders in parallel (4 jobs), prints `LATE` drift (> 0.6 s), concatenates, encodes.
- **Size budget:** artifact binary files max 15 MB. Speech audio at stereo 128 k was half of a
  20 MB file — mono AAC 64 k is plenty for voice. Video: H.264 `-tune animation`, CRF 27–31.
- Final render of ~11 min at 1080p30 with 4 jobs: ~15–20 min. Run it in the background and do
  the site meanwhile.
- Chapters (scene start times + labels) go into `chapters.json`; the site shows them as buttons.

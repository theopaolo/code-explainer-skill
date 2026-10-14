"""Manim helpers for narrated 3Blue1Brown-style explainers.

Copy this file next to your scene file (or add its folder to sys.path), then:

    from narrated import *          # also re-exports manim's *
    setup_project(here=Path(__file__).parent, font_dir="fonts", font="SN Pro",
                  theme=dict(bg="#0c0c0c", ink="#f0f0f0", muted="#8a8a84", faint="#2a2a28",
                             accent="#ffc800", accent_soft="#ffe06d", danger="#ff4a4a"))

    class S01(Narrated):
        key = "s01_intro"            # matches narration.json + audio/<key>.mp3/.align.json
        def construct(self):
            self.at("Première phrase")   # wait until the sentence containing this fragment starts
            self.play(Write(T("Titre", 48)))
            self.finish()

Chapter cards: set `card = ("Chapitre 4 · Étape 1", "Échantillonner", "stride")` on the scene that opens a
chapter. A silent title card (CARD_LEN s) plays before the narration, and the audio is offset to match.
Viewers asked for this: without breaks, a long video sounds like one speech and chapters blur together.

Timing model: narration is split into sentences on '.', '?', '!' and ':'. ElevenLabs alignment gives the
exact start time of each sentence. `self.at(fragment)` waits until that sentence starts. If the scene is
already past that point (animations too long), it prints `LATE <key> '<frag>' by Xs` to stderr — grep
the render logs for LATE and shorten run_times where the lag is > ~1 s.
"""
import json
import re
import sys
from pathlib import Path

import manimpango
from manim import *  # noqa: F401,F403

CFG = {"here": Path("."), "audio": "audio", "font": "sans-serif"}
C = dict(bg="#0c0c0c", ink="#f0f0f0", muted="#8a8a84", faint="#2a2a28", accent="#ffc800", accent_soft="#ffe06d", danger="#ff4a4a")
SENTENCE_SPLIT = r"(?<=[.:?!])\s+"
CARD_LEN = 3.0  # silent chapter title card, in seconds (keep in sync with node_times.py --card-len)


def setup_project(here, font_dir=None, font="sans-serif", theme=None, audio="audio", narration="narration.json"):
    """Register fonts (OTF/TTF; convert woff2 with fontTools first), set theme + background."""
    CFG.update(here=Path(here), audio=audio, font=font)
    if font_dir:
        for f in list((Path(here) / font_dir).glob("*.otf")) + list((Path(here) / font_dir).glob("*.ttf")):
            manimpango.register_font(str(f))
    if theme:
        C.update(theme)
    config.background_color = C["bg"]
    CFG["narr"] = json.loads((Path(here) / narration).read_text())


def T(s, size=36, color=None, weight=NORMAL, **kw):
    """Text in the project font. No LaTeX needed: use unicode (√, ², ≈, ×, ΔE, ⌈⌉) instead of MathTex."""
    return Text(s, font=CFG["font"], font_size=size, color=color or C["ink"], weight=weight, **kw)


def tech(label, anchor, size=20):
    """Small accent tag under a title: the technical name next to the plain-language one."""
    return T(label, size, C["accent_soft"]).next_to(anchor, DOWN, buff=0.18, aligned_edge=LEFT)


def step_title(n, label):
    return VGroup(T(str(n), 30, C["accent"], weight=SEMIBOLD), T(label, 30)).arrange(RIGHT, buff=0.25).to_corner(UL, buff=0.55)


def scene_title(label):
    return T(label, 30).to_corner(UL, buff=0.55)


def hexc(rgb):
    return "#%02x%02x%02x" % tuple(int(round(v)) for v in rgb)


class Narrated(Scene):
    key = ""
    card = None  # (eyebrow, title, subtitle or None) on the first scene of a chapter
    _cap = None
    _card_done = False

    def setup(self):
        text = CFG["narr"][self.key]
        self.sents = [s for s in re.split(SENTENCE_SPLIT, text) if s]
        adir = CFG["here"] / CFG["audio"]
        align = json.loads((adir / f"{self.key}.align.json").read_text())
        chars, t0 = "".join(align["characters"]), align["character_start_times_seconds"]
        off = CARD_LEN if self.card else 0.0
        self.dur = off + align["character_end_times_seconds"][-1] + 0.25
        self.starts, pos = [], 0
        for sent in self.sents:
            i = chars.find(sent[:12], pos)
            i = pos if i < 0 else i
            self.starts.append(off + max(0.0, t0[min(i, len(t0) - 1)] - 0.1))
            pos = i + len(sent)
        self.add_sound(str(adir / f"{self.key}.mp3"), time_offset=off)

    def show_card(self):
        """Silent chapter title: eyebrow, title, accent rule, optional subtitle (technical names)."""
        self._card_done = True
        eyebrow, title, sub = self.card
        e = T(eyebrow, 26, C["accent"])
        t = T(title, 56, weight=SEMIBOLD)
        line = Line(LEFT, RIGHT, color=C["accent"], stroke_width=3).set_width(1.2)
        g = VGroup(e, t, line).arrange(DOWN, buff=0.35)
        if sub:
            g.add(T(sub, 22, C["muted"]).next_to(line, DOWN, buff=0.35))
        g.move_to(ORIGIN)
        self.play(FadeIn(e, shift=UP * 0.15), Write(t), run_time=0.9)
        self.play(Create(line), *([FadeIn(g[3])] if sub else []), run_time=0.5)
        self.wait(CARD_LEN - 2.1)
        self.play(FadeOut(g, shift=UP * 0.2), run_time=0.5)

    def at(self, frag):
        """Wait until the first sentence containing `frag` starts (case-sensitive)."""
        if self.card and not self._card_done:
            self.show_card()
        try:
            i = next(k for k, s in enumerate(self.sents) if frag in s)
        except StopIteration:
            raise ValueError(f"[{self.key}] fragment not found in narration: {frag!r}")
        dt = self.starts[i] - self.time
        if dt < -0.6:
            print(f"LATE {self.key} '{frag}' by {-dt:.2f}s", file=sys.stderr)
        if dt > 1 / 30:
            self.wait(dt)

    def finish(self, tail=0.7):
        dt = self.dur + tail - self.time
        if dt > 1 / 30:
            self.wait(dt)

    # Caption = the on-screen "why" line. One at a time, replaced in place.
    def cap(self, text, size=24, color=None, corner=DL, buff=0.6, run_time=0.5):
        new = T(text, size, color, line_spacing=0.9).to_corner(corner, buff=buff)
        if self._cap is not None:
            self.play(FadeOut(self._cap, shift=UP * 0.1), FadeIn(new, shift=UP * 0.1), run_time=run_time)
        else:
            self.play(FadeIn(new, shift=UP * 0.1), run_time=run_time)
        self._cap = new
        return new

    def uncap(self, run_time=0.4):
        if self._cap is not None:
            self.play(FadeOut(self._cap), run_time=run_time)
            self._cap = None

    def wipe(self, keep=(), run_time=0.6):
        """Fade out everything except `keep` (use between sub-parts of a long scene)."""
        gone = [m for m in self.mobjects if m not in keep]
        if gone:
            self.play(*[FadeOut(m) for m in gone], run_time=run_time)
        if self._cap is not None and self._cap not in keep:
            self._cap = None

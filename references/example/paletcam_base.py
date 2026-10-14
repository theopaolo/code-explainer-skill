"""PaletCam : comment l'application extrait les couleurs. Vidéo style 3Blue1Brown."""

import json
import math
import random
import re
from pathlib import Path

import manimpango
import numpy as np
from manim import *

HERE = Path(__file__).parent
ROOT = HERE.parent
for f in (HERE / "fonts").glob("*.otf"):
    manimpango.register_font(str(f))

NARR = json.loads((HERE / "narration.json").read_text())
TIMING = json.loads((HERE / "timing.json").read_text())
PIPE = json.loads((ROOT / "pipeline-data.json").read_text())
SD = json.loads((ROOT / "scene-data.json").read_text())

F = "SN Pro"
BG = "#0c0c0c"
INK = "#f0f0f0"
MUTED = "#8a8a84"
FAINT = "#2a2a28"
ACCENT = "#ffc800"
ACCENT_SOFT = "#ffe06d"
DANGER = "#ff4a4a"
config.background_color = BG


# ---------------------------------------------------------------- color math
def _lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _unlin(c):
    s = 12.92 * c if c <= 0.0031308 else 1.055 * (max(c, 0) ** (1 / 2.4)) - 0.055
    return int(round(max(0, min(1, s)) * 255))


def rgb_to_oklab(r, g, b):
    r, g, b = _lin(r), _lin(g), _lin(b)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = np.cbrt(l), np.cbrt(m), np.cbrt(s)
    return (
        0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
        1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
        0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s,
    )


def oklab_to_rgb(L, a, b):
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return (
        _unlin(4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s),
        _unlin(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s),
        _unlin(-0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s),
    )


def hexc(rgb):
    return "#%02x%02x%02x" % tuple(int(v) for v in rgb)


def lab_hex(L, a, b):
    return hexc(oklab_to_rgb(L, a, b))


def T(s, size=36, color=INK, weight=NORMAL, **kw):
    return Text(s, font=F, font_size=size, color=color, weight=weight, **kw)


# ---------------------------------------------------------------- narration
class Narrated(Scene):
    key = ""

    def setup(self):
        text = NARR[self.key]
        self.sents = [s for s in re.split(r"(?<=[.:])\s+", text) if s]
        align = json.loads((HERE / "audio2" / f"{self.key}.align.json").read_text())
        chars, t0 = "".join(align["characters"]), align["character_start_times_seconds"]
        self.dur = align["character_end_times_seconds"][-1] + 0.25
        self.starts, pos = [], 0
        for sent in self.sents:
            i = chars.find(sent[:12], pos)
            i = pos if i < 0 else i
            self.starts.append(max(0.0, t0[i] - 0.1))
            pos = i + len(sent)
        self.add_sound(str(HERE / "audio2" / f"{self.key}.mp3"))

    def at(self, frag):
        i = next(k for k, s in enumerate(self.sents) if frag in s)
        dt = self.starts[i] - self.time
        if dt < -0.6:
            import sys
            print(f"LATE {self.key} '{frag}' by {-dt:.2f}s", file=sys.stderr)
        if dt > 1 / 30:
            self.wait(dt)

    def finish(self, tail=0.7):
        dt = self.dur + tail - self.time
        if dt > 1 / 30:
            self.wait(dt)

    def clear_all(self, run_time=0.6):
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects], run_time=run_time)


def tech(label, anchor):
    return T(label, 20, ACCENT_SOFT).next_to(anchor, DOWN, buff=0.18, aligned_edge=LEFT)


def step_title(n, label):
    num = T(str(n), 30, ACCENT, weight=SEMIBOLD)
    lab = T(label, 30, INK)
    g = VGroup(num, lab).arrange(RIGHT, buff=0.25)
    return g.to_corner(UL, buff=0.55)


def scene_title(label):
    return T(label, 30, INK).to_corner(UL, buff=0.55)


def palette_bars(colors, height=3.6, width=0.75, buff=0.0):
    bars = VGroup(
        *[
            Rectangle(width=width, height=height, stroke_width=0)
            .set_fill(hexc((c["r"], c["g"], c["b"])), 1)
            for c in colors
        ]
    ).arrange(RIGHT, buff=buff)
    return bars


def ab_plane(center=ORIGIN, K=14.0, extent=0.3, labels=True):
    r = extent * K
    h = Line(center + LEFT * r, center + RIGHT * r, stroke_width=1.5, color=FAINT)
    v = Line(center + DOWN * r, center + UP * r, stroke_width=1.5, color=FAINT)
    g = VGroup(h, v)
    if labels:
        g.add(T("a", 22, MUTED).next_to(h, RIGHT, buff=0.12))
        g.add(T("b", 22, MUTED).next_to(v, UP, buff=0.12))
    return g


def ab_pos(a, b, center=ORIGIN, K=14.0):
    return center + np.array([a * K, b * K, 0])


STEPS = ["Échantillonner", "Découper", "Choisir", "Lisser"]


def steps_row(width=12.4):
    boxes = VGroup()
    for i, s in enumerate(STEPS):
        num = T(str(i + 1), 26, ACCENT, weight=SEMIBOLD)
        lab = T(s, 26, INK)
        g = VGroup(num, lab).arrange(RIGHT, buff=0.2)
        box = RoundedRectangle(
            corner_radius=0.12, width=g.width + 0.6, height=0.9, stroke_color=FAINT, stroke_width=2
        )
        g.move_to(box)
        boxes.add(VGroup(box, g))
    boxes.arrange(RIGHT, buff=0.55)
    arrows = VGroup(
        *[
            Arrow(boxes[i].get_right(), boxes[i + 1].get_left(), buff=0.08, stroke_width=3,
                  color=MUTED, max_tip_length_to_length_ratio=0.35)
            for i in range(3)
        ]
    )
    return boxes, arrows


PAL16 = PIPE["16"]["colors"]


# ======================================================================= S01
class S01(Narrated):
    key = "s01_intro"

    def construct(self):
        title = T("PaletCam", 64, INK, weight=SEMIBOLD)
        self.at("PaletCam est")
        self.play(Write(title), run_time=1.4)
        self.play(title.animate.scale(0.5).to_corner(UL, buff=0.55), run_time=0.8)

        self.at("Elle lit")
        img = ImageMobject(str(HERE / "img16.jpg")).set_height(4.8).move_to(LEFT * 2.6 + DOWN * 0.2)
        frame = img.get_corner(UL), img.get_corner(UR), img.get_corner(DR), img.get_corner(DL)
        corners = VGroup()
        L = 0.45
        for p, dx, dy in [(frame[0], 1, -1), (frame[1], -1, -1), (frame[2], -1, 1), (frame[3], 1, 1)]:
            q = p + np.array([-dx * 0.15, -dy * 0.15, 0])
            corners.add(VMobject(stroke_color=ACCENT, stroke_width=4).set_points_as_corners(
                [q + RIGHT * dx * L, q, q + UP * dy * L]))
        self.play(FadeIn(img, scale=1.04), Create(corners), run_time=1.2)

        self.at("Elle trouve")
        spots = [(0.62, 0.78), (0.12, 0.35), (0.25, 0.86), (0.38, 0.47), (0.9, 0.1)]
        chips = VGroup()
        for c, (u, v) in zip(PAL16, spots):
            pos = img.get_corner(UL) + RIGHT * img.width * u + DOWN * img.height * v
            chips.add(Square(0.32, stroke_color=INK, stroke_width=2).set_fill(hexc((c["r"], c["g"], c["b"])), 1).move_to(pos))
        self.play(LaggedStart(*[GrowFromCenter(s) for s in chips], lag_ratio=0.18), run_time=1.4)

        self.at("Elle montre")
        bars = palette_bars(PAL16, height=4.8, width=0.85).move_to(RIGHT * 3.6 + DOWN * 0.2)
        self.play(
            LaggedStart(*[ReplacementTransform(chips[i], bars[i]) for i in range(5)], lag_ratio=0.12),
            run_time=1.6,
        )

        self.at("Le processus")
        boxes, arrows = steps_row()
        boxes.move_to(DOWN * 2.6)
        arrows = VGroup(*[Arrow(boxes[i].get_right(), boxes[i + 1].get_left(), buff=0.08, stroke_width=3,
                               color=MUTED, max_tip_length_to_length_ratio=0.35) for i in range(3)])
        top = Group(img, corners, bars)
        self.play(top.animate.scale(0.7).shift(UP * 0.9), run_time=0.8)
        for i in range(4):
            anims = [FadeIn(boxes[i], shift=UP * 0.2)]
            if i:
                anims.append(GrowArrow(arrows[i - 1]))
            self.play(*anims, run_time=0.55)

        self.at("Cette vidéo")
        self.play(LaggedStart(*[Indicate(b[0], color=ACCENT, scale_factor=1.06) for b in boxes], lag_ratio=0.25), run_time=1.8)
        self.finish()


# ======================================================================= S02
def red_cloud(n=240, seed=3):
    rnd = random.Random(seed)
    pts = []
    hue0 = math.radians(29)
    for _ in range(n):
        k = rnd.random()
        if k < 0.5:
            L, C = rnd.gauss(0.56, 0.04), max(0.02, rnd.gauss(0.18, 0.025))
        elif k < 0.65:
            L, C = rnd.uniform(0.74, 0.92), rnd.uniform(0.02, 0.09)
        elif k < 0.82:
            L, C = rnd.uniform(0.22, 0.38), rnd.uniform(0.04, 0.11)
        else:
            t = rnd.uniform(0.25, 0.9)
            L, C = 0.56 * (1 - t) + 0.82 * t, 0.18 * (1 - t) + 0.035 * t
        h = hue0 + rnd.gauss(0, math.radians(7))
        pts.append((L, C * math.cos(h), C * math.sin(h)))
    return pts


class S02(Narrated):
    key = "s02_probleme"

    def construct(self):
        self.at("D'abord")
        title = scene_title("Le problème de la moyenne")
        self.play(Write(title), run_time=1.0)

        center = RIGHT * 2.2 + DOWN * 0.5
        K = 16
        plane = ab_plane(center, K, 0.22)
        grey = Dot(center, radius=0.09, color="#9a9a9a")
        self.at("Une zone")
        self.play(Create(plane), FadeIn(grey), run_time=1.0)

        pts = red_cloud()
        dots = VGroup(*[Dot(ab_pos(a, b, center, K), radius=0.055, color=lab_hex(L, a, b)) for L, a, b in pts])
        self.at("Un objet rouge")
        self.play(LaggedStart(*[FadeIn(d, scale=0.3) for d in dots], lag_ratio=0.006), run_time=2.2)

        self.at("Chaque pixel")
        sample = VGroup(*dots[::12])
        self.play(LaggedStart(*[Indicate(d, scale_factor=2.2, color=d.get_color()) for d in sample], lag_ratio=0.05), run_time=1.6)

        mL = sum(p[0] for p in pts) / len(pts)
        ma = sum(p[1] for p in pts) / len(pts)
        mb = sum(p[2] for p in pts) / len(pts)
        vivid = max(pts, key=lambda p: math.hypot(p[1], p[2]))
        vdot = Dot(ab_pos(vivid[1], vivid[2], center, K), radius=0.16, color=lab_hex(*vivid)).set_stroke(INK, 3)
        mdot = Dot(ab_pos(ma, mb, center, K), radius=0.16, color=lab_hex(mL, ma, mb)).set_stroke(INK, 3)
        self.at("Si vous")
        self.play(dots.animate.set_opacity(0.35), FadeIn(vdot, scale=0.4), run_time=0.7)
        arrow = Arrow(vdot.get_center(), mdot.get_center(), buff=0.18, color=INK, stroke_width=4)
        mlab = T("moyenne", 24, INK).next_to(mdot, DOWN, buff=0.25).add_background_rectangle(color=BG, opacity=0.75, buff=0.06)
        self.play(GrowArrow(arrow), FadeIn(mdot, scale=0.4), FadeIn(mlab), run_time=1.3)
        arrow2 = DashedLine(mdot.get_center(), center, color=MUTED, dash_length=0.08)
        self.play(Create(arrow2), run_time=0.8)

        self.at("Le centre")
        glab = T("gris", 24, MUTED).next_to(grey, DL, buff=0.12)
        self.play(Flash(grey, color=INK, line_length=0.18), FadeIn(glab), run_time=0.9)

        self.at("Donc")
        sw_v = Square(1.6, stroke_width=0).set_fill(lab_hex(*vivid), 1)
        sw_m = Square(1.6, stroke_width=0).set_fill(lab_hex(mL, ma, mb), 1)
        sws = VGroup(sw_v, sw_m).arrange(RIGHT, buff=0.35).move_to(LEFT * 4.2 + DOWN * 0.2)
        lv = T("pixel le plus vif", 22, MUTED).next_to(sw_v, DOWN, buff=0.2)
        lm = T("moyenne", 22, MUTED).next_to(sw_m, DOWN, buff=0.2)
        cm = math.hypot(ma, mb)
        cv = math.hypot(vivid[1], vivid[2])
        cvl = T(f"C = {cv:.2f}".replace(".", ","), 22, INK).next_to(sw_v, UP, buff=0.2)
        cml = T(f"C = {cm:.2f}".replace(".", ","), 22, INK).next_to(sw_m, UP, buff=0.2)
        self.play(FadeIn(sws, shift=RIGHT * 0.3), FadeIn(lv), FadeIn(lm), FadeIn(cvl), FadeIn(cml), run_time=1.0)

        self.at("PaletCam évite")
        box = SurroundingRectangle(VGroup(sw_v, lv, cvl), color=ACCENT, buff=0.15, corner_radius=0.1)
        self.play(Create(box), run_time=0.8)
        self.finish()


# ======================================================================= S03
class S03(Narrated):
    key = "s03_oklab"

    def construct(self):
        self.at("Pour comparer")
        title = scene_title("L'espace OKLab")
        center = RIGHT * 2.4 + DOWN * 0.4
        K = 13
        plane = ab_plane(center, K, 0.24, labels=False)
        self.play(Write(title), Create(plane), run_time=1.2)

        self.at("Dans cet espace")
        pairs = VGroup()
        for (L, a, b), ang in [((0.75, -0.14, 0.10), 0.0), ((0.5, -0.02, -0.18), 0.0)]:
            p1 = ab_pos(a, b, center, K)
            p2 = p1 + RIGHT * 0.9
            a2 = a + 0.9 / K
            d1 = Dot(p1, radius=0.12, color=lab_hex(L, a, b))
            d2 = Dot(p2, radius=0.12, color=lab_hex(L, a2, b))
            seg = Line(p1, p2, color=INK, stroke_width=2)
            pairs.add(VGroup(seg, d1, d2))
        eq = T("même distance = même écart visible", 24, MUTED).to_edge(DOWN, buff=0.5).shift(RIGHT * 2.4)
        self.play(FadeIn(pairs), FadeIn(eq), run_time=1.0)
        self.wait(1.2)
        self.play(FadeOut(pairs), FadeOut(eq), run_time=0.6)

        self.at("L'axe L")
        bar = Rectangle(width=0.55, height=5.2, stroke_width=0).set_fill(color=[BLACK, WHITE], opacity=1)
        bar.set_sheen_direction(UP).move_to(LEFT * 4.4 + DOWN * 0.4)
        bar.set_stroke(FAINT, 1)
        lL = T("L · clarté", 24, INK).next_to(bar, UP, buff=0.25)
        l0 = T("0  noir", 20, MUTED).next_to(bar, RIGHT, buff=0.2).align_to(bar, DOWN)
        l1 = T("1  blanc", 20, MUTED).next_to(bar, RIGHT, buff=0.2).align_to(bar, UP)
        self.play(GrowFromEdge(bar, DOWN), FadeIn(lL), FadeIn(l0), FadeIn(l1), run_time=1.2)

        r = 0.24 * K
        self.at("L'axe a")
        ax_a = Arrow(center + LEFT * r, center + RIGHT * r, buff=0, stroke_width=6, max_tip_length_to_length_ratio=0.04)
        ax_a.set_color([lab_hex(0.7, -0.2, 0), lab_hex(0.65, 0.2, 0)])
        ta = T("a", 26, INK).next_to(ax_a, RIGHT, buff=0.15)
        tav = T("vert", 20, MUTED).next_to(ax_a.get_start(), DOWN, buff=0.15)
        tar = T("rouge", 20, MUTED).next_to(ax_a.get_end(), DOWN, buff=0.15).shift(LEFT * 0.3)
        self.play(GrowArrow(ax_a), FadeIn(ta), FadeIn(tav), FadeIn(tar), run_time=1.1)

        self.at("L'axe b")
        ax_b = Arrow(center + DOWN * r, center + UP * r, buff=0, stroke_width=6, max_tip_length_to_length_ratio=0.04)
        ax_b.set_color([lab_hex(0.5, 0, -0.2), lab_hex(0.88, 0, 0.18)])
        tb = T("b", 26, INK).next_to(ax_b, UP, buff=0.15)
        tbb = T("bleu", 20, MUTED).next_to(ax_b.get_start(), LEFT, buff=0.15)
        tbj = T("jaune", 20, MUTED).next_to(ax_b.get_end(), LEFT, buff=0.15).shift(DOWN * 0.3)
        self.play(GrowArrow(ax_b), FadeIn(tb), FadeIn(tbb), FadeIn(tbj), run_time=1.1)

        ring = VGroup()
        for k in range(72):
            h = 2 * math.pi * k / 72
            a, b = 0.13 * math.cos(h), 0.13 * math.sin(h)
            ring.add(Dot(ab_pos(a, b, center, K), radius=0.075, color=lab_hex(0.72, a, b)))
        self.play(LaggedStart(*[FadeIn(d, scale=0.2) for d in ring], lag_ratio=0.01), run_time=1.0)

        self.at("Les gris")
        grey = Dot(center, radius=0.12, color="#a0a0a0").set_stroke(INK, 2)
        gl = T("gris", 22, INK).next_to(grey, DL, buff=0.12)
        self.play(FadeIn(grey, scale=0.3), FadeIn(gl), run_time=0.8)

        h0 = math.radians(62)
        tip = ab_pos(0.13 * math.cos(h0), 0.13 * math.sin(h0), center, K)
        self.at("La distance")
        rad = Line(center, tip, color=ACCENT, stroke_width=5)
        cl = T("C : chroma = √(a² + b²)", 24, ACCENT).to_corner(UR, buff=0.6)
        self.play(Create(rad), Indicate(ring[12], scale_factor=2.0, color=ring[12].get_color()), FadeIn(cl), run_time=1.2)

        self.at("L'angle")
        arc = Arc(radius=0.8, start_angle=0, angle=h0, arc_center=center, color=ACCENT_SOFT, stroke_width=4)
        hl = VGroup(T("h : teinte (angle)", 24, ACCENT_SOFT).next_to(cl, DOWN, buff=0.2, aligned_edge=LEFT), T("h", 22, ACCENT_SOFT).move_to(center + 1.05 * np.array([math.cos(h0 / 2), math.sin(h0 / 2), 0])))
        self.play(Create(arc), FadeIn(hl), run_time=1.0)
        self.finish()


# ======================================================================= S04
class S04(Narrated):
    key = "s04_echantillonner"

    def construct(self):
        self.at("Étape un")
        title = step_title(1, "Échantillonner")
        self.play(Write(title), run_time=1.0)

        g = SD["grid35"]
        gw, gh, cells = g["gw"], g["gh"], g["cells"]
        s = 0.26
        grid = VGroup()
        for i, c in enumerate(cells):
            x, y = i % gw, i // gw
            sq = Square(s, stroke_width=0.6, stroke_color=BG).set_fill(hexc(c), 1)
            sq.move_to(np.array([(x - (gw - 1) / 2) * s, ((gh - 1) / 2 - y) * s, 0]))
            grid.add(sq)
        grid.move_to(DOWN * 0.35)
        self.at("Une image")
        cap = T("1920 × 1080 ≈ 2 073 600 pixels", 26, INK).next_to(grid, UP, buff=0.3)
        self.play(FadeIn(grid, lag_ratio=0.002), FadeIn(cap), run_time=1.6)

        self.at("L'application ne lit")
        self.play(grid.animate.set_opacity(0.18), run_time=1.0)

        self.at("Pour une image")
        keep = VGroup(*[grid[i] for i in range(len(cells)) if (i % gw) % 7 == 3 and (i // gw) % 7 == 3])
        self.play(*[sq.animate.set_opacity(1).set_stroke(ACCENT, 2.5) for sq in keep], run_time=1.0)
        formula = T("pas = ⌈ √(2 073 600 ÷ 46 000) ⌉ = 7", 26, ACCENT).next_to(grid, DOWN, buff=0.3)
        self.play(FadeIn(formula, shift=UP * 0.2), run_time=0.8)

        self.at("Ce pas fixe")
        tg = tech("stride · sous-échantillonnage", title)
        self.play(FadeIn(tg, shift=DOWN * 0.1), run_time=0.6)
        self.at("Elle garde")
        cnt = T("275 × 155 = 42 625 pixels lus", 26, INK).move_to(cap)
        self.play(ReplacementTransform(cap, cnt), run_time=0.9)
        self.wait(0.8)

        self.at("La répartition")
        self.play(FadeOut(grid), FadeOut(formula), FadeOut(cnt), run_time=0.6)
        dist = SD["dist"]
        rows = VGroup()
        for label, shares in [("toute l'image", dist["full"]), ("échantillon", dist["samp"])]:
            segs = VGroup()
            for c, sh in zip(PAL16, shares):
                segs.add(Rectangle(width=max(0.02, 9 * sh), height=0.7, stroke_width=0).set_fill(hexc((c["r"], c["g"], c["b"])), 1))
            segs.arrange(RIGHT, buff=0)
            lab = T(label, 24, MUTED)
            rows.add(VGroup(lab, segs).arrange(RIGHT, buff=0.4))
        for r in rows:
            r[1].align_to(rows[0][1], LEFT)
        rows.arrange(DOWN, buff=0.5, aligned_edge=RIGHT).move_to(DOWN * 0.2)
        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.3) for r in rows], lag_ratio=0.4), run_time=1.4)

        self.at("Le calcul")
        pulse = Dot(radius=0.18, color=ACCENT).move_to(DOWN * 2.6 + LEFT * 1.6)
        rate = T("≈ 5 extractions par seconde", 26, INK).next_to(pulse, RIGHT, buff=0.35)
        self.play(FadeIn(pulse), FadeIn(rate), run_time=0.5)
        for _ in range(5):
            self.play(Flash(pulse, color=ACCENT, line_length=0.16, flash_radius=0.3), run_time=0.2)
        self.finish()


# ======================================================================= S05
def median_cut_2d(pts, n_boxes):
    """pts: list of (x, y) in 0..31 quantized space. Returns boxes as index lists, in split order."""
    def bounds(idx):
        xs = [pts[i][0] for i in idx]
        ys = [pts[i][1] for i in idx]
        return min(xs), max(xs), min(ys), max(ys)

    boxes = [list(range(len(pts)))]
    history = [list(boxes)]
    cuts = []
    while len(boxes) < n_boxes:
        def vol(idx):
            x0, x1, y0, y1 = bounds(idx)
            return (x1 - x0 + 1) * (y1 - y0 + 1) if len(set(pts[i] for i in idx)) > 1 else -1
        k = max(range(len(boxes)), key=lambda j: vol(boxes[j]))
        if vol(boxes[k]) <= 0:
            break
        idx = boxes.pop(k)
        x0, x1, y0, y1 = bounds(idx)
        dim = 0 if (x1 - x0) >= (y1 - y0) else 1
        idx.sort(key=lambda i: pts[i][dim])
        half = len(idx) // 2
        split_val = pts[idx[half]][dim]
        lo = [i for i in idx if pts[i][dim] < split_val]
        hi = [i for i in idx if pts[i][dim] >= split_val]
        if not lo or not hi:
            lo, hi = idx[:half], idx[half:]
        boxes.extend([lo, hi])
        cuts.append((dim, split_val, (x0, x1, y0, y1)))
        history.append(list(boxes))
    return boxes, cuts


class S05(Narrated):
    key = "s05_decouper"

    def construct(self):
        self.at("Étape deux")
        title = step_title(2, "Découper")
        self.play(Write(title), run_time=1.0)
        self.at("Cet algorithme")
        tg = tech("median cut · ColorCutQuantizer", title)
        self.play(FadeIn(tg, shift=DOWN * 0.1), run_time=0.6)

        raw = SD["pts_05"]
        size = 5.6
        origin = LEFT * 4.6 + DOWN * 3.3
        unit = size / 256

        def pos(r, b):
            return origin + np.array([r * unit, b * unit, 0])

        axes = VGroup(
            Arrow(origin, origin + RIGHT * (size + 0.3), buff=0, stroke_width=2, color=MUTED, max_tip_length_to_length_ratio=0.03),
            Arrow(origin, origin + UP * (size + 0.3), buff=0, stroke_width=2, color=MUTED, max_tip_length_to_length_ratio=0.03),
        )
        axl = VGroup(T("R", 22, MUTED).next_to(axes[0], RIGHT, buff=0.1), T("B", 22, MUTED).next_to(axes[1], UP, buff=0.1))
        dots = VGroup(*[Dot(pos(p[0], p[2]), radius=0.04, color=hexc(p)) for p in raw])
        self.play(Create(axes), FadeIn(axl), FadeIn(dots, lag_ratio=0.002), run_time=1.2)

        self.at("L'application réduit")
        lines = VGroup()
        for k in range(33):
            t = k * 8 * unit
            lines.add(Line(origin + RIGHT * t, origin + RIGHT * t + UP * size, stroke_width=0.6, color=FAINT))
            lines.add(Line(origin + UP * t, origin + UP * t + RIGHT * size, stroke_width=0.6, color=FAINT))
        q = [((p[0] >> 3), (p[2] >> 3)) for p in raw]
        self.play(Create(lines, lag_ratio=0.01), run_time=0.9)
        self.play(*[d.animate.move_to(origin + np.array([(qx + 0.5) * 8 * unit, (qy + 0.5) * 8 * unit, 0])) for d, (qx, qy) in zip(dots, q)], run_time=1.0)
        lv = T("32 niveaux par canal · histogramme 15 bits", 24, MUTED).next_to(axes[0], DOWN, buff=0.25).align_to(axes[0], LEFT)
        self.play(FadeIn(lv), run_time=0.5)

        def rect_for(idx):
            xs = [q[i][0] for i in idx]
            ys = [q[i][1] for i in idx]
            x0, x1, y0, y1 = min(xs), max(xs) + 1, min(ys), max(ys) + 1
            r = Rectangle(width=(x1 - x0) * 8 * unit, height=(y1 - y0) * 8 * unit, stroke_color=ACCENT, stroke_width=2.5)
            r.move_to(origin + np.array([(x0 + x1) / 2 * 8 * unit, (y0 + y1) / 2 * 8 * unit, 0]))
            return r

        self.at("Ensuite")
        all_idx = list(range(len(q)))
        box0 = rect_for(all_idx)
        self.play(Create(box0), lines.animate.set_opacity(0.4), run_time=1.0)

        boxes, cuts = median_cut_2d(q, 55)
        # Replay the first split slowly.
        self.at("Elle coupe")
        b1, _ = median_cut_2d(q, 2)
        r1 = VGroup(*[rect_for(b) for b in b1])
        self.play(ReplacementTransform(box0, r1), run_time=1.2)

        self.at("La coupe")
        c1 = VGroup(*[T(str(len(b)), 24, INK).move_to(r.get_center()).add_background_rectangle(color=BG, opacity=0.7, buff=0.08) for b, r in zip(b1, r1)])
        self.play(FadeIn(c1), run_time=0.6)
        self.wait(1.0)
        self.play(FadeOut(c1), run_time=0.4)

        self.at("L'application répète")
        counter_val = ValueTracker(2)
        counter = always_redraw(lambda: T(f"boîtes : {int(counter_val.get_value())}", 28, INK).to_corner(UR, buff=0.7))
        self.add(counter)
        current = r1
        for n in [4, 8, 16, 32, 55]:
            bn, _ = median_cut_2d(q, n)
            rn = VGroup(*[rect_for(b) for b in bn])
            self.play(ReplacementTransform(current, rn), counter_val.animate.set_value(n), run_time=0.55)
            current = rn

        self.at("Chaque boîte")
        # Pick a populated chromatic box and show its two representatives.
        def chroma(p):
            L, a, b = rgb_to_oklab(*p)
            return math.hypot(a, b)
        pick = max((b for b in boxes if len(b) >= 12), key=lambda b: max(chroma(raw[i]) for i in b) - chroma(tuple(sum(raw[i][k] for i in b) / len(b) for k in range(3))))
        hi = rect_for(pick).set_stroke(INK, 5)
        self.play(current.animate.set_stroke(opacity=0.25), Create(hi), run_time=0.7)
        labs = [rgb_to_oklab(*raw[i]) for i in pick]
        mean = tuple(sum(l[k] for l in labs) / len(labs) for k in range(3))
        viv = max(pick, key=lambda i: chroma(raw[i]))
        sm = Square(1.5, stroke_width=0).set_fill(lab_hex(*mean), 1)
        sv = Square(1.5, stroke_width=0).set_fill(hexc(raw[viv]), 1)
        pair = VGroup(sm, sv).arrange(RIGHT, buff=0.4).move_to(RIGHT * 3.6 + DOWN * 0.3)
        lm = T("moyenne", 22, MUTED).next_to(sm, DOWN, buff=0.2)
        lvv = T("la plus vive", 22, MUTED).next_to(sv, DOWN, buff=0.2)
        self.play(TransformFromCopy(hi, sm), run_time=0.9)
        self.play(FadeIn(lm), run_time=0.3)
        self.at("la couleur moyenne")
        self.play(TransformFromCopy(dots[viv], sv), FadeIn(lvv), run_time=0.9)
        self.finish()


# ======================================================================= S06 / S07 data
D16 = PIPE["16"]
THR = D16["threshold"]
CANDS = D16["cands"]
for c in CANDS:
    c["vlab"] = rgb_to_oklab(c["vivid"]["r"], c["vivid"]["g"], c["vivid"]["b"])
NEUTRALS = [c for c in CANDS if c["c"] < THR]
CHROMA = [c for c in CANDS if c["c"] >= THR]
MAXMASS = max(c["mass"] for c in CANDS)


def cand_radius(m):
    return 0.05 + 0.32 * (m / MAXMASS) ** 0.33


def mean_hex(c):
    return hexc((c["mean"]["r"], c["mean"]["g"], c["mean"]["b"]))


def greedy(tone=0.9, slots=4, radius=0.08, spread=0.6, rarity=0.2):
    maxc = max(c["vc"] for c in CHROMA)
    maxm = max(c["mass"] for c in CHROMA)
    avail = []
    for c in CHROMA:
        L = c["L"] + (c["vlab"][0] - c["L"]) * tone
        a = c["a"] + (c["vlab"][1] - c["a"]) * tone
        b = c["b"] + (c["vlab"][2] - c["b"]) * tone
        h = math.degrees(math.atan2(b, a)) % 360
        avail.append(dict(c=c, L=L, a=a, b=b, h=h, cn=c["vc"] / maxc, rn=1 - c["mass"] / maxm))
    picked = []
    def gap(h1, h2):
        d = abs(h1 - h2)
        return min(d, 360 - d)
    while len(picked) < slots and avail:
        best, bs = -1, -1e9
        for i, x in enumerate(avail):
            if any(math.dist((p["L"], p["a"], p["b"]), (x["L"], x["a"], x["b"])) < radius for p in picked):
                continue
            if any(gap(p["h"], x["h"]) < 25 for p in picked):
                continue
            hs = min(gap(p["h"], x["h"]) for p in picked) / 180 if picked else 0
            s = x["cn"] + spread * hs + rarity * x["rn"]
            if s > bs:
                bs, best = s, i
        if best < 0:
            best = max(range(len(avail)), key=lambda i: min(math.dist((p["L"], p["a"], p["b"]), (avail[i]["L"], avail[i]["a"], avail[i]["b"])) for p in picked))
        picked.append(avail.pop(best))
    return picked


# ======================================================================= S06
class S06(Narrated):
    key = "s06_neutres"

    def construct(self):
        self.at("Étape trois")
        title = step_title(3, "Choisir")
        self.play(Write(title), run_time=1.0)

        center = RIGHT * 2.3 + DOWN * 0.3
        K = 13
        plane = ab_plane(center, K, 0.26)
        self.at("Chaque boîte")
        circles = VGroup()
        for c in CANDS:
            circles.add(Circle(cand_radius(c["mass"]), stroke_color=BG, stroke_width=1.5).set_fill(mean_hex(c), 1).move_to(ab_pos(c["a"], c["b"], center, K)))
        lab = T("55 candidats", 24, MUTED).to_corner(UR, buff=0.6)
        self.play(Create(plane), LaggedStart(*[GrowFromCenter(c) for c in circles], lag_ratio=0.02), FadeIn(lab), run_time=1.6)

        self.at("D'abord")
        self.wait(0.2)
        self.at("Elle calcule")
        ring = DashedVMobject(Circle(THR * K, color=ACCENT, stroke_width=3), num_dashes=24).move_to(center)
        rl = T(f"seuil = {THR:.3f}".replace(".", ","), 24, ACCENT).next_to(center, DR, buff=0.6)
        rule = T("seuil adaptatif = ¼ × chroma (p90 pondéré), entre 0,02 et 0,045", 22, MUTED).to_edge(DOWN, buff=0.4)
        self.play(Create(ring), FadeIn(rl), FadeIn(rule), run_time=1.2)

        self.at("Un candidat sous")
        zoom = VGroup(plane, circles, ring)
        self.play(zoom.animate.scale(3.2, about_point=center), FadeOut(rl), run_time=1.2)
        nidx = [i for i, c in enumerate(CANDS) if c["c"] < THR]
        self.play(*[Indicate(circles[i], color=INK, scale_factor=1.3) for i in nidx], run_time=1.0)
        self.play(zoom.animate.scale(1 / 3.2, about_point=center), run_time=1.0)

        self.at("Les neutres ont")
        slots = VGroup(*[RoundedRectangle(corner_radius=0.06, width=0.7, height=1.1, stroke_color=MUTED, stroke_width=2) for _ in range(5)]).arrange(RIGHT, buff=0.15)
        slots.move_to(LEFT * 4.3 + UP * 2.3)
        tag = T("neutre", 18, ACCENT).next_to(slots[4], DOWN, buff=0.15)
        self.play(FadeIn(slots), run_time=0.6)
        self.play(slots[4].animate.set_stroke(ACCENT, 3), FadeIn(tag), run_time=0.6)

        self.at("L'application divise")
        bar_x = -4.3
        y0, y1 = -3.1, 1.2
        bar = Line([bar_x, y0, 0], [bar_x, y1, 0], color=MUTED, stroke_width=2)
        def ly(L):
            return y0 + (y1 - y0) * L
        seps = VGroup(*[DashedLine([bar_x - 0.9, ly(v), 0], [bar_x + 1.4, ly(v), 0], color=FAINT) for v in (0.34, 0.66)])
        names = VGroup(
            T("sombre", 20, MUTED).move_to([bar_x - 1.5, ly(0.17), 0]),
            T("moyen", 20, MUTED).move_to([bar_x - 1.5, ly(0.5), 0]),
            T("clair", 20, MUTED).move_to([bar_x - 1.5, ly(0.83), 0]),
        )
        self.play(Create(bar), Create(seps), FadeIn(names), run_time=0.9)
        copies = VGroup()
        for k, i in enumerate(nidx):
            c = CANDS[i]
            copies.add(circles[i].copy().move_to([bar_x + 0.35 + 0.25 * (k % 3), ly(c["L"]), 0]))
        self.play(*[TransformFromCopy(circles[i], copies[k]) for k, i in enumerate(nidx)], run_time=1.0)

        self.at("Un groupe doit")
        total = sum(c["mass"] for c in CANDS)
        pct = VGroup()
        for lo, hi, mid in [(0, 0.34, 0.17), (0.34, 0.66, 0.5), (0.66, 1.01, 0.83)]:
            m = sum(c["mass"] for c in NEUTRALS if lo <= c["L"] < hi)
            share = 100 * m / total
            col = INK if share >= 5 else DANGER
            pct.add(T(f"{share:.1f} %".replace(".", ","), 22, col).move_to([bar_x + 1.9, ly(mid), 0]))
        self.play(FadeIn(pct, lag_ratio=0.3), run_time=1.0)
        rule2 = T("un groupe doit avoir ≥ 5 % des pixels", 22, MUTED).move_to(rule)
        self.play(ReplacementTransform(rule, rule2), run_time=0.6)

        self.at("Dans chaque groupe")
        winners = [k for k, i in enumerate(nidx) if CANDS[i]["L"] >= 0.66]
        if winners:
            k = min(winners, key=lambda k: CANDS[nidx[k]]["c"])
            target = copies[k]
            self.play(Indicate(target, color=ACCENT, scale_factor=1.6), run_time=0.8)
            fill = slots[4].copy().set_stroke(width=0).set_fill(mean_hex(CANDS[nidx[k]]), 1)
            self.play(TransformFromCopy(target, fill), run_time=0.9)
        self.finish()


# ======================================================================= S07
class S07(Narrated):
    key = "s07_couleurs"

    def construct(self):
        title = step_title(3, "Choisir")
        self.add(title)
        center = RIGHT * 2.6 + DOWN * 0.55
        K = 12
        plane = ab_plane(center, K, 0.27)
        picks = greedy()
        blended = []
        for c in CHROMA:
            L = c["L"] + (c["vlab"][0] - c["L"]) * 0.9
            a = c["a"] + (c["vlab"][1] - c["a"]) * 0.9
            b = c["b"] + (c["vlab"][2] - c["b"]) * 0.9
            blended.append((L, a, b))
        circles = VGroup(*[
            Circle(cand_radius(c["mass"]), stroke_color=BG, stroke_width=1.5).set_fill(lab_hex(*bl), 1).move_to(ab_pos(bl[1], bl[2], center, K))
            for c, bl in zip(CHROMA, blended)
        ])
        self.at("Ensuite")
        self.play(Create(plane), LaggedStart(*[GrowFromCenter(c) for c in circles], lag_ratio=0.02), run_time=1.5)

        self.at("C'est une sélection")
        tg = tech("greedy selection", title)
        self.play(FadeIn(tg, shift=DOWN * 0.1), run_time=0.6)
        self.at("Chaque candidat")
        terms = [("score =", INK), ("vivacité", INK), ("+ 0,6 × nouveauté", INK), ("+ 0,2 × rareté", INK), ("+ 0,3 × fidélité", MUTED)]
        formula = VGroup(*[T(t, 26, c) for t, c in terms]).arrange(RIGHT, buff=0.18).to_edge(UP, buff=0.55).shift(RIGHT * 1.6)
        self.play(FadeIn(formula, shift=DOWN * 0.2), run_time=0.9)

        for frag, idx in [("Le score augmente", 1), ("Il augmente pour une teinte", 2), ("Il augmente aussi", 3)]:
            self.at(frag)
            self.play(formula[idx].animate.set_color(ACCENT), *[formula[j].animate.set_color(INK) for j in (1, 2, 3) if j != idx], run_time=0.5)
            if idx == 1:
                maxc = max(range(len(CHROMA)), key=lambda i: CHROMA[i]["vc"])
                self.play(Indicate(circles[maxc], color=INK, scale_factor=1.8), run_time=0.8)
            if idx == 3:
                small = sorted(range(len(CHROMA)), key=lambda i: CHROMA[i]["mass"])[:6]
                self.play(*[Indicate(circles[i], color=INK, scale_factor=1.8) for i in small], run_time=0.8)
        self.play(formula[3].animate.set_color(INK), run_time=0.3)

        def zone_for(p):
            pos = ab_pos(p["a"], p["b"], center, K)
            disk = Circle(0.08 * K, color=ACCENT, stroke_width=2.5).set_fill(ACCENT, 0.08).move_to(pos)
            hrad = math.radians(p["h"])
            wedge = AnnularSector(inner_radius=0.0, outer_radius=0.27 * K, angle=math.radians(50), start_angle=hrad - math.radians(25),
                                  arc_center=center, fill_color=ACCENT, fill_opacity=0.07, stroke_width=0)
            return disk, wedge

        def excluded(picked_list):
            out = []
            for i, (L, a, b) in enumerate(blended):
                h = math.degrees(math.atan2(b, a)) % 360
                for p in picked_list:
                    d = math.dist((L, a, b), (p["L"], p["a"], p["b"]))
                    g = min(abs(h - p["h"]), 360 - abs(h - p["h"]))
                    if (d < 0.08 or g < 25) and p["c"] is not CHROMA[i]:
                        out.append(i)
                        break
            return out

        pick_idx = [next(i for i, c in enumerate(CHROMA) if c is p["c"]) for p in picks]

        self.at("Après chaque choix")
        p0 = picks[0]
        ring0 = Circle(cand_radius(p0["c"]["mass"]) + 0.08, color=INK, stroke_width=4).move_to(circles[pick_idx[0]])
        disk0, wedge0 = zone_for(p0)
        self.play(Create(ring0), run_time=0.5)
        self.play(GrowFromCenter(disk0), run_time=0.8)

        self.at("C'est une contrainte")
        tg2 = tech("contrainte de répulsion", tg)
        self.play(FadeIn(tg2, shift=DOWN * 0.1), run_time=0.5)
        self.at("Un candidat dans")
        ex = [i for i in excluded([p0]) if math.dist(blended[i], (p0["L"], p0["a"], p0["b"])) < 0.08]
        self.play(*[circles[i].animate.set_opacity(0.15) for i in ex], run_time=0.8)

        self.at("La distance minimale")
        rline = Line(disk0.get_center(), disk0.get_center() + RIGHT * 0.08 * K, color=ACCENT, stroke_width=3)
        rlab = T("0,08", 22, ACCENT).next_to(rline, UP, buff=0.08)
        self.play(Create(rline), FadeIn(rlab), run_time=0.7)

        self.at("L'écart de teinte")
        wl = T("± 25°", 22, ACCENT_SOFT).move_to(center + 0.27 * K * 0.75 * np.array([math.cos(math.radians(p0["h"]) + 0.5), math.sin(math.radians(p0["h"]) + 0.5), 0]))
        self.play(FadeIn(wedge0), FadeIn(wl), run_time=0.8)
        ex2 = excluded([p0])
        self.play(*[circles[i].animate.set_opacity(0.15) for i in ex2], run_time=0.6)

        self.at("Ainsi")
        self.play(FadeOut(rline), FadeOut(rlab), FadeOut(wl), run_time=0.3)
        for k in range(1, len(picks)):
            p = picks[k]
            ring = Circle(cand_radius(p["c"]["mass"]) + 0.08, color=INK, stroke_width=4).move_to(circles[pick_idx[k]])
            disk, wedge = zone_for(p)
            exk = excluded(picks[: k + 1])
            self.play(Create(ring), GrowFromCenter(disk), FadeIn(wedge),
                      *[circles[i].animate.set_opacity(0.15) for i in exk if i not in pick_idx], run_time=0.55)
        bars = palette_bars(PAL16, height=0.9, width=0.8).to_corner(DL, buff=0.6)
        self.play(FadeIn(bars, shift=UP * 0.3), run_time=0.6)
        self.finish()


# ======================================================================= S08
class S08(Narrated):
    key = "s08_tone"

    def construct(self):
        self.at("La couleur affichée")
        title = scene_title("Le réglage Tone")
        picks = greedy()
        p = max(picks, key=lambda x: math.dist((x["c"]["L"], x["c"]["a"], x["c"]["b"]), x["c"]["vlab"]))
        c = p["c"]
        m = (c["L"], c["a"], c["b"])
        v = c["vlab"]
        center = RIGHT * 2.0 + DOWN * 0.4
        K = 16
        plane = ab_plane(center, K, 0.22)
        pm = ab_pos(m[1], m[2], center, K)
        pv = ab_pos(v[1], v[2], center, K)
        dm = Dot(pm, radius=0.14, color=lab_hex(*m)).set_stroke(INK, 2)
        dv = Dot(pv, radius=0.14, color=lab_hex(*v)).set_stroke(INK, 2)
        lm = T("moyenne", 22, MUTED).next_to(dm, DOWN, buff=0.18)
        lv = T("la plus vive", 22, MUTED).next_to(dv, UP, buff=0.18)
        self.play(Write(title), Create(plane), FadeIn(dm), FadeIn(lm), run_time=1.2)

        self.at("L'application mélange")
        seg = Line(pm, pv, color=MUTED, stroke_width=3)
        self.play(FadeIn(dv), FadeIn(lv), Create(seg), run_time=1.0)

        t = ValueTracker(0.5)

        def mix():
            k = t.get_value()
            return tuple(m[i] + (v[i] - m[i]) * k for i in range(3))

        moving = always_redraw(lambda: Dot(ab_pos(mix()[1], mix()[2], center, K), radius=0.2, color=lab_hex(*mix())).set_stroke(ACCENT, 4))
        swatch = always_redraw(lambda: Square(2.4, stroke_width=0).set_fill(lab_hex(*mix()), 1).move_to(LEFT * 4.2 + UP * 0.4))
        sl0 = LEFT * 5.6 + DOWN * 2.2
        sl1 = LEFT * 2.8 + DOWN * 2.2
        track = Line(sl0, sl1, color=MUTED, stroke_width=4)
        knob = always_redraw(lambda: Dot(sl0 + (sl1 - sl0) * t.get_value(), radius=0.13, color=ACCENT))
        val = always_redraw(lambda: T(f"Tone = {t.get_value():.2f}".replace(".", ","), 26, INK).next_to(track, DOWN, buff=0.35))
        ends = VGroup(T("0", 20, MUTED).next_to(sl0, UP, buff=0.18), T("1", 20, MUTED).next_to(sl1, UP, buff=0.18))

        self.at("C'est une interpolation")
        tg = tech("interpolation linéaire (lerp) dans OKLab", title)
        self.play(FadeIn(tg, shift=DOWN * 0.1), run_time=0.6)
        self.at("Le réglage Tone")
        self.play(FadeIn(moving), FadeIn(swatch), Create(track), FadeIn(knob), FadeIn(val), FadeIn(ends), run_time=1.0)

        self.at("À zéro")
        self.play(t.animate.set_value(0), run_time=1.4)
        self.at("À un")
        self.play(t.animate.set_value(1), run_time=1.8)
        self.at("La valeur par défaut")
        self.play(t.animate.set_value(0.9), run_time=1.0)
        self.at("La couleur reste")
        self.play(Indicate(swatch, color=ACCENT, scale_factor=1.04), run_time=1.0)
        self.finish()


# ======================================================================= S09
class S09(Narrated):
    key = "s09_lisser"

    def construct(self):
        self.at("Étape quatre")
        title = step_title(4, "Lisser")
        self.play(Write(title), run_time=1.0)

        rnd = random.Random(5)
        base = [rgb_to_oklab(c["r"], c["g"], c["b"]) for c in PAL16]
        bars = palette_bars(PAL16, height=2.2, width=1.2).move_to(UP * 0.2)
        self.at("La caméra bouge")
        self.play(FadeIn(bars), run_time=0.6)
        self.at("Sans protection")
        for _ in range(12):
            anims = []
            for bar, (L, a, b) in zip(bars, base):
                n = lambda s: rnd.gauss(0, s)
                anims.append(bar.animate.set_fill(lab_hex(L + n(0.05), a + n(0.03), b + n(0.03)), 1))
            self.play(*anims, run_time=0.14)
        self.play(*[bar.animate.set_fill(lab_hex(*lab), 1) for bar, lab in zip(bars, base)], run_time=0.3)

        self.at("L'application utilise")
        self.play(bars.animate.scale(0.45).to_corner(UR, buff=0.6), run_time=0.7)
        cards = VGroup()
        for n, txt in [("1", "fidélité · hystérésis"), ("2", "moyenne glissante · 5 extractions ≈ 1 s"), ("3", "zone morte · deadband ΔE < 0,04")]:
            g = VGroup(T(n, 26, ACCENT, weight=SEMIBOLD), T(txt, 24, INK)).arrange(RIGHT, buff=0.3)
            cards.add(g)
        cards.arrange(DOWN, buff=0.45, aligned_edge=LEFT).to_edge(LEFT, buff=0.8).shift(UP * 0.6)
        self.play(FadeIn(cards, lag_ratio=0.3, shift=RIGHT * 0.2), cards.animate.set_opacity(0.35), run_time=1.0)

        axes = Axes(x_range=[0, 10, 1], y_range=[0.2, 0.9, 0.1], x_length=6.2, y_length=3.6, tips=False,
                    axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": False}).to_corner(DR, buff=0.7)
        xl = T("temps (s)", 20, MUTED).next_to(axes.x_axis, DOWN, buff=0.15)
        yl = T("clarté L", 20, MUTED).next_to(axes.y_axis, UP, buff=0.12)
        rnd2 = random.Random(11)
        ts = [i * 0.2 for i in range(51)]
        raw = [(0.42 if t < 5 else 0.72) + rnd2.gauss(0, 0.035) for t in ts]
        acc, disp, out = [], None, []
        for r in raw:
            acc = (acc + [r])[-5:]
            avg = sum(acc) / len(acc)
            if disp is None:
                disp = avg
            elif abs(avg - disp) >= 0.04:
                disp = disp + (avg - disp) * 0.45  # display-rate EMA, compressed to extraction steps
            out.append(disp)

        self.at("Premièrement")
        self.play(cards[0].animate.set_opacity(1), run_time=0.5)
        self.at("Deuxièmement")
        rawdots = VGroup(*[Dot(axes.c2p(t, r), radius=0.04, color=MUTED) for t, r in zip(ts, raw)])
        self.play(cards[0].animate.set_opacity(0.35), cards[1].animate.set_opacity(1), Create(axes), FadeIn(xl), FadeIn(yl), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(d, scale=0.3) for d in rawdots], lag_ratio=0.03), run_time=1.4)

        self.at("Troisièmement")
        self.play(cards[1].animate.set_opacity(0.35), cards[2].animate.set_opacity(1), run_time=0.5)
        band = Rectangle(width=axes.x_length * 0.48, height=abs(axes.c2p(0, 0.08)[1] - axes.c2p(0, 0)[1]), stroke_width=0)
        band.set_fill(ACCENT, 0.15).move_to(axes.c2p(2.45, out[20]))
        self.play(FadeIn(band), run_time=0.7)

        self.at("Au-delà")
        tg = T("lissage exponentiel · α = 0,16", 22, ACCENT).next_to(cards, DOWN, buff=0.5, aligned_edge=LEFT)
        curve = VMobject(stroke_color=ACCENT, stroke_width=5).set_points_as_corners([axes.c2p(t, o) for t, o in zip(ts, out)])
        self.play(Create(curve), run_time=2.4)
        self.at("Ce glissement")
        self.play(FadeIn(tg, shift=UP * 0.1), run_time=0.6)
        self.finish()


# ======================================================================= S10
class S10(Narrated):
    key = "s10_une_couleur"

    def construct(self):
        cr = SD["cross"]
        self.at("Avec une seule")
        title = scene_title("Mode une couleur")
        img = ImageMobject(str(HERE / "cross.png")).set_height(3.5).move_to(LEFT * 3.7 + DOWN * 0.2)
        self.play(Write(title), FadeIn(img), run_time=1.2)

        self.at("Une croix")
        c = img.get_center()
        cross = VGroup(
            Line(c + LEFT * 0.5, c + LEFT * 0.12, color=INK, stroke_width=3),
            Line(c + RIGHT * 0.12, c + RIGHT * 0.5, color=INK, stroke_width=3),
            Line(c + UP * 0.5, c + UP * 0.12, color=INK, stroke_width=3),
            Line(c + DOWN * 0.12, c + DOWN * 0.5, color=INK, stroke_width=3),
        )
        px = img.height / 270
        sq = Square(9 * px, color=ACCENT, stroke_width=2).move_to(c)
        self.play(Create(cross), run_time=0.8)

        self.at("L'application lit")
        cells = VGroup()
        s = 0.3
        for i, rgb in enumerate(cr["cells"]):
            x, y = i % 9, i // 9
            cells.add(Square(s, stroke_width=1, stroke_color=BG).set_fill(hexc(rgb), 1).move_to(np.array([(x - 4) * s, (4 - y) * s, 0])))
        cells.move_to(RIGHT * 1.5 + UP * 0.1)
        l1 = DashedLine(sq.get_corner(UR), cells.get_corner(UL), color=MUTED, dash_length=0.06)
        l2 = DashedLine(sq.get_corner(DR), cells.get_corner(DL), color=MUTED, dash_length=0.06)
        lab = T("9 × 9 = 81 pixels", 22, MUTED).next_to(cells, DOWN, buff=0.25)
        self.play(Create(sq), run_time=0.4)
        self.play(TransformFromCopy(sq, cells), Create(l1), Create(l2), FadeIn(lab), run_time=1.2)

        self.at("Elle calcule")
        avg = Square(9 * s, stroke_width=0).set_fill(hexc(cr["avg"]), 1).move_to(cells)
        hx = T(hexc(cr["avg"]).upper(), 22, MUTED).move_to(lab)
        self.play(ReplacementTransform(cells, avg), ReplacementTransform(lab, hx), run_time=1.2)

        self.at("Elle trouve le nom")
        name = T(cr["name"], 34, INK).next_to(avg, RIGHT, buff=0.5).align_to(avg, UP)
        self.play(Write(name), run_time=1.0)

        self.at("Elle trouve aussi")
        ral = cr["ral"]["raw"]
        rsw = Square(0.7, stroke_width=0).set_fill(hexc((ral["r"], ral["g"], ral["b"])), 1)
        rtxt = VGroup(T(cr["ral"]["code"], 26, INK), T(cr["ral"]["name"], 20, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        rg = VGroup(rsw, rtxt).arrange(RIGHT, buff=0.25).next_to(name, DOWN, buff=0.5, aligned_edge=LEFT)
        de = T(f"CIEDE2000 · ΔE₀₀ = {cr['ral']['deltaE']:.1f}".replace(".", ","), 22, ACCENT).next_to(rg, DOWN, buff=0.3, aligned_edge=LEFT)
        self.play(FadeIn(rg, shift=UP * 0.2), run_time=0.8)
        self.play(FadeIn(de), run_time=0.6)
        self.finish()


# ======================================================================= S11
class S11(Narrated):
    key = "s11_resume"

    def construct(self):
        boxes, arrows = steps_row()
        boxes.move_to(UP * 1.2)
        arrows = VGroup(*[Arrow(boxes[i].get_right(), boxes[i + 1].get_left(), buff=0.08, stroke_width=3,
                               color=MUTED, max_tip_length_to_length_ratio=0.35) for i in range(3)])
        self.at("En résumé")
        for i in range(4):
            anims = [FadeIn(boxes[i], shift=UP * 0.2)]
            if i:
                anims.append(GrowArrow(arrows[i - 1]))
            self.play(*anims, run_time=0.55)

        self.at("Le résultat")
        bars = palette_bars(PAL16, height=1.6, width=1.3).move_to(DOWN * 1.4)
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars], lag_ratio=0.12), run_time=1.2)
        words = VGroup(T("vive", 28, INK), T("variée", 28, INK), T("stable", 28, INK)).arrange(RIGHT, buff=0.9).next_to(bars, DOWN, buff=0.4)
        self.play(LaggedStart(*[FadeIn(w, shift=UP * 0.15) for w in words], lag_ratio=0.3), run_time=1.2)

        self.at("L'application calcule")
        self.wait(1.5)
        self.play(FadeOut(boxes), FadeOut(arrows), FadeOut(words), bars.animate.move_to(ORIGIN + DOWN * 0.4), run_time=0.9)
        name = T("PaletCam", 56, INK, weight=SEMIBOLD).next_to(bars, UP, buff=0.5)
        self.play(Write(name), run_time=1.2)
        self.finish(tail=1.6)

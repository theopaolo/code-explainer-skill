"""ColorCatchers : version longue (pourquoi + termes techniques). Réutilise les outils de explainer.py."""

from explainer import (
    ACCENT, ACCENT_SOFT, BG, CANDS, CHROMA, DANGER, FAINT, HERE, INK, MUTED, NEUTRALS, PAL16, SD, THR,
    Narrated, T, ab_plane, ab_pos, cand_radius, greedy, hexc, lab_hex, mean_hex, median_cut_2d,
    oklab_to_rgb, palette_bars, red_cloud, rgb_to_oklab, scene_title, step_title, steps_row, tech,
)
import json
import math
import random
import re
import sys

import numpy as np
from manim import *

from explainer import NARR

HIST = json.loads((HERE / "hist05.json").read_text())


CARD_LEN = 3.0  # silent chapter title before the narration starts


class N(Narrated):
    _cap = None
    card = None  # (eyebrow, title, subtitle) for scenes that open a chapter
    _card_done = False

    def setup(self):
        text = NARR[self.key]
        self.sents = [x for x in re.split(r"(?<=[.:])\s+", text) if x]
        align = json.loads((HERE / "audio3" / f"{self.key}.align.json").read_text())
        chars, t0 = "".join(align["characters"]), align["character_start_times_seconds"]
        off = CARD_LEN if self.card else 0.0
        self.dur = off + align["character_end_times_seconds"][-1] + 0.25
        self.starts, pos = [], 0
        for sent in self.sents:
            i = chars.find(sent[:12], pos)
            i = pos if i < 0 else i
            self.starts.append(off + max(0.0, t0[i] - 0.1))
            pos = i + len(sent)
        self.add_sound(str(HERE / "audio3" / f"{self.key}.mp3"), time_offset=off)

    def show_card(self):
        self._card_done = True
        eyebrow, title, sub = self.card
        e = T(eyebrow, 26, ACCENT)
        t = T(title, 56, INK, weight=SEMIBOLD)
        line = Line(LEFT, RIGHT, color=ACCENT, stroke_width=3).set_width(1.2)
        g = VGroup(e, t, line).arrange(DOWN, buff=0.35)
        if sub:
            g.add(T(sub, 22, MUTED).next_to(line, DOWN, buff=0.35))
        g.move_to(ORIGIN)
        self.play(FadeIn(e, shift=UP * 0.15), Write(t), run_time=0.9)
        self.play(Create(line), *([FadeIn(g[3])] if sub else []), run_time=0.5)
        self.wait(CARD_LEN - 2.1)
        self.play(FadeOut(g, shift=UP * 0.2), run_time=0.5)

    def at(self, frag):
        if self.card and not self._card_done:
            self.show_card()
        matches = [k for k, x in enumerate(self.sents) if frag in x]
        if not matches:
            raise ValueError(f"{self.key}: cue {frag!r} not in narration")
        i = matches[0]
        dt = self.starts[i] - self.time
        if dt < -0.6:
            print(f"LATE {self.key} '{frag}' by {-dt:.2f}s", file=sys.stderr)
        if dt > 1 / 30:
            self.wait(dt)

    def cap(self, text, size=24, color=INK, corner=DL, buff=0.6, run_time=0.5):
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
        gone = [m for m in self.mobjects if m not in keep]
        if gone:
            self.play(*[FadeOut(m) for m in gone], run_time=run_time)
        if self._cap is not None and self._cap not in keep:
            self._cap = None


def sw(rgb, size=1.2):
    return Square(size, stroke_width=0).set_fill(hexc(rgb), 1)


def arrow(a, b, **kw):
    return Arrow(a, b, buff=0.08, stroke_width=3, color=MUTED, max_tip_length_to_length_ratio=0.25, **kw)


# ======================================================================= S01
class S01(N):
    key = "s01_intro"

    def construct(self):
        title = T("ColorCatchers", 64, INK, weight=SEMIBOLD)
        self.at("ColorCatchers est")
        self.play(Write(title), run_time=1.4)
        self.play(title.animate.scale(0.5).to_corner(UL, buff=0.55), run_time=0.8)
        self.at("Elle lit")
        img = ImageMobject(str(HERE / "img16.jpg")).set_height(4.8).move_to(LEFT * 2.6 + DOWN * 0.2)
        corners = VGroup()
        for p, dx, dy in [(img.get_corner(UL), 1, -1), (img.get_corner(UR), -1, -1), (img.get_corner(DR), -1, 1), (img.get_corner(DL), 1, 1)]:
            q = p + np.array([-dx * 0.15, -dy * 0.15, 0])
            corners.add(VMobject(stroke_color=ACCENT, stroke_width=4).set_points_as_corners([q + RIGHT * dx * 0.45, q, q + UP * dy * 0.45]))
        self.play(FadeIn(img, scale=1.04), Create(corners), run_time=1.2)
        self.at("Elle trouve")
        spots = [(0.62, 0.78), (0.12, 0.35), (0.25, 0.86), (0.38, 0.47), (0.9, 0.1)]
        chips = VGroup(*[
            Square(0.32, stroke_color=INK, stroke_width=2).set_fill(hexc((c["r"], c["g"], c["b"])), 1)
            .move_to(img.get_corner(UL) + RIGHT * img.width * u + DOWN * img.height * v)
            for c, (u, v) in zip(PAL16, spots)
        ])
        self.play(LaggedStart(*[GrowFromCenter(s) for s in chips], lag_ratio=0.18), run_time=1.4)
        self.at("Elle montre")
        bars = palette_bars(PAL16, height=4.8, width=0.85).move_to(RIGHT * 3.6 + DOWN * 0.2)
        self.play(LaggedStart(*[ReplacementTransform(chips[i], bars[i]) for i in range(5)], lag_ratio=0.12), run_time=1.6)
        self.at("Le processus")
        boxes, _ = steps_row()
        boxes.move_to(DOWN * 2.6)
        arrows = VGroup(*[arrow(boxes[i].get_right(), boxes[i + 1].get_left()) for i in range(3)])
        self.play(Group(img, corners, bars).animate.scale(0.7).shift(UP * 0.9), run_time=0.8)
        for i in range(4):
            self.play(FadeIn(boxes[i], shift=UP * 0.2), *([GrowArrow(arrows[i - 1])] if i else []), run_time=0.5)
        self.at("Pour chaque étape")
        qs = VGroup(*[T(w, 22, ACCENT_SOFT).next_to(boxes[i], DOWN, buff=0.2) for i, w in enumerate(["quoi ?", "comment ?", "pourquoi ?", "avec quel nom ?"])])
        self.play(LaggedStart(*[FadeIn(q, shift=UP * 0.1) for q in qs], lag_ratio=0.3), run_time=1.6)
        self.finish()


# ======================================================================= S02
def hull(points):
    pts = sorted(set(points))
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


class S02(N):
    key = "s02_probleme"
    card = ('Chapitre 2 · Problème 1', 'La moyenne ternit les couleurs', 'chroma')

    def construct(self):
        self.at("Premier problème")
        title = scene_title("Le problème de la moyenne")
        self.play(Write(title), run_time=1.0)
        center = RIGHT * 2.4 + DOWN * 0.6
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
        self.play(LaggedStart(*[Indicate(d, scale_factor=2.2, color=d.get_color()) for d in dots[::12]], lag_ratio=0.05), run_time=1.6)

        vivid = max(pts, key=lambda p: math.hypot(p[1], p[2]))
        mL, ma, mb = (sum(p[k] for p in pts) / len(pts) for k in range(3))
        self.at("Dans ce graphique")
        rad = Line(center, ab_pos(vivid[1], vivid[2], center, K), color=ACCENT, stroke_width=4)
        rl = T("chroma = distance au centre", 22, ACCENT).next_to(plane, DOWN, buff=0.1)
        self.play(Create(rad), FadeIn(rl), run_time=1.0)
        self.at("Le centre")
        glab = T("gris", 22, MUTED).next_to(grey, DL, buff=0.12)
        self.play(Flash(grey, color=INK, line_length=0.18), FadeIn(glab), FadeOut(rad), FadeOut(rl), run_time=0.9)

        vdot = Dot(ab_pos(vivid[1], vivid[2], center, K), radius=0.16, color=lab_hex(*vivid)).set_stroke(INK, 3)
        mdot = Dot(ab_pos(ma, mb, center, K), radius=0.16, color=lab_hex(mL, ma, mb)).set_stroke(INK, 3)
        self.at("Si vous")
        self.play(dots.animate.set_opacity(0.4), FadeIn(vdot, scale=0.4), run_time=0.6)
        self.play(GrowArrow(Arrow(vdot.get_center(), mdot.get_center(), buff=0.18, color=INK, stroke_width=4)), FadeIn(mdot, scale=0.4), run_time=1.2)
        mlab = T("moyenne", 22, INK).next_to(mdot, DOWN, buff=0.25).add_background_rectangle(color=BG, opacity=0.75, buff=0.06)
        self.play(FadeIn(mlab), run_time=0.4)

        self.at("La raison")
        self.cap("Pourquoi ?", 30, ACCENT)
        self.at("La moyenne est toujours")
        h = hull([(round(a, 5), round(b, 5)) for _, a, b in pts])
        poly = Polygon(*[ab_pos(a, b, center, K) for a, b in h], color=ACCENT_SOFT, stroke_width=2.5).set_fill(ACCENT, 0.06)
        self.play(Create(poly), run_time=1.2)
        self.cap("La moyenne est toujours\nà l'intérieur du nuage.")
        self.at("Les points les plus vifs")
        rim = sorted(range(len(pts)), key=lambda i: -math.hypot(pts[i][1], pts[i][2]))[:12]
        self.play(*[dots[i].animate.set_opacity(1).scale(1.8) for i in rim], run_time=0.9)
        self.cap("Les points vifs sont sur le bord.")
        self.at("Donc")
        l1 = DashedLine(center, vdot.get_center(), color=INK, dash_length=0.08)
        l2 = Line(center, mdot.get_center(), color=ACCENT, stroke_width=5)
        self.play(Create(l1), Create(l2), run_time=1.0)

        self.at("Ici, le pixel")
        self.uncap()
        sv = Square(1.6, stroke_width=0).set_fill(lab_hex(*vivid), 1)
        sm = Square(1.6, stroke_width=0).set_fill(lab_hex(mL, ma, mb), 1)
        sws = VGroup(sv, sm).arrange(RIGHT, buff=0.35).move_to(LEFT * 4.3 + DOWN * 0.1)
        cv = T(f"C = {math.hypot(vivid[1], vivid[2]):.2f}".replace(".", ","), 24, INK).next_to(sv, UP, buff=0.2)
        lv = T("pixel le plus vif", 20, MUTED).next_to(sv, DOWN, buff=0.2)
        self.play(FadeIn(sv, shift=RIGHT * 0.3), FadeIn(cv), FadeIn(lv), run_time=0.8)
        self.at("La moyenne a une")
        cm = T(f"C = {math.hypot(ma, mb):.2f}".replace(".", ","), 24, INK).next_to(sm, UP, buff=0.2)
        lm = T("moyenne", 20, MUTED).next_to(sm, DOWN, buff=0.2)
        self.play(FadeIn(sm, shift=RIGHT * 0.3), FadeIn(cm), FadeIn(lm), run_time=0.8)
        self.at("Les outils")
        tag = T("outils classiques", 20, DANGER).next_to(lm, DOWN, buff=0.15)
        self.play(FadeIn(tag), run_time=0.5)
        self.at("C'est pourquoi")
        self.play(Indicate(sm, color=DANGER, scale_factor=1.06), run_time=1.0)
        self.at("ColorCatchers garde")
        box = SurroundingRectangle(VGroup(sv, sm, cv, lv, lm), color=ACCENT, buff=0.18, corner_radius=0.1)
        bl = T("ColorCatchers garde les deux", 22, ACCENT).next_to(box, DOWN, buff=0.55)
        self.play(Create(box), FadeIn(bl), run_time=0.9)
        self.finish()


# ======================================================================= S03
class S03(N):
    key = "s03_oklab"
    card = ('Chapitre 3 · Problème 2', "Mesurer l'écart entre deux couleurs", 'gamma · sRGB · OKLab')

    def construct(self):
        self.at("Deuxième problème")
        title = scene_title("Pourquoi un espace de couleur ?")
        self.play(Write(title), run_time=1.0)

        self.at("La caméra donne")
        chans = VGroup(*[
            VGroup(Rectangle(width=2.6, height=0.36, stroke_width=0).set_fill(color=[BLACK, c], opacity=1).set_sheen_direction(RIGHT),
                   T(n, 22, INK)).arrange(LEFT, buff=0.25)
            for n, c in [("R", "#ff0000"), ("V", "#00ff00"), ("B", "#0000ff")]
        ]).arrange(DOWN, buff=0.25, aligned_edge=RIGHT).move_to(LEFT * 3.6 + UP * 0.4)
        cl = T("sRGB : 0 → 255 par canal", 22, MUTED).next_to(chans, DOWN, buff=0.3)
        self.play(FadeIn(chans, lag_ratio=0.2), FadeIn(cl), run_time=1.0)
        self.at("Ces valeurs ont")
        self.cap("Deux défauts.", 28, ACCENT)

        self.at("Premièrement")
        ax = Axes(x_range=[0, 255, 64], y_range=[0, 1, 0.25], x_length=5.2, y_length=3.6, tips=False,
                  axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": False}).move_to(RIGHT * 2.9 + UP * 0.2)
        xl = T("valeur sRGB", 20, MUTED).next_to(ax.x_axis, DOWN, buff=0.15)
        yl = T("lumière réelle", 20, MUTED).next_to(ax.y_axis, UP, buff=0.12)
        curve = ax.plot(lambda v: (v / 255 / 12.92) if v / 255 <= 0.04045 else ((v / 255 + 0.055) / 1.055) ** 2.4, x_range=[0, 255], color=ACCENT, stroke_width=4)
        lin = DashedLine(ax.c2p(0, 0), ax.c2p(255, 1), color=FAINT)
        self.play(Create(ax), FadeIn(xl), FadeIn(yl), Create(lin), run_time=0.8)
        self.play(Create(curve), run_time=1.2)
        self.cap("Courbe gamma")
        self.at("La valeur cent")
        p = ax.c2p(128, 0.2159)
        g1 = DashedLine(ax.c2p(128, 0), p, color=INK, dash_length=0.06)
        g2 = DashedLine(p, ax.c2p(0, 0.2159), color=INK, dash_length=0.06)
        gl = T("128 → 22 %", 24, INK).next_to(p, RIGHT, buff=0.2).shift(UP * 0.1)
        self.play(Create(g1), Create(g2), FadeIn(Dot(p, color=INK)), FadeIn(gl), run_time=1.2)

        self.at("Une moyenne directe")
        self.play(*[FadeOut(m) for m in (chans, cl)], run_time=0.4)
        r, g = sw((255, 0, 0), 0.9), sw((0, 255, 0), 0.9)
        plus = T("+", 30, INK)
        row = VGroup(r, plus, g).arrange(RIGHT, buff=0.25).move_to(LEFT * 3.6 + UP * 1.2)
        self.play(FadeIn(row), run_time=0.6)
        self.at("Ici, le mélange")
        a1, a2 = sw((128, 128, 0), 1.2), sw((188, 188, 0), 1.2)
        res = VGroup(a1, a2).arrange(RIGHT, buff=0.5).next_to(row, DOWN, buff=0.6)
        l1 = T("moyenne sRGB", 18, DANGER).next_to(a1, DOWN, buff=0.15)
        l2 = T("moyenne en lumière", 18, ACCENT).next_to(a2, DOWN, buff=0.15)
        self.play(FadeIn(a1, shift=DOWN * 0.2), FadeIn(l1), run_time=0.7)
        self.play(FadeIn(a2, shift=DOWN * 0.2), FadeIn(l2), run_time=0.7)

        self.at("Deuxièmement")
        self.wipe(keep=[title])
        self.cap("Les distances sRGB\nne suivent pas la vision.")
        def pair(c1, c2, de, y):
            s1, s2 = sw(c1, 1.4), sw(c2, 1.4)
            grp = VGroup(s1, s2).arrange(RIGHT, buff=0).move_to(RIGHT * 0.2 + UP * y)
            d1 = T("Δ RGB = 40", 22, INK).next_to(grp, RIGHT, buff=0.5)
            d2 = T(f"ΔE OK = {de}", 22, ACCENT).next_to(d1, RIGHT, buff=0.5)
            return grp, d1, d2
        b = pair((0, 0, 50), (0, 40, 50), "0,135", 1.1)
        gg = pair((0, 230, 0), (40, 230, 0), "0,006", -1.0)
        self.at("Ces deux bleus")
        self.play(FadeIn(b[0]), FadeIn(b[1]), run_time=0.7)
        self.at("La différence est très")
        self.play(FadeIn(b[2]), FadeIn(T("très visible", 20, MUTED).next_to(b[0], DOWN, buff=0.12)), run_time=0.6)
        self.at("Ces deux verts")
        self.play(FadeIn(gg[0]), FadeIn(gg[1]), run_time=0.7)
        self.at("La différence est presque")
        self.play(FadeIn(gg[2]), FadeIn(T("presque invisible", 20, MUTED).next_to(gg[0], DOWN, buff=0.12)), run_time=0.6)

        self.at("Pour ces deux raisons")
        self.wipe()
        title2 = scene_title("L'espace OKLab")
        tg = tech("Björn Ottosson, 2020 · espace perceptuellement uniforme", title2)
        self.play(FadeIn(title2), FadeIn(tg), run_time=0.8)
        self.at("La conversion")
        steps = VGroup(*[T(s, 22, INK) for s in ["sRGB", "retirer le gamma", "cônes L, M, S", "racine cubique", "OKLab"]]).arrange(RIGHT, buff=0.75).move_to(UP * 0.2)
        steps[-1].set_color(ACCENT)
        arrs = VGroup(*[arrow(steps[i].get_right(), steps[i + 1].get_left()) for i in range(4)])
        for i in range(5):
            self.play(FadeIn(steps[i], shift=RIGHT * 0.2), *([GrowArrow(arrs[i - 1])] if i else []), run_time=0.45)
        self.at("Dans OKLab, une")
        self.cap("Distance égale = différence visible égale", 24, ACCENT_SOFT)
        self.wait(1.0)

        self.at("L'axe L")
        self.play(FadeOut(steps), FadeOut(arrs), run_time=0.4)
        self.uncap()
        center = RIGHT * 2.4 + DOWN * 0.5
        K = 13
        r = 0.24 * K
        bar = Rectangle(width=0.55, height=5.0, stroke_width=0).set_fill(color=[BLACK, WHITE], opacity=1).set_sheen_direction(UP).move_to(LEFT * 4.4 + DOWN * 0.5)
        bl = VGroup(T("L · clarté", 22, INK).next_to(bar, UP, buff=0.2),
                    T("0  noir", 20, MUTED).next_to(bar, RIGHT, buff=0.2).align_to(bar, DOWN),
                    T("1  blanc", 20, MUTED).next_to(bar, RIGHT, buff=0.2).align_to(bar, UP))
        self.play(GrowFromEdge(bar, DOWN), FadeIn(bl), run_time=1.0)
        self.at("L'axe a")
        ax_a = Arrow(center + LEFT * r, center + RIGHT * r, buff=0, stroke_width=6, max_tip_length_to_length_ratio=0.04)
        ax_a.set_color([lab_hex(0.7, -0.2, 0), lab_hex(0.65, 0.2, 0)])
        la = VGroup(T("a", 24, INK).next_to(ax_a, RIGHT, buff=0.12), T("vert", 18, MUTED).next_to(ax_a.get_start(), DOWN, buff=0.12),
                    T("rouge", 18, MUTED).next_to(ax_a.get_end(), DOWN, buff=0.12).shift(LEFT * 0.3))
        self.play(GrowArrow(ax_a), FadeIn(la), run_time=1.0)
        self.at("L'axe b")
        ax_b = Arrow(center + DOWN * r, center + UP * r, buff=0, stroke_width=6, max_tip_length_to_length_ratio=0.04)
        ax_b.set_color([lab_hex(0.5, 0, -0.2), lab_hex(0.88, 0, 0.18)])
        lb = VGroup(T("b", 24, INK).next_to(ax_b, UP, buff=0.12), T("bleu", 18, MUTED).next_to(ax_b.get_start(), LEFT, buff=0.12),
                    T("jaune", 18, MUTED).next_to(ax_b.get_end(), LEFT, buff=0.12).shift(DOWN * 0.3))
        self.play(GrowArrow(ax_b), FadeIn(lb), run_time=1.0)
        ring = VGroup()
        for k in range(72):
            hh = 2 * math.pi * k / 72
            a, b2 = 0.13 * math.cos(hh), 0.13 * math.sin(hh)
            ring.add(Dot(ab_pos(a, b2, center, K), radius=0.075, color=lab_hex(0.72, a, b2)))
        self.play(LaggedStart(*[FadeIn(d, scale=0.2) for d in ring], lag_ratio=0.01), run_time=0.9)
        self.at("Les gris")
        grey = Dot(center, radius=0.12, color="#a0a0a0").set_stroke(INK, 2)
        self.play(FadeIn(grey, scale=0.3), FadeIn(T("gris", 20, INK).next_to(grey, DL, buff=0.1)), run_time=0.7)
        h0 = math.radians(62)
        self.at("La distance à cet")
        rad = Line(center, ab_pos(0.13 * math.cos(h0), 0.13 * math.sin(h0), center, K), color=ACCENT, stroke_width=5)
        cl = T("C : chroma = √(a² + b²)", 24, ACCENT).to_corner(UR, buff=0.6)
        self.play(Create(rad), FadeIn(cl), run_time=1.0)
        self.at("L'angle autour")
        arc = Arc(radius=0.8, start_angle=0, angle=h0, arc_center=center, color=ACCENT_SOFT, stroke_width=4)
        hl = T("h : teinte = atan2(b, a)", 24, ACCENT_SOFT).next_to(cl, DOWN, buff=0.2, aligned_edge=LEFT)
        self.play(Create(arc), FadeIn(hl), run_time=0.9)

        self.at("Attention")
        self.play(FadeOut(rad), FadeOut(arc), ring.animate.set_opacity(0.35), run_time=0.6)
        self.cap("Attention : la teinte est un angle.", 24, DANGER, corner=DL)
        self.at("Trois cent")
        pa = ab_pos(0.13 * math.cos(math.radians(-1)), 0.13 * math.sin(math.radians(-1)), center, K)
        pb = ab_pos(0.13 * math.cos(math.radians(1)), 0.13 * math.sin(math.radians(1)), center, K)
        da = Dot(pa + DOWN * 0.08, radius=0.14, color=lab_hex(0.72, 0.13, -0.002)).set_stroke(INK, 2)
        db = Dot(pb + UP * 0.08, radius=0.14, color=lab_hex(0.72, 0.13, 0.002)).set_stroke(INK, 2)
        ta = VGroup(T("359°", 20, INK).next_to(da, DR, buff=0.05), T("1°", 20, INK).next_to(db, UR, buff=0.05))
        self.play(FadeIn(da), FadeIn(db), FadeIn(ta), run_time=0.8)
        self.at("Leur moyenne")
        pw = ab_pos(-0.13, 0, center, K)
        dw = Dot(pw, radius=0.16, color=lab_hex(0.72, -0.13, 0)).set_stroke(DANGER, 3)
        tw = T("180°", 20, DANGER).next_to(dw, UL, buff=0.08)
        self.play(TransformFromCopy(VGroup(da, db), dw), FadeIn(tw), run_time=1.0)
        self.at("Ce résultat")
        cross = VGroup(Line(pw + UL * 0.25, pw + DR * 0.25), Line(pw + DL * 0.25, pw + UR * 0.25)).set_stroke(DANGER, 5)
        self.play(Create(cross), run_time=0.6)
        self.at("Donc, ColorCatchers")
        ok = Dot(ab_pos(0.13, 0, center, K) + RIGHT * 0.32, radius=0.16, color=lab_hex(0.72, 0.13, 0)).set_stroke(ACCENT, 4)
        self.play(TransformFromCopy(VGroup(da, db), ok), run_time=0.9)
        self.cap("Moyenne sur (L, a, b) : correcte.", 24, ACCENT, corner=DL)
        self.finish()


# ======================================================================= S04
class S04(N):
    key = "s04_echantillonner"
    card = ('Chapitre 4 · Étape 1', 'Échantillonner', 'stride')

    def construct(self):
        self.at("Étape un")
        title = step_title(1, "Échantillonner")
        self.play(Write(title), run_time=1.0)
        g = SD["grid35"]
        gw, gh, cells = g["gw"], g["gh"], g["cells"]
        s = 0.24
        grid = VGroup()
        for i, c in enumerate(cells):
            x, y = i % gw, i // gw
            grid.add(Square(s, stroke_width=0.6, stroke_color=BG).set_fill(hexc(c), 1).move_to(np.array([(x - (gw - 1) / 2) * s, ((gh - 1) / 2 - y) * s, 0])))
        grid.move_to(UP * 0.1)
        self.at("Une image")
        cap0 = T("1920 × 1080 ≈ 2 073 600 pixels", 26, INK).next_to(grid, UP, buff=0.3)
        self.play(FadeIn(grid, lag_ratio=0.002), FadeIn(cap0), run_time=1.6)
        self.at("L'application calcule")
        self.cap("≈ 5 extractions par seconde, sur un téléphone")
        self.at("Elle ne peut")
        self.play(grid.animate.set_opacity(0.18), run_time=0.9)
        self.at("Pour une image")
        keep_idx = [i for i in range(len(cells)) if (i % gw) % 7 == 3 and (i // gw) % 7 == 3]
        self.play(*[grid[i].animate.set_opacity(1).set_stroke(ACCENT, 2.5) for i in keep_idx], run_time=1.0)
        formula = T("pas = ⌈ √(2 073 600 ÷ 46 000) ⌉ = 7", 24, ACCENT).next_to(grid, DOWN, buff=0.3)
        self.play(FadeIn(formula, shift=UP * 0.2), run_time=0.7)
        self.at("Ce pas fixe")
        tg = tech("stride · sous-échantillonnage à pas fixe", title)
        self.play(FadeIn(tg, shift=DOWN * 0.1), run_time=0.6)
        self.at("Le pas est régulier")
        self.cap("Pourquoi un pas régulier ?", 24, ACCENT)
        self.at("Une grille")
        lines = VGroup()
        for gx in range(3, gw, 7):
            lines.add(Line(grid[gx].get_top(), grid[gx + gw * (gh - 1)].get_bottom(), stroke_width=1.5, color=ACCENT_SOFT))
        for gy in range(3, gh, 7):
            lines.add(Line(grid[gy * gw].get_left(), grid[gy * gw + gw - 1].get_right(), stroke_width=1.5, color=ACCENT_SOFT))
        self.play(Create(lines), run_time=1.2)
        self.at("Chaque zone")
        self.cap("Chaque zone de l'image a le même poids.")
        self.at("L'application garde")
        cnt = T("275 × 155 = 42 625 pixels lus (max 46 000)", 26, INK).move_to(cap0)
        self.play(ReplacementTransform(cap0, cnt), run_time=0.9)
        self.at("Les proportions")
        self.uncap()
        self.play(FadeOut(grid), FadeOut(lines), FadeOut(formula), FadeOut(cnt), run_time=0.5)
        dist = SD["dist"]
        rows = VGroup()
        for label, shares in [("image entière", dist["full"]), ("échantillon", dist["samp"])]:
            segs = VGroup(*[Rectangle(width=max(0.02, 9 * sh), height=0.7, stroke_width=0).set_fill(hexc((c["r"], c["g"], c["b"])), 1) for c, sh in zip(PAL16, shares)]).arrange(RIGHT, buff=0)
            rows.add(VGroup(T(label, 24, MUTED), segs).arrange(RIGHT, buff=0.4))
        rows.arrange(DOWN, buff=0.5, aligned_edge=RIGHT).move_to(UP * 0.4)
        self.play(LaggedStart(*[FadeIn(r, shift=RIGHT * 0.3) for r in rows], lag_ratio=0.4), run_time=1.3)
        self.at("Cette méthode")
        self.cap("Limite", 26, DANGER)
        self.at("Une couleur sur")
        dots = VGroup(*[Square(0.5, stroke_color=ACCENT, stroke_width=2).set_fill(MUTED, 0.3) for _ in range(5)]).arrange(RIGHT, buff=0.45).move_to(DOWN * 1.6)
        speck = Square(0.12, stroke_width=0).set_fill("#ff2fa0", 1).move_to((dots[1].get_center() + dots[2].get_center()) / 2)
        sl = T("< 0,1 % des pixels : peut disparaître", 22, INK).next_to(dots, DOWN, buff=0.3)
        self.play(FadeIn(dots), FadeIn(speck, scale=3), FadeIn(sl), run_time=0.8)
        self.at("C'est un choix")
        self.play(FadeOut(speck, scale=0.2), run_time=0.8)
        self.cap("Choix : ces détails sont souvent du bruit.")
        self.finish()


# ======================================================================= S05 (quantifier)
class S05(N):
    key = "s05_quantifier"
    card = ('Chapitre 5 · Étape 2', 'Découper', 'quantification · coupe médiane')

    def construct(self):
        self.at("Étape deux")
        title = step_title(2, "Découper")
        self.play(Write(title), run_time=1.0)
        self.at("Cette étape")
        tg = tech("quantification (quantization)", title)
        self.play(FadeIn(tg, shift=DOWN * 0.1), run_time=0.6)

        self.at("Quantifier, c'est")
        nl = NumberLine(x_range=[0, 10, 1], length=9, color=MUTED, include_numbers=False).move_to(UP * 0.4)
        nums = VGroup(*[T(str(i), 20, MUTED).next_to(nl.n2p(i), DOWN, buff=0.2) for i in range(11)])
        self.play(Create(nl), FadeIn(nums), run_time=0.8)
        v = Dot(nl.n2p(3.37), radius=0.12, color=ACCENT)
        vl = T("3,37", 22, ACCENT).next_to(v, UP, buff=0.2)
        self.play(FadeIn(v), FadeIn(vl), run_time=0.5)
        self.play(v.animate.move_to(nl.n2p(3)), vl.animate.next_to(nl.n2p(3), UP, buff=0.32), run_time=1.0)
        self.play(Transform(vl, T("3", 22, ACCENT).next_to(nl.n2p(3), UP, buff=0.32)), run_time=0.4)
        self.at("Exemple")
        self.cap("Exemple : 3,37 cm → 3 cm")

        self.at("Chaque canal")
        self.play(FadeOut(nl), FadeOut(nums), FadeOut(v), FadeOut(vl), run_time=0.4)
        self.uncap()
        smooth = Rectangle(width=9, height=0.6, stroke_width=0).set_fill(color=["#000000", "#ff2a00"], opacity=1).set_sheen_direction(RIGHT).move_to(UP * 1.2)
        sl = T("256 niveaux", 22, MUTED).next_to(smooth, LEFT, buff=0.3)
        self.play(FadeIn(smooth), FadeIn(sl), run_time=0.8)
        self.at("Trois canaux donnent plus")
        big = T("256³ = 16 777 216 couleurs", 30, INK).move_to(DOWN * 0.3)
        self.play(Write(big), run_time=1.2)
        self.at("C'est trop")
        self.play(Indicate(big, color=DANGER), run_time=0.9)

        self.at("ColorCatchers garde")
        self.play(FadeOut(big), run_time=0.3)
        bits = "10110110"
        boxes = VGroup(*[VGroup(Square(0.6, stroke_color=INK if i < 5 else FAINT, stroke_width=2), T(b, 26, INK if i < 5 else MUTED)) for i, b in enumerate(bits)]).arrange(RIGHT, buff=0.06).move_to(DOWN * 0.4)
        for bx in boxes:
            bx[1].move_to(bx[0])
        bl = T("valeur 182 = 1011 0110", 20, MUTED).next_to(boxes, UP, buff=0.2)
        self.play(FadeIn(boxes, lag_ratio=0.1), FadeIn(bl), run_time=0.9)
        self.play(*[boxes[i].animate.set_opacity(0.2) for i in (5, 6, 7)], run_time=0.6)
        sh = T("r ≫ 3 : on garde 5 bits", 22, ACCENT).next_to(boxes, DOWN, buff=0.25)
        self.play(FadeIn(sh), run_time=0.5)
        self.at("Chaque canal a alors")
        steps = VGroup(*[Rectangle(width=9 / 32, height=0.6, stroke_width=0).set_fill(hexc((int((k + 0.5) * 8), int((k + 0.5) * 8 * 42 / 255), 0)), 1) for k in range(32)]).arrange(RIGHT, buff=0).next_to(smooth, DOWN, buff=0.15)
        stl = T("32 niveaux", 22, ACCENT).next_to(steps, LEFT, buff=0.3)
        self.play(FadeIn(steps, lag_ratio=0.03), FadeIn(stl), run_time=1.0)

        self.at("L'image change")
        self.wipe(keep=[title, tg])
        imgs = Group(*[ImageMobject(str(HERE / f"post{b}.png")).set_height(3.2) for b in (8, 5, 2)]).arrange(RIGHT, buff=0.4).move_to(UP * 0.1)
        labs = VGroup(*[T(t, 22, c).next_to(im, DOWN, buff=0.2) for t, c, im in zip(["8 bits (original)", "5 bits (ColorCatchers)", "2 bits (pour comparer)"], [MUTED, ACCENT, MUTED], imgs)])
        self.play(LaggedStart(*[FadeIn(i) for i in imgs], lag_ratio=0.3), FadeIn(labs), run_time=1.4)

        self.at("Trois canaux donnent trente")
        self.play(FadeOut(imgs), FadeOut(labs), run_time=0.5)
        t32 = T("32³ = 32 768 cases", 30, INK).move_to(UP * 2.0)
        self.play(Write(t32), run_time=1.0)
        self.at("Ce tableau")
        bins = HIST["bins"]
        mx = bins[0][1]
        bars = VGroup(*[Rectangle(width=0.2, height=max(0.04, 3.2 * (c ** 0.5) / (mx ** 0.5)), stroke_width=0).set_fill(hexc((r, g, b)), 1) for _, c, r, g, b in bins]).arrange(RIGHT, buff=0.04, aligned_edge=DOWN).move_to(DOWN * 0.9)
        base = Line(bars.get_corner(DL) + LEFT * 0.1, bars.get_corner(DR) + RIGHT * 0.1, color=MUTED)
        hl = T("histogramme : les 48 cases les plus remplies (image du chapitre)", 20, MUTED).next_to(base, DOWN, buff=0.2)
        self.play(Create(base), LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars], lag_ratio=0.02), FadeIn(hl), run_time=1.6)
        self.at("Chaque case compte")
        cl = T(f"{mx:,} pixels".replace(",", " "), 20, INK).next_to(bars[0], UP, buff=0.15)
        self.play(Indicate(bars[0], color=ACCENT), FadeIn(cl), run_time=1.0)

        self.at("La quantification a deux")
        self.wipe(keep=[title, tg])
        self.cap("Pourquoi quantifier ?", 28, ACCENT, corner=UR)
        self.at("Premièrement")
        rnd = random.Random(4)
        base_c = (180, 90, 40)
        noisy = VGroup(*[Dot(LEFT * 3 + UP * 0.2 + np.array([rnd.gauss(0, 0.5), rnd.gauss(0, 0.5), 0]), radius=0.09,
                             color=hexc(tuple(max(0, min(255, v + rnd.randint(-6, 6))) for v in base_c))) for _ in range(16)])
        self.play(FadeIn(noisy, lag_ratio=0.05), run_time=0.8)
        cell = Square(0.9, stroke_color=ACCENT, stroke_width=3).set_fill(hexc((180, 92, 44)), 1).move_to(RIGHT * 1.2 + UP * 0.2)
        self.play(*[d.animate.move_to(cell.get_center()) for d in noisy], run_time=1.0)
        self.play(FadeIn(cell), FadeOut(noisy), run_time=0.4)
        self.play(FadeIn(T("16 pixels proches → 1 case", 22, INK).next_to(cell, DOWN, buff=0.3)), run_time=0.5)
        self.at("Une partie")
        self.play(FadeIn(T("bruit absorbé", 22, ACCENT_SOFT).next_to(cell, RIGHT, buff=0.4)), run_time=0.5)
        self.at("Deuxièmement")
        mem = T("32 768 cases × 4 octets = 128 Ko", 26, INK).move_to(DOWN * 2.0)
        self.play(Write(mem), run_time=1.2)
        self.at("Le tableau occupe")
        self.play(FadeIn(T("taille fixe, quelle que soit l'image", 22, MUTED).next_to(mem, DOWN, buff=0.2)), run_time=0.6)
        self.at("Un outil")
        tg2 = tech("color quantizer", tg)
        self.play(FadeIn(tg2, shift=DOWN * 0.1), run_time=0.6)
        self.finish()


# ======================================================================= S06 (median cut)
class S06(N):
    key = "s06_decouper"

    def construct(self):
        title = step_title(2, "Découper")
        self.add(title)
        raw = SD["pts_05"]
        size = 5.0
        origin = LEFT * 5.4 + DOWN * 3.5
        unit = size / 256
        q = [((p[0] >> 3), (p[2] >> 3)) for p in raw]
        axes = VGroup(
            Arrow(origin, origin + RIGHT * (size + 0.3), buff=0, stroke_width=2, color=MUTED, max_tip_length_to_length_ratio=0.03),
            Arrow(origin, origin + UP * (size + 0.3), buff=0, stroke_width=2, color=MUTED, max_tip_length_to_length_ratio=0.03),
        )
        axl = VGroup(T("R", 20, MUTED).next_to(axes[0], RIGHT, buff=0.1), T("B", 20, MUTED).next_to(axes[1], UP, buff=0.1))
        lines = VGroup()
        for k in range(33):
            t = k * 8 * unit
            lines.add(Line(origin + RIGHT * t, origin + RIGHT * t + UP * size, stroke_width=0.6, color=FAINT))
            lines.add(Line(origin + UP * t, origin + UP * t + RIGHT * size, stroke_width=0.6, color=FAINT))
        dots = VGroup(*[Dot(origin + np.array([(qx + 0.5) * 8 * unit, (qy + 0.5) * 8 * unit, 0]), radius=0.04, color=hexc(p)) for p, (qx, qy) in zip(raw, q)])

        def rect_for(idx):
            xs = [q[i][0] for i in idx]
            ys = [q[i][1] for i in idx]
            x0, x1, y0, y1 = min(xs), max(xs) + 1, min(ys), max(ys) + 1
            r = Rectangle(width=(x1 - x0) * 8 * unit, height=(y1 - y0) * 8 * unit, stroke_color=ACCENT, stroke_width=2.5)
            return r.move_to(origin + np.array([(x0 + x1) / 2 * 8 * unit, (y0 + y1) / 2 * 8 * unit, 0]))

        self.at("Ensuite, l'application groupe")
        self.play(Create(axes), FadeIn(axl), Create(lines, lag_ratio=0.01), FadeIn(dots, lag_ratio=0.002), run_time=1.4)
        self.play(FadeIn(T("projection sur R et B (l'application utilise R, V, B)", 18, MUTED).next_to(axes[0], DOWN, buff=0.2).align_to(axes[0], LEFT)), run_time=0.5)
        self.at("L'algorithme")
        tg = tech("median cut · ColorCutQuantizer", title)
        self.play(FadeIn(tg, shift=DOWN * 0.1), run_time=0.6)
        self.at("Paul Heckbert")
        tg2 = tech("Paul Heckbert, 1982", tg)
        self.play(FadeIn(tg2, shift=DOWN * 0.1), run_time=0.6)

        self.at("D'abord")
        box0 = rect_for(list(range(len(q))))
        self.play(Create(box0), run_time=0.9)
        self.at("Elle choisit")
        self.play(box0.animate.set_fill(ACCENT, 0.12), run_time=0.6)
        self.cap("volume = étendue des couleurs", 22, MUTED, corner=UR)
        self.at("Elle coupe")
        b1, _ = median_cut_2d(q, 2)
        r1 = VGroup(*[rect_for(b) for b in b1])
        self.play(ReplacementTransform(box0, r1), run_time=1.1)
        self.at("La coupe est")
        c1 = VGroup(*[T(str(len(b)), 22, INK).move_to(r.get_center()).add_background_rectangle(color=BG, opacity=0.75, buff=0.06) for b, r in zip(b1, r1)])
        self.play(FadeIn(c1), run_time=0.5)
        self.cap("coupe à la médiane : 350 | 350 pixels", 22, MUTED, corner=UR)
        self.at("L'application répète")
        self.play(FadeOut(c1), run_time=0.3)
        cv = ValueTracker(2)
        counter = always_redraw(lambda: T(f"boîtes : {int(cv.get_value())}", 26, INK).move_to(RIGHT * 3.6 + UP * 1.6))
        self.add(counter)
        current = r1
        boxes = None
        for n in [4, 8, 16, 32, 55]:
            boxes, _ = median_cut_2d(q, n)
            rn = VGroup(*[rect_for(b) for b in boxes])
            self.play(ReplacementTransform(current, rn), cv.animate.set_value(n), run_time=0.5)
            current = rn
        self.uncap()

        self.at("La boîte la plus grande passe")
        self.cap("Pourquoi la boîte la plus grande ?", 24, ACCENT, corner=UR)
        self.at("Une grande boîte")
        pts_right = VGroup(T("une grande boîte = couleurs très différentes", 22, INK)).move_to(RIGHT * 3.4 + UP * 0.6)
        self.play(FadeIn(pts_right), run_time=0.5)
        self.at("La couper")
        self.play(FadeIn(T("la couper d'abord les sépare", 22, INK).next_to(pts_right, DOWN, buff=0.25)), run_time=0.5)
        self.at("Ainsi")
        def isolation(b):
            cx = sum(q[i][0] for i in b) / len(b)
            cy = sum(q[i][1] for i in b) / len(b)
            return min(math.hypot(cx - q[j][0], cy - q[j][1]) for j in range(len(q)) if j not in b) if len(b) < len(q) else 0
        small = max((b for b in boxes if 1 <= len(b) <= 12), key=isolation)
        hi = rect_for(small).set_stroke(INK, 5)
        self.play(Create(hi), Flash(hi, color=INK), run_time=0.9)
        self.play(FadeIn(T("petite couleur distincte : sa propre boîte", 22, ACCENT_SOFT).next_to(pts_right, DOWN, buff=0.85)), run_time=0.5)

        self.at("La coupe médiane a trois")
        self.play(*[FadeOut(m) for m in self.mobjects if m not in (title, tg, tg2, current, dots, axes, axl, lines, counter, self._cap)], run_time=0.4)
        self.cap("Pourquoi pas k-means ?", 24, ACCENT, corner=UR)
        hdr = VGroup(T("coupe médiane", 22, ACCENT), T("k-means", 22, MUTED)).arrange(RIGHT, buff=0.9).move_to(RIGHT * 3.4 + UP * 1.0)
        self.play(FadeOut(counter), FadeIn(hdr), run_time=0.5)
        rows = [("déterministe", "départ aléatoire"), ("entiers, une passe", "itératif, flottants"), ("stable en vidéo", "peut sauter")]
        rowm = []
        for k, (a, b) in enumerate(rows):
            ra = T("✓ " + a, 20, INK).move_to(hdr[0].get_center() + DOWN * (0.6 + 0.5 * k))
            rb = T("✗ " + b, 20, MUTED).move_to(hdr[1].get_center() + DOWN * (0.6 + 0.5 * k))
            rowm.append(VGroup(ra, rb))
        for frag, k in [("Elle est déterministe", 0), ("Elle est rapide", 1), ("Elle est stable", 2)]:
            self.at(frag)
            self.play(FadeIn(rowm[k], shift=UP * 0.1), run_time=0.5)
        self.at("Pour une vidéo")
        self.play(Indicate(rowm[2][0], color=ACCENT), run_time=0.9)

        self.at("Chaque boîte")
        self.play(FadeOut(hdr), *[FadeOut(r) for r in rowm], run_time=0.4)
        self.uncap()
        def chroma(p):
            _, a, b = rgb_to_oklab(*p)
            return math.hypot(a, b)
        pick = max((b for b in boxes if len(b) >= 12), key=lambda b: max(chroma(raw[i]) for i in b) - chroma(tuple(sum(raw[i][k] for i in b) / len(b) for k in range(3))))
        hi = rect_for(pick).set_stroke(INK, 5)
        self.play(current.animate.set_stroke(opacity=0.25), Create(hi), run_time=0.6)
        labs = [rgb_to_oklab(*raw[i]) for i in pick]
        mean = tuple(sum(l[k] for l in labs) / len(labs) for k in range(3))
        viv = max(pick, key=lambda i: chroma(raw[i]))
        smn = Square(1.4, stroke_width=0).set_fill(lab_hex(*mean), 1)
        svv = Square(1.4, stroke_width=0).set_fill(hexc(raw[viv]), 1)
        pair = VGroup(smn, svv).arrange(RIGHT, buff=0.4).move_to(RIGHT * 3.4 + DOWN * 0.2)
        self.play(TransformFromCopy(hi, smn), FadeIn(T("moyenne", 20, MUTED).next_to(smn, DOWN, buff=0.15)), run_time=0.8)
        self.at("la couleur moyenne")
        self.play(TransformFromCopy(dots[viv], svv), FadeIn(T("la plus vive", 20, MUTED).next_to(svv, DOWN, buff=0.15)), run_time=0.8)
        self.finish()


# ======================================================================= S07 (neutres)
class S07(N):
    key = "s07_neutres"
    card = ('Chapitre 6 · Étape 3', 'Choisir', 'neutres · sélection gloutonne · Tone')

    def construct(self):
        self.at("Étape trois")
        title = step_title(3, "Choisir")
        self.play(Write(title), run_time=1.0)
        center = RIGHT * 2.6 + DOWN * 0.3
        K = 13
        plane = ab_plane(center, K, 0.26)
        circles = VGroup(*[Circle(cand_radius(c["mass"]), stroke_color=BG, stroke_width=1.5).set_fill(mean_hex(c), 1).move_to(ab_pos(c["a"], c["b"], center, K)) for c in CANDS])
        self.at("Chaque boîte")
        lab = T("55 candidats", 22, MUTED).to_corner(UR, buff=0.6)
        self.play(Create(plane), LaggedStart(*[GrowFromCenter(c) for c in circles], lag_ratio=0.02), FadeIn(lab), run_time=1.5)
        self.at("D'abord")
        self.cap("neutres  |  couleurs", 26, INK)
        self.at("Le noir")
        self.cap("Pourquoi deux groupes ?", 24, ACCENT)
        white = max(range(len(CANDS)), key=lambda i: CANDS[i]["mass"])
        self.at("Le noir")
        self.play(Indicate(circles[white], color=INK, scale_factor=1.3), run_time=0.9)
        self.at("Un score")
        self.cap("score de vivacité du blanc ≈ 0")
        self.at("Pourtant")
        total = sum(c["mass"] for c in CANDS)
        self.cap(f"mais le blanc couvre {100 * CANDS[white]['mass'] / total:.0f} % de l'image".replace(".", ","))

        self.at("L'application calcule")
        ring = DashedVMobject(Circle(THR * K, color=ACCENT, stroke_width=3), num_dashes=24).move_to(center)
        rl = T(f"seuil = {THR:.3f}".replace(".", ","), 22, ACCENT).next_to(center, DR, buff=0.6)
        self.play(Create(ring), FadeIn(rl), run_time=1.0)
        self.at("Le seuil est")
        tg = tech("seuil adaptatif · percentile pondéré", title)
        self.play(FadeIn(tg), run_time=0.5)
        self.cap("seuil = ¼ × p90(chroma, pondéré)\nborné entre 0,02 et 0,045", 22)

        self.at("Le seuil change")
        self.cap("Pourquoi adaptatif ?", 24, ACCENT)
        beige = (214, 196, 168)
        row1 = VGroup(*[sw(c, 0.55) for c in [(90, 90, 90), (140, 140, 140), beige, (200, 200, 200)]]).arrange(RIGHT, buff=0.08)
        row2 = VGroup(*[sw(c, 0.55) for c in [(220, 30, 40), (30, 90, 220), beige, (250, 210, 0)]]).arrange(RIGHT, buff=0.08)
        demo = VGroup(row1, row2).arrange(DOWN, buff=0.7).move_to(LEFT * 4.2 + UP * 0.6)
        self.at("Un beige")
        self.play(FadeIn(row1), run_time=0.5)
        self.play(row1[2].animate.set_stroke(ACCENT, 4), FadeIn(T("scène grise : couleur", 20, INK).next_to(row1, DOWN, buff=0.12)), run_time=0.6)
        self.at("Dans une scène très")
        self.play(FadeIn(row2), run_time=0.5)
        self.play(row2[2].animate.set_stroke(MUTED, 4), FadeIn(T("scène vive : neutre", 20, INK).next_to(row2, DOWN, buff=0.12)), run_time=0.6)

        self.at("Un candidat sous")
        self.wipe(keep=[title, tg, plane, circles, ring, lab])
        zoom = VGroup(plane, circles, ring)
        self.play(zoom.animate.scale(3.2, about_point=center), run_time=1.0)
        nidx = [i for i, c in enumerate(CANDS) if c["c"] < THR]
        self.play(*[Indicate(circles[i], color=INK, scale_factor=1.3) for i in nidx], run_time=0.9)
        self.play(zoom.animate.scale(1 / 3.2, about_point=center), run_time=0.9)

        self.at("Les neutres ont")
        slots = VGroup(*[RoundedRectangle(corner_radius=0.06, width=0.7, height=1.1, stroke_color=MUTED, stroke_width=2) for _ in range(5)]).arrange(RIGHT, buff=0.15).move_to(LEFT * 3.9 + UP * 1.75)
        self.play(FadeIn(slots), run_time=0.5)
        self.play(slots[4].animate.set_stroke(ACCENT, 3), FadeIn(T("neutre", 18, ACCENT).next_to(slots[4], DOWN, buff=0.12)), run_time=0.5)
        self.cap("slot reservation : 3 places au maximum", 20, MUTED)

        self.at("L'application divise")
        self.uncap()
        bar_x, y0, y1 = -4.3, -3.2, 1.0
        ly = lambda L: y0 + (y1 - y0) * L
        bar = Line([bar_x, y0, 0], [bar_x, y1, 0], color=MUTED, stroke_width=2)
        seps = VGroup(*[DashedLine([bar_x - 0.9, ly(v), 0], [bar_x + 1.4, ly(v), 0], color=FAINT) for v in (0.34, 0.66)])
        names = VGroup(*[T(n, 18, MUTED).move_to([bar_x - 1.5, ly(m), 0]) for n, m in [("sombre", 0.17), ("moyen", 0.5), ("clair", 0.83)]])
        self.play(Create(bar), Create(seps), FadeIn(names), run_time=0.8)
        copies = VGroup(*[circles[i].copy().move_to([bar_x + 0.35 + 0.25 * (k % 3), ly(CANDS[i]["L"]), 0]) for k, i in enumerate(nidx)])
        self.play(*[TransformFromCopy(circles[i], copies[k]) for k, i in enumerate(nidx)], run_time=0.9)
        self.at("Un groupe doit")
        pct = VGroup()
        for lo, hi, mid in [(0, 0.34, 0.17), (0.34, 0.66, 0.5), (0.66, 1.01, 0.83)]:
            share = 100 * sum(c["mass"] for c in NEUTRALS if lo <= c["L"] < hi) / total
            pct.add(T(f"{share:.1f} %".replace(".", ","), 20, INK if share >= 5 else DANGER).move_to([bar_x + 1.9, ly(mid), 0]))
        self.play(FadeIn(pct, lag_ratio=0.3), run_time=0.9)
        self.cap("seuil de masse : 5 % des pixels", 20, MUTED)
        self.at("Cette limite")
        self.cap("élimine les gris des bords des objets", 20, INK)
        self.at("Dans chaque groupe")
        ws = [k for k, i in enumerate(nidx) if CANDS[i]["L"] >= 0.66]
        k = min(ws, key=lambda k: CANDS[nidx[k]]["c"])
        self.play(Indicate(copies[k], color=ACCENT, scale_factor=1.6), run_time=0.7)
        self.play(TransformFromCopy(copies[k], slots[4].copy().set_stroke(width=0).set_fill(mean_hex(CANDS[nidx[k]]), 1)), run_time=0.8)
        self.cap("exemplaire : la chroma la plus faible", 20, MUTED)
        self.finish()


# ======================================================================= S08 (couleurs)
class S08(N):
    key = "s08_couleurs"

    def construct(self):
        title = step_title(3, "Choisir")
        self.add(title)
        center = RIGHT * 3.0 + DOWN * 0.9
        K = 11
        plane = ab_plane(center, K, 0.27)
        picks = greedy()
        blended = [tuple(c[k2] + (c["vlab"][j] - c[k2]) * 0.9 for j, k2 in enumerate(("L", "a", "b"))) for c in CHROMA]
        circles = VGroup(*[Circle(cand_radius(c["mass"]), stroke_color=BG, stroke_width=1.5).set_fill(lab_hex(*bl), 1).move_to(ab_pos(bl[1], bl[2], center, K)) for c, bl in zip(CHROMA, blended)])
        self.at("Ensuite")
        self.play(Create(plane), LaggedStart(*[GrowFromCenter(c) for c in circles], lag_ratio=0.02), run_time=1.4)
        self.at("C'est une sélection")
        tg = tech("greedy selection", title)
        self.play(FadeIn(tg), run_time=0.5)
        self.at("Chaque candidat")
        terms = [("score =", INK), ("vivacité", INK), ("+ 0,6 × nouveauté", INK), ("+ 0,2 × rareté", INK), ("+ 0,3 × fidélité", MUTED)]
        formula = VGroup(*[T(t, 24, c) for t, c in terms]).arrange(RIGHT, buff=0.16).to_edge(UP, buff=0.5).shift(RIGHT * 1.9)
        self.play(FadeIn(formula, shift=DOWN * 0.2), run_time=0.8)

        def hl(idx):
            return [formula[j].animate.set_color(ACCENT if j == idx else INK) for j in (1, 2, 3)]
        self.at("Le score augmente")
        self.play(*hl(1), run_time=0.4)
        maxc = max(range(len(CHROMA)), key=lambda i: CHROMA[i]["vc"])
        self.play(Indicate(circles[maxc], color=INK, scale_factor=1.8), run_time=0.7)
        self.at("La vivacité est")
        self.cap("vivacité = chroma ÷ chroma max de l'image", 22)
        self.at("Ainsi, la méthode")
        pastel = VGroup(*[sw(c, 0.4) for c in [(240, 200, 200), (200, 225, 240), (230, 240, 200)]]).arrange(RIGHT, buff=0.05)
        neon = VGroup(*[sw(c, 0.4) for c in [(255, 0, 120), (0, 220, 255), (180, 255, 0)]]).arrange(RIGHT, buff=0.05)
        pn = VGroup(VGroup(pastel, T("pastel", 18, MUTED)).arrange(DOWN, buff=0.1), VGroup(neon, T("fluo", 18, MUTED)).arrange(DOWN, buff=0.1)).arrange(RIGHT, buff=0.6).move_to(LEFT * 4.5 + UP * 0.8)
        self.play(FadeIn(pn), run_time=0.6)
        self.at("aussi pour une teinte")
        self.play(*hl(2), FadeOut(pn), run_time=0.4)
        self.cap("nouveauté = écart de teinte avec les couleurs choisies", 20)
        self.at("Il augmente enfin")
        self.play(*hl(3), run_time=0.4)
        self.cap("rareté = 1 − population ÷ population max", 20)
        self.at("Ce bonus de rareté")
        self.cap("Pourquoi la rareté ?", 24, ACCENT)
        self.at("Une petite tache")
        small = sorted(range(len(CHROMA)), key=lambda i: CHROMA[i]["mass"])[:6]
        self.play(*[Indicate(circles[i], color=INK, scale_factor=2.0) for i in small], run_time=0.9)
        self.cap("petite tache : attire l'œil, peu de pixels", 20)
        self.at("Sans ce bonus")
        self.cap("sans bonus : les grandes zones gagnent toujours", 20)
        self.play(*[formula[j].animate.set_color(INK) for j in (1, 2, 3)], run_time=0.3)

        def zone_for(p):
            pos = ab_pos(p["a"], p["b"], center, K)
            disk = Circle(0.08 * K, color=ACCENT, stroke_width=2.5).set_fill(ACCENT, 0.08).move_to(pos)
            wedge = AnnularSector(inner_radius=0, outer_radius=0.27 * K, angle=math.radians(50), start_angle=math.radians(p["h"] - 25), arc_center=center, fill_color=ACCENT, fill_opacity=0.07, stroke_width=0)
            return disk, wedge

        def excluded(pl, disk_only=False):
            out = []
            for i, (L, a, b) in enumerate(blended):
                hh = math.degrees(math.atan2(b, a)) % 360
                for p in pl:
                    if p["c"] is CHROMA[i]:
                        break
                    d = math.dist((L, a, b), (p["L"], p["a"], p["b"]))
                    gap = min(abs(hh - p["h"]), 360 - abs(hh - p["h"]))
                    if d < 0.08 or (not disk_only and gap < 25):
                        out.append(i)
                        break
            return out
        pidx = [next(i for i, c in enumerate(CHROMA) if c is p["c"]) for p in picks]

        self.at("Après chaque choix")
        self.uncap()
        p0 = picks[0]
        disk0, wedge0 = zone_for(p0)
        self.play(Create(Circle(cand_radius(p0["c"]["mass"]) + 0.08, color=INK, stroke_width=4).move_to(circles[pidx[0]])), run_time=0.5)
        self.play(GrowFromCenter(disk0), run_time=0.7)
        self.at("C'est une contrainte")
        tg2 = tech("contrainte de répulsion (hard constraint)", tg)
        self.play(FadeIn(tg2), run_time=0.5)
        self.at("Un candidat dans")
        self.play(*[circles[i].animate.set_opacity(0.15) for i in excluded([p0], True)], run_time=0.7)
        self.at("La distance minimale")
        rline = Line(disk0.get_center(), disk0.get_center() + RIGHT * 0.08 * K, color=ACCENT, stroke_width=3)
        rlab = T("ΔE OK 0,08", 20, ACCENT).next_to(rline, UP, buff=0.08)
        self.play(Create(rline), FadeIn(rlab), run_time=0.6)
        self.at("L'écart de teinte")
        self.play(FadeIn(wedge0), run_time=0.6)
        self.cap("coin de teinte : ± 25°", 22, ACCENT_SOFT)
        self.play(*[circles[i].animate.set_opacity(0.15) for i in excluded([p0])], run_time=0.5)
        self.at("Il faut ces deux")
        self.cap("Pourquoi deux règles ?", 24, ACCENT)
        self.at("Deux rouges")
        reds = VGroup(sw(oklab_to_rgb(0.42, 0.16, 0.08), 0.8), sw(oklab_to_rgb(0.72, 0.16, 0.08), 0.8)).arrange(RIGHT, buff=0.3).move_to(LEFT * 4.6 + UP * 0.6)
        rd = T("ΔE OK 0,30, même teinte", 18, INK).next_to(reds, DOWN, buff=0.15)
        self.play(FadeIn(reds), FadeIn(rd), run_time=0.7)
        self.at("La répulsion est")
        self.play(FadeOut(reds), FadeOut(rd), run_time=0.3)
        self.cap("Pourquoi une règle stricte ?", 24, ACCENT)
        self.at("Une pénalité de score")
        self.cap("une pénalité peut perdre contre le score", 20)
        self.at("Une règle stricte garantit")
        self.cap("une règle stricte garantit des couleurs distinctes", 20, ACCENT_SOFT)
        self.at("Ainsi, la palette")
        self.play(FadeOut(rline), FadeOut(rlab), run_time=0.3)
        for k in range(1, len(picks)):
            p = picks[k]
            disk, wedge = zone_for(p)
            self.play(Create(Circle(cand_radius(p["c"]["mass"]) + 0.08, color=INK, stroke_width=4).move_to(circles[pidx[k]])), GrowFromCenter(disk), FadeIn(wedge),
                      *[circles[i].animate.set_opacity(0.15) for i in excluded(picks[: k + 1]) if i not in pidx], run_time=0.5)
        self.uncap()
        bars = palette_bars(PAL16, height=0.9, width=0.8).to_corner(DL, buff=0.6)
        self.play(FadeIn(bars, shift=UP * 0.3), run_time=0.6)
        self.finish()


# ======================================================================= S09 (tone)
class S09(N):
    key = "s09_tone"

    def construct(self):
        self.at("La couleur affichée")
        title = scene_title("Le réglage Tone")
        picks = greedy()
        p = max(picks, key=lambda x: math.dist((x["c"]["L"], x["c"]["a"], x["c"]["b"]), x["c"]["vlab"]))
        c = p["c"]
        m, v = (c["L"], c["a"], c["b"]), c["vlab"]
        center = RIGHT * 2.0 + DOWN * 0.4
        K = 16
        plane = ab_plane(center, K, 0.22)
        pm, pv = ab_pos(m[1], m[2], center, K), ab_pos(v[1], v[2], center, K)
        dm = Dot(pm, radius=0.14, color=lab_hex(*m)).set_stroke(INK, 2)
        dv = Dot(pv, radius=0.14, color=lab_hex(*v)).set_stroke(INK, 2)
        self.play(Write(title), Create(plane), FadeIn(dm), FadeIn(T("moyenne", 20, MUTED).next_to(dm, DOWN, buff=0.18)), run_time=1.2)
        self.at("L'application mélange")
        self.play(FadeIn(dv), FadeIn(T("la plus vive", 20, MUTED).next_to(dv, UP, buff=0.18)), Create(Line(pm, pv, color=MUTED, stroke_width=3)), run_time=0.9)
        self.at("C'est une interpolation")
        tg = tech("interpolation linéaire (lerp) dans OKLab", title)
        self.play(FadeIn(tg), run_time=0.5)
        self.cap("couleur = moyenne + (vive − moyenne) × Tone", 22)
        t = ValueTracker(0.5)
        mix = lambda: tuple(m[i] + (v[i] - m[i]) * t.get_value() for i in range(3))
        moving = always_redraw(lambda: Dot(ab_pos(mix()[1], mix()[2], center, K), radius=0.2, color=lab_hex(*mix())).set_stroke(ACCENT, 4))
        swatch = always_redraw(lambda: Square(2.2, stroke_width=0).set_fill(lab_hex(*mix()), 1).move_to(LEFT * 4.2 + UP * 0.5))
        s0, s1 = LEFT * 5.5 + DOWN * 1.8, LEFT * 2.9 + DOWN * 1.8
        track = Line(s0, s1, color=MUTED, stroke_width=4)
        knob = always_redraw(lambda: Dot(s0 + (s1 - s0) * t.get_value(), radius=0.13, color=ACCENT))
        val = always_redraw(lambda: T(f"Tone = {t.get_value():.2f}".replace(".", ","), 24, INK).next_to(track, UP, buff=0.3))
        self.at("Le réglage Tone")
        self.play(FadeIn(moving), FadeIn(swatch), Create(track), FadeIn(knob), FadeIn(val), run_time=0.9)
        self.at("À zéro")
        self.play(t.animate.set_value(0), run_time=1.3)
        self.at("À un")
        self.play(t.animate.set_value(1), run_time=1.5)
        self.at("La valeur par défaut")
        self.play(t.animate.set_value(0.9), run_time=1.0)
        self.at("Une valeur de un")
        self.cap("Pourquoi pas 1 ?", 24, ACCENT)
        self.at("Un seul pixel")
        self.cap("un pixel seul peut être une erreur du capteur", 20)
        self.at("Dix pour cent")
        self.cap("10 % de moyenne stabilisent le résultat", 20, ACCENT_SOFT)
        self.at("La couleur reste")
        self.play(Indicate(swatch, color=ACCENT, scale_factor=1.04), run_time=1.0)
        self.finish()


# ======================================================================= S10 (stabilité)
class S10(N):
    key = "s10_stabilite"
    card = ('Chapitre 7 · Étape 4', 'Lisser', 'hystérésis · alignement · filtres')

    def construct(self):
        self.at("Étape quatre")
        title = step_title(4, "Lisser")
        self.play(Write(title), run_time=1.0)
        base = [rgb_to_oklab(c["r"], c["g"], c["b"]) for c in PAL16]
        rnd = random.Random(5)
        bars = palette_bars(PAL16, height=1.6, width=1.0).move_to(RIGHT * 2.6 + UP * 1.6)
        self.at("La caméra bouge")
        self.play(FadeIn(bars), run_time=0.5)
        for _ in range(6):
            self.play(*[b.animate.set_fill(lab_hex(L + rnd.gauss(0, 0.03), a + rnd.gauss(0, 0.02), bb + rnd.gauss(0, 0.02)), 1) for b, (L, a, bb) in zip(bars, base)], run_time=0.15)
        self.at("Deux candidats")
        ca, cb = (229, 161, 76), (226, 132, 70)
        sa = VGroup(sw(ca, 0.5), Rectangle(width=0.612 * 5, height=0.4, stroke_width=0).set_fill(INK, 0.8)).arrange(RIGHT, buff=0.2)
        sb = VGroup(sw(cb, 0.5), Rectangle(width=0.609 * 5, height=0.4, stroke_width=0).set_fill(INK, 0.8)).arrange(RIGHT, buff=0.2)
        duel = VGroup(sa, sb).arrange(DOWN, buff=0.25, aligned_edge=LEFT).move_to(RIGHT * 2.6 + DOWN * 0.7)
        vals = VGroup(T("0,612", 20, INK).next_to(sa, RIGHT, buff=0.2), T("0,609", 20, INK).next_to(sb, RIGHT, buff=0.2))
        self.play(FadeIn(duel), FadeIn(vals), run_time=0.7)
        self.at("D'une extraction")
        for k in range(6):
            win = ca if k % 2 else cb
            self.play(bars[2].animate.set_fill(hexc(win), 1), sa[1].animate.stretch_to_fit_width(5 * (0.605 + 0.01 * (k % 2)), about_edge=LEFT),
                      sb[1].animate.stretch_to_fit_width(5 * (0.615 - 0.01 * (k % 2)), about_edge=LEFT), run_time=0.35)
        self.at("Sans protection")
        self.cap("la palette clignote", 22, DANGER)

        self.at("L'application utilise")
        self.uncap()
        self.play(FadeOut(duel), FadeOut(vals), FadeOut(bars), run_time=0.4)
        cards = VGroup(*[VGroup(T(n, 22, ACCENT, weight=SEMIBOLD), T(t, 21, INK)).arrange(RIGHT, buff=0.25) for n, t in [
            ("1", "fidélité · hystérésis"), ("2", "alignement · appariement glouton"), ("3", "moyenne glissante"), ("4", "zone morte · deadband"), ("5", "lissage exponentiel")]])
        cards.arrange(DOWN, buff=0.35, aligned_edge=LEFT).to_edge(LEFT, buff=0.7).shift(DOWN * 0.3)
        self.play(FadeIn(cards, lag_ratio=0.2, shift=RIGHT * 0.2), run_time=1.2)
        self.play(cards.animate.set_opacity(0.3), run_time=0.3)

        self.at("La première agit")
        self.play(cards[0].animate.set_opacity(1), run_time=0.4)
        ax = Axes(x_range=[0, 0.16, 0.04], y_range=[0, 1, 0.5], x_length=5.0, y_length=2.8, tips=False,
                  axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": False}).move_to(RIGHT * 2.9 + DOWN * 0.2)
        axl = VGroup(T("distance à la palette précédente", 18, MUTED).next_to(ax.x_axis, DOWN, buff=0.15), T("bonus", 18, MUTED).next_to(ax.y_axis, UP, buff=0.1))
        self.at("Les couleurs de la palette")
        self.play(Create(ax), FadeIn(axl), run_time=0.8)
        self.at("Le bonus est maximal")
        line = VMobject(stroke_color=ACCENT, stroke_width=5).set_points_as_corners([ax.c2p(0, 1), ax.c2p(0.1, 0), ax.c2p(0.16, 0)])
        self.play(Create(line), run_time=1.0)
        self.at("Il diminue")
        tick = VGroup(DashedLine(ax.c2p(0.1, 0), ax.c2p(0.1, 0.6), color=INK), T("0,1", 18, INK).next_to(ax.c2p(0.1, 0.6), UP, buff=0.1))
        self.play(FadeIn(tick), run_time=0.5)
        self.at("C'est une hystérésis")
        self.cap("pour changer, un rival doit être nettement meilleur", 20, ACCENT_SOFT, corner=DR)
        self.at("Quand la scène")
        mk = Dot(ax.c2p(0.01, 0.9), radius=0.12, color=INK)
        self.play(FadeIn(mk), run_time=0.3)
        self.play(MoveAlongPath(mk, VMobject().set_points_as_corners([ax.c2p(0.01, 0.9), ax.c2p(0.1, 0), ax.c2p(0.14, 0)])), run_time=1.4)
        self.at("Le bonus est nul")
        self.cap("bonus nul : la palette change librement", 20, INK, corner=DR)

        self.at("La deuxième protection")
        self.play(FadeOut(ax), FadeOut(axl), FadeOut(line), FadeOut(tick), FadeOut(mk), cards[0].animate.set_opacity(0.3), cards[1].animate.set_opacity(1), run_time=0.6)
        self.uncap()
        prev_cols = [(c["r"], c["g"], c["b"]) for c in PAL16]
        order = [3, 0, 4, 1, 2]
        prev = VGroup(*[sw(c, 0.7) for c in prev_cols]).arrange(RIGHT, buff=0.25).move_to(RIGHT * 2.9 + UP * 1.4)
        new = VGroup(*[sw(prev_cols[i], 0.7) for i in order]).arrange(RIGHT, buff=0.25).move_to(RIGHT * 2.9 + DOWN * 0.6)
        pl = T("palette précédente", 18, MUTED).next_to(prev, UP, buff=0.15)
        nl = T("nouvelle extraction", 18, MUTED).next_to(new, DOWN, buff=0.15)
        self.play(FadeIn(prev), FadeIn(pl), run_time=0.5)
        self.at("Les couleurs extraites")
        self.play(FadeIn(new), FadeIn(nl), run_time=0.6)
        self.at("L'application associe")
        arrs = VGroup(*[Arrow(new[j].get_top(), prev[order[j]].get_bottom(), buff=0.08, stroke_width=3, color=ACCENT, max_tip_length_to_length_ratio=0.12) for j in range(5)])
        self.play(LaggedStart(*[GrowArrow(a) for a in arrs], lag_ratio=0.15), run_time=1.2)
        self.cap("paires les plus proches d'abord (ΔE OK)", 20, ACCENT_SOFT, corner=DR)
        self.at("Sans alignement")
        self.play(FadeOut(arrs), run_time=0.3)
        wrong = VGroup(*[Line(new[j].get_top(), prev[j].get_bottom(), color=DANGER, stroke_width=3) for j in range(5)])
        self.play(Create(wrong), run_time=0.8)
        self.cap("sans alignement : tout semble changer", 20, DANGER, corner=DR)
        self.finish()


# ======================================================================= S11 (filtres)
class S11(N):
    key = "s11_filtres"

    def construct(self):
        title = step_title(4, "Lisser")
        self.add(title)
        cards = VGroup(*[VGroup(T(n, 22, ACCENT, weight=SEMIBOLD), T(t, 21, INK)).arrange(RIGHT, buff=0.25) for n, t in [
            ("3", "moyenne glissante"), ("4", "zone morte · deadband"), ("5", "lissage exponentiel")]])
        cards.arrange(DOWN, buff=0.4, aligned_edge=LEFT).to_edge(LEFT, buff=0.7).shift(UP * 1.2)
        self.at("Les trois dernières")
        self.play(FadeIn(cards, lag_ratio=0.2), run_time=0.9)
        self.play(cards.animate.set_opacity(0.3), run_time=0.3)

        ax = Axes(x_range=[0, 10, 1], y_range=[0.2, 0.9, 0.1], x_length=6.4, y_length=3.6, tips=False,
                  axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": False}).to_corner(UR, buff=0.6).shift(DOWN * 0.4)
        axl = VGroup(T("temps (s)", 18, MUTED).next_to(ax.x_axis, DOWN, buff=0.12), T("clarté L", 18, MUTED).next_to(ax.y_axis, UP, buff=0.1))
        rnd = random.Random(11)
        ts = [i * 0.2 for i in range(51)]
        raw = [(0.42 if t < 5 else 0.72) + rnd.gauss(0, 0.035) for t in ts]
        sma = [sum(raw[max(0, i - 4): i + 1]) / len(raw[max(0, i - 4): i + 1]) for i in range(len(raw))]
        self.at("Troisième protection")
        self.play(cards[0].animate.set_opacity(1), Create(ax), FadeIn(axl), run_time=0.8)
        rawdots = VGroup(*[Dot(ax.c2p(t, r), radius=0.04, color=MUTED) for t, r in zip(ts, raw)])
        self.at("L'application garde")
        self.play(LaggedStart(*[FadeIn(d, scale=0.3) for d in rawdots], lag_ratio=0.02), run_time=1.2)
        win = SurroundingRectangle(VGroup(*rawdots[10:15]), color=ACCENT, buff=0.08)
        self.play(Create(win), run_time=0.4)
        self.cap("fenêtre de 5 extractions ≈ 1 s", 20, MUTED, corner=DL)
        self.at("Pour chaque case")
        smac = VMobject(stroke_color=INK, stroke_width=3).set_points_as_corners([ax.c2p(t, s) for t, s in zip(ts, sma)])
        self.play(Create(smac), win.animate.move_to(VGroup(*rawdots[30:35])), run_time=1.6)
        self.play(FadeOut(win), run_time=0.3)
        self.at("Cette moyenne réduit")
        self.cap("Pourquoi ?", 24, ACCENT, corner=DL)
        self.at("Avec cinq mesures")
        self.cap("bruit ÷ √5 ≈ bruit ÷ 2,2", 24, INK, corner=DL)
        self.at("L'inconvénient")
        lag = DoubleArrow(ax.c2p(5, 0.8), ax.c2p(5.8, 0.8), buff=0, color=DANGER, stroke_width=3, max_tip_length_to_length_ratio=0.2)
        self.play(FadeIn(lag), FadeIn(T("retard", 18, DANGER).next_to(lag, UP, buff=0.08)), run_time=0.6)
        self.at("L'application calcule cette moyenne")
        pair = VGroup(sw((128, 128, 0), 0.6), sw((188, 188, 0), 0.6)).arrange(RIGHT, buff=0.15)
        lbl = VGroup(T("sRGB", 16, DANGER).next_to(pair[0], DOWN, buff=0.08), T("lumière", 16, ACCENT).next_to(pair[1], DOWN, buff=0.08))
        g = VGroup(pair, lbl).next_to(cards, DOWN, buff=0.6, aligned_edge=LEFT)
        self.play(FadeIn(g), run_time=0.5)
        self.cap("moyenne en OKLab : pas d'assombrissement", 20, INK, corner=DL)

        self.at("Quatrième protection")
        self.play(FadeOut(g), cards[0].animate.set_opacity(0.3), cards[1].animate.set_opacity(1), run_time=0.5)
        held = sma[20]
        band = Rectangle(width=abs(ax.c2p(4.8, 0)[0] - ax.c2p(0, 0)[0]), height=abs(ax.c2p(0, 0.08)[1] - ax.c2p(0, 0)[1]), stroke_width=0).set_fill(ACCENT, 0.18)
        band.move_to(ax.c2p(2.4, held))
        self.at("Un changement plus petit")
        self.play(FadeIn(band), run_time=0.6)
        self.cap("|Δ| < 0,04 : l'affichage ne bouge pas", 20, INK, corner=DL)
        self.at("Le seuil de perception")
        jnd = VGroup(sw(oklab_to_rgb(0.6, 0.1, 0.05), 0.6), sw(oklab_to_rgb(0.62, 0.1, 0.05), 0.6)).arrange(RIGHT, buff=0)
        jl = T("ΔE OK 0,02 : à peine visible", 16, MUTED).next_to(jnd, DOWN, buff=0.1)
        jg = VGroup(jnd, jl).next_to(cards, DOWN, buff=0.6, aligned_edge=LEFT)
        self.play(FadeIn(jg), run_time=0.5)
        self.at("La zone morte est donc")
        self.cap("zone morte = 2 × seuil de perception", 20, INK, corner=DL)
        self.at("Ainsi, le scintillement")
        self.cap("scintillement invisible → aucun mouvement", 20, ACCENT_SOFT, corner=DL)

        self.at("Cinquième protection")
        self.play(FadeOut(jg), FadeOut(band), FadeOut(smac), FadeOut(rawdots), FadeOut(lag), *[FadeOut(m) for m in self.mobjects if isinstance(m, Text) and m.text == "retard"],
                  cards[1].animate.set_opacity(0.3), cards[2].animate.set_opacity(1), run_time=0.5)
        self.uncap()
        ax2 = Axes(x_range=[0, 40, 10], y_range=[0, 1, 0.5], x_length=6.4, y_length=3.6, tips=False,
                   axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": False}).move_to(ax)
        ax2l = VGroup(T("images de l'écran (60 par seconde)", 18, MUTED).next_to(ax2.x_axis, DOWN, buff=0.12), T("part du chemin", 18, MUTED).next_to(ax2.y_axis, UP, buff=0.1))
        self.play(ReplacementTransform(ax, ax2), ReplacementTransform(axl, ax2l), run_time=0.6)
        self.at("Au-delà")
        f = T("x ← x + 0,16 · (cible − x)", 24, ACCENT).next_to(cards, DOWN, buff=0.6, aligned_edge=LEFT)
        self.play(Write(f), run_time=1.0)
        target = DashedLine(ax2.c2p(0, 1), ax2.c2p(40, 1), color=INK)
        self.play(Create(target), run_time=0.5)
        ys = [1 - 0.84 ** n for n in range(41)]
        edots = VGroup(*[Dot(ax2.c2p(n, y), radius=0.05, color=ACCENT) for n, y in enumerate(ys)])
        self.at("Le mouvement est rapide")
        self.play(LaggedStart(*[FadeIn(d, scale=0.3) for d in edots], lag_ratio=0.08), run_time=2.2)
        self.at("C'est un filtre")
        tg = tech("filtre passe-bas du premier ordre · EMA", title)
        self.play(FadeIn(tg), run_time=0.5)
        self.at("La couleur arrive")
        m95 = VGroup(DashedLine(ax2.c2p(17, 0), ax2.c2p(17, ys[17]), color=INK), T("95 % après 17 images ≈ 0,3 s", 18, INK).next_to(ax2.c2p(17, ys[17]), DR, buff=0.1))
        self.play(FadeIn(m95), Indicate(edots[17], color=INK, scale_factor=2.5), run_time=0.9)
        self.at("Quand l'écart")
        self.cap("écart < 0,01 : arrêt exact sur la cible", 20, ACCENT_SOFT, corner=DL)
        self.finish()


# ======================================================================= S12 (une couleur)
class S12(N):
    key = "s12_une_couleur"
    card = ('Chapitre 8', 'Mode une couleur', 'moyenne 9 × 9 · CIEDE2000')

    def construct(self):
        cr = SD["cross"]
        self.at("Mode une couleur")
        title = scene_title("Mode une couleur")
        img = ImageMobject(str(HERE / "cross.png")).set_height(3.5).move_to(LEFT * 3.7 + UP * 0.2)
        self.play(Write(title), FadeIn(img), run_time=1.2)
        self.at("Ici, vous visez")
        self.cap("vous visez un objet précis : pas de palette", 22)
        self.at("Une croix")
        c = img.get_center()
        cross = VGroup(*[Line(c + d * 0.5, c + d * 0.12, color=INK, stroke_width=3) for d in (LEFT, RIGHT, UP, DOWN)])
        self.play(Create(cross), run_time=0.7)
        px = img.height / 270
        sq = Square(9 * px, color=ACCENT, stroke_width=2).move_to(c)
        self.at("L'application lit")
        s = 0.3
        cells = VGroup(*[Square(s, stroke_width=1, stroke_color=BG).set_fill(hexc(rgb), 1).move_to(np.array([(i % 9 - 4) * s, (4 - i // 9) * s, 0])) for i, rgb in enumerate(cr["cells"])])
        cells.move_to(RIGHT * 1.5 + UP * 0.3)
        lab = T("9 × 9 = 81 pixels · 10 fois par seconde", 20, MUTED).next_to(cells, DOWN, buff=0.25)
        self.play(Create(sq), run_time=0.4)
        self.play(TransformFromCopy(sq, cells), Create(DashedLine(sq.get_corner(UR), cells.get_corner(UL), color=MUTED, dash_length=0.06)),
                  Create(DashedLine(sq.get_corner(DR), cells.get_corner(DL), color=MUTED, dash_length=0.06)), FadeIn(lab), run_time=1.1)
        self.at("Elle calcule")
        tg = tech("filtre moyenneur (box filter)", title)
        self.play(FadeIn(tg), run_time=0.5)
        self.at("Un carré donne")
        self.cap("Pourquoi un carré ?", 24, ACCENT)
        self.at("Un pixel seul")
        one = cells[40]
        self.play(*[cells[i].animate.set_opacity(0.25) for i in range(81) if i != 40], one.animate.set_stroke(ACCENT, 3), run_time=0.6)
        for col in [(214, 170, 40), (190, 150, 30), (209, 166, 36), (196, 158, 33)]:
            self.play(one.animate.set_fill(hexc(col), 1), run_time=0.25)
        self.cap("1 pixel : bruit et texture", 20)
        self.at("La moyenne de quatre")
        avg = Square(9 * s, stroke_width=0).set_fill(hexc(cr["avg"]), 1).move_to(cells)
        self.play(ReplacementTransform(cells, avg), Transform(lab, T(hexc(cr["avg"]).upper(), 20, MUTED).move_to(lab)), run_time=1.0)
        self.cap("81 pixels : bruit divisé par 9", 20, ACCENT_SOFT)
        self.at("trouve ensuite le nom")
        name = T(cr["name"], 32, INK).next_to(avg, RIGHT, buff=0.5).align_to(avg, UP)
        self.play(Write(name), run_time=0.9)
        self.at("Elle trouve aussi")
        ral = cr["ral"]["raw"]
        rg = VGroup(Square(0.7, stroke_width=0).set_fill(hexc((ral["r"], ral["g"], ral["b"])), 1),
                    VGroup(T(cr["ral"]["code"], 24, INK), T(cr["ral"]["name"], 18, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)).arrange(RIGHT, buff=0.25)
        rg.next_to(name, DOWN, buff=0.5, aligned_edge=LEFT)
        self.play(FadeIn(rg, shift=UP * 0.2), run_time=0.8)
        self.at("Cette formule")
        tg2 = tech("CIEDE2000 (ΔE₀₀) · plus proche voisin", tg)
        self.play(FadeIn(tg2), run_time=0.5)
        self.at("Ici, l'écart")
        de = T(f"ΔE₀₀ = {cr['ral']['deltaE']:.1f}".replace(".", ","), 22, ACCENT).next_to(rg, DOWN, buff=0.3, aligned_edge=LEFT)
        self.play(FadeIn(de), run_time=0.5)
        self.cap("< 2 : invisible  ·  > 5 : évident", 20, MUTED)
        self.finish()


# ======================================================================= S13
class S13(N):
    key = "s13_resume"
    card = ('Chapitre 9', 'Résumé', None)

    def construct(self):
        boxes, _ = steps_row()
        boxes.move_to(UP * 1.6)
        arrows = VGroup(*[arrow(boxes[i].get_right(), boxes[i + 1].get_left()) for i in range(3)])
        subs = ["grille régulière\n(stride)", "quantifier +\nmedian cut", "neutres réservés +\nsélection gloutonne", "hystérésis, moyenne,\ndeadband, EMA"]
        subt = VGroup(*[T(s, 18, MUTED, line_spacing=0.8).next_to(boxes[i], DOWN, buff=0.2) for i, s in enumerate(subs)])
        for frag, i in [("En résumé", 0), ("Découper", 1), ("Choisir", 2), ("Lisser", 3)]:
            self.at(frag)
            self.play(FadeIn(boxes[i], shift=UP * 0.2), FadeIn(subt[i]), *([GrowArrow(arrows[i - 1])] if i else []), run_time=0.6)
        self.at("Le résultat")
        bars = palette_bars(PAL16, height=1.4, width=1.2).move_to(DOWN * 1.6)
        self.play(LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars], lag_ratio=0.12), run_time=1.1)
        words = VGroup(T("vive", 26, INK), T("variée", 26, INK), T("stable", 26, INK)).arrange(RIGHT, buff=0.9).next_to(bars, DOWN, buff=0.35)
        self.play(LaggedStart(*[FadeIn(w, shift=UP * 0.15) for w in words], lag_ratio=0.3), run_time=1.1)
        self.at("L'application calcule")
        self.wait(1.2)
        self.play(FadeOut(boxes), FadeOut(arrows), FadeOut(subt), FadeOut(words), bars.animate.move_to(DOWN * 0.4), run_time=0.9)
        self.play(Write(T("ColorCatchers", 56, INK, weight=SEMIBOLD).next_to(bars, UP, buff=0.5)), run_time=1.2)
        self.finish(tail=1.6)

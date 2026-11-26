"""A change of scale on an axis, done by one map applied to everything that is
attached to a value: curve points, ticks, numbers.

Rules (the manim-video skill, "Zooms and changes of scale"):
- every tick and number belongs to its value and moves where the new scale
  puts that value, continuously;
- a number that exists in both scales is one object: it morphs from the old
  notation to the new one while it travels;
- a tick or number of the old scale only fades as it crowds or leaves; one of
  the new scale only fades in while travelling with its value.

    sm = ScaleMorph(t, xmap, y, old_ticks, new_ticks, old_labels, new_labels)
    scene.add(sm.group); scene.play(t.animate.set_value(1)); sm.freeze()

xmap(n, t) -> screen x of value n at time t in [0, 1] (may be +-inf: off screen).
old_labels / new_labels: {value: tex}.
"""
import math
import numpy as np
from manim import *


def smooth01(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def box_cox(n, lam):
    """(n^lam - 1)/lam, which is n - 1 at lam = 1 and tends to ln n as lam -> 0."""
    if lam < 1e-6:
        return math.log(n) if n > 0 else -math.inf
    if n <= 0:
        return -1 / lam
    return (n ** lam - 1) / lam


def lin_to_log_map(x0, x1, lo0, hi0, lo1, hi1):
    """The Box-Cox family from a linear axis on [lo0, hi0] (lo0 may be 0) to a
    logarithmic one on [lo1, hi1]: lambda goes 1 -> 0 while the visible range
    goes from the one interval to the other (the lower end linearly, the upper
    geometrically), so that the values in view stay in view."""
    def xmap(n, t):
        lam = 1 - t
        lo = lo0 + (lo1 - lo0) * t
        hi = hi0 * (hi1 / hi0) ** t
        g0, g1, g = box_cox(lo, lam), box_cox(hi, lam), box_cox(n, lam)
        if not math.isfinite(g):
            return -math.inf
        return x0 + (x1 - x0) * (g - g0) / (g1 - g0)
    return xmap


class ScaleMorph:
    def __init__(self, t, xmap, y, old_ticks, new_ticks, old_labels, new_labels, x0, x1,
                 font=(24, 26), buff=0.2, crowd=(1.1, 1.4)):
        self.t, self.xmap, self.y, self.x0, self.x1 = t, xmap, y, x0, x1
        self.old_ticks, self.new_ticks = set(old_ticks), set(new_ticks)
        self.crowd, self.buff = crowd, buff
        self.ticks = always_redraw(self._ticks)
        self.labels = VGroup()
        old_vals = sorted(old_labels)
        for v in sorted(set(old_labels) | set(new_labels)):
            a = MathTex(old_labels.get(v, new_labels.get(v)), font_size=font[0])
            b = MathTex(new_labels.get(v, old_labels.get(v)), font_size=font[1])
            a.move_to(ORIGIN); b.move_to(ORIGIN)
            a.align_data(b)                      # what Transform does before interpolating
            # Aligning pads the shorter notation with copies of its own glyphs,
            # drawn on top of each other: the label looks bold. Make the copies
            # transparent, so they fade out as the morph completes.
            for mob in (a, b):
                fam = mob.family_members_with_points()
                for i in range(1, len(fam)):
                    if fam[i].points.shape == fam[i - 1].points.shape and np.allclose(fam[i].points, fam[i - 1].points):
                        fam[i].set_fill(opacity=0)
            m = a.copy()
            m.value, m.a, m.b = v, a, b
            m.in_old, m.in_new = v in old_labels, v in new_labels
            nxt = [w for w in old_vals if w > v]
            m.old_next = nxt[0] if nxt else None
            self.labels.add(m)
        self.labels.add_updater(lambda g: self._place())
        self._place()
        self.group = VGroup(self.ticks, self.labels)

    def _edge(self, x):
        if not math.isfinite(x):
            return 0.0
        return smooth01(min(x - (self.x0 - 0.3), (self.x1 + 0.3) - x) / 0.3)

    def _ticks(self):
        t = self.t.get_value()
        g = VGroup()
        for v in self.old_ticks | self.new_ticks:
            o = (1 - t) * (v in self.old_ticks) + t * (v in self.new_ticks)
            x = self.xmap(v, t)
            o *= self._edge(x)
            if o > 0.01:
                g.add(Line([x, self.y - 0.1, 0], [x, self.y + 0.1, 0], stroke_width=2, stroke_opacity=o))
        return g

    def _place(self):
        t = self.t.get_value()
        s = smooth01((t - 0.15) / 0.7)             # the change of notation, in the middle of the move
        for m in self.labels:
            # Mobject.interpolate does not recurse: do every glyph, as Transform does
            for gm, ga, gb in zip(m.family_members_with_points(), m.a.family_members_with_points(),
                                  m.b.family_members_with_points()):
                gm.interpolate(ga, gb, s)
            x = self.xmap(m.value, t)
            if not math.isfinite(x):
                m.set_fill(opacity=0, family=True)
                continue
            m.move_to([x, self.y - self.buff - m.height / 2, 0])
            if m.in_old and m.in_new:
                o = 1.0
            elif m.in_old:
                o = 1 - smooth01((t - 0.8) / 0.2)    # gone by the end in any case
                if m.old_next is not None:
                    gap = self.xmap(m.old_next, t) - x
                    o = min(o, smooth01((gap - self.crowd[0]) / (self.crowd[1] - self.crowd[0])))
            else:
                o = t
            o *= self._edge(x)
            for g in m.family_members_with_points():
                g.set_fill(opacity=g.get_fill_opacity() * o)

    def freeze(self):
        self.ticks.clear_updaters()
        self.labels.clear_updaters()

"""A number line that zooms: its visible range and its place on screen follow a
ValueTracker alpha in [0, 1]. Ticks and numbers are attached to values, so they
move with the stretching axis; finer ticks and numbers fade in as the space
between them opens up, and fade out as it closes."""
import math
from manim import *


def smooth01(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


class ZoomLine:
    """frame(alpha) -> (a, b, x0, x1, y): the values at the two ends of the
    line and where the line is drawn.

    labels: {value: (tex, level)}; a number is shown when `level` values span
    at least label_fade[1] units of screen, hidden below label_fade[0]."""

    def __init__(self, alpha, frame, tick_steps, labels, tick_fade=(0.15, 0.35),
                 label_fade=(0.8, 1.1), font=(28, 28), buff=(0.25, 0.25), color_fn=None):
        self.alpha, self.frame = alpha, frame
        self.tick_steps, self.tick_fade, self.label_fade = tick_steps, tick_fade, label_fade
        self.font, self.buff, self.color_fn = font, buff, color_fn
        self.line = always_redraw(self._line)
        self.ticks = always_redraw(self._ticks)
        self.labels = VGroup()
        for v, (tex, level) in labels.items():
            m = MathTex(tex, font_size=font[0])
            m.value, m.level, m.h0 = v, level, m.height
            self.labels.add(m)
        self.labels.add_updater(lambda g: self._place_labels())
        self._place_labels()
        self.group = VGroup(self.line, self.ticks, self.labels)

    def x_of(self, v, f=None):
        a, b, x0, x1, _ = f or self.frame(self.alpha.get_value())
        return x0 + (v - a) * (x1 - x0) / (b - a)

    def _line(self):
        a, b, x0, x1, y = self.frame(self.alpha.get_value())
        return Line([x0, y, 0], [x1, y, 0], stroke_width=2)

    def _ticks(self):
        f = self.frame(self.alpha.get_value())
        a, b, x0, x1, y = f
        scale = (x1 - x0) / (b - a)
        best = {}
        for s in self.tick_steps:
            o = smooth01((s * scale - self.tick_fade[0]) / (self.tick_fade[1] - self.tick_fade[0]))
            if o < 0.01:
                continue
            k0, k1 = math.ceil(a / s - 1e-9), math.floor(b / s + 1e-9)
            for k in range(k0, k1 + 1):
                v = k * s
                best[v] = max(best.get(v, 0), o)
        g = VGroup()
        for v, o in best.items():
            x = self.x_of(v, f)
            g.add(Line([x, y - 0.1, 0], [x, y + 0.1, 0], stroke_width=2, stroke_opacity=o))
        return g

    def _place_labels(self):
        al = self.alpha.get_value()
        f = self.frame(al)
        a, b, x0, x1, y = f
        scale = (x1 - x0) / (b - a)
        fs = self.font[0] + (self.font[1] - self.font[0]) * al
        buff = self.buff[0] + (self.buff[1] - self.buff[0]) * al
        for m in self.labels:
            m.set_height(m.h0 * fs / self.font[0])
            x = self.x_of(m.value, f)
            m.move_to([x, y - buff - m.height / 2, 0])
            o = smooth01((m.level * scale - self.label_fade[0]) / (self.label_fade[1] - self.label_fade[0]))
            o *= smooth01(min(x - (x0 - 0.3), (x1 + 0.3) - x) / 0.3)
            m.set_opacity(o)
            if self.color_fn:
                m.set_color(self.color_fn(m.value, al))

    def freeze(self):
        for mob in (self.line, self.ticks, self.labels):
            mob.clear_updaters()

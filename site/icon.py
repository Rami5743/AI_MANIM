"""The page's icon: the Manim logo, built as Manim itself builds it (the M, the
green circle, the blue square, the red triangle), with two changes: the
triangle is a play button, and an AI sparkle stands in the corner.

    manim -s -qh icon.py Icon     # then cut to a rounded square (see README)
"""
from manim import *
from manim.mobject.logo import MANIM_SVG_PATHS, VMobjectFromSVGPath
import manim.constants as cst

config.pixel_width = config.pixel_height = 1024
config.frame_width = config.frame_height = 6.6
config.background_color = "#ece6e2"


def sparkle(radius=1.0, pinch=0.12, color="#343434"):
    """A four-pointed star with concave sides: the usual sign for AI."""
    tips = [radius * d for d in (UP, RIGHT, DOWN, LEFT)]
    m = VMobject(fill_color=color, fill_opacity=1, stroke_width=0)
    pts = []
    for a, b in zip(tips, tips[1:] + tips[:1]):
        pts += [a, a * pinch, b * pinch, b]   # both handles pulled to the centre
    m.set_points(np.array(pts))
    return m


class Icon(Scene):
    def construct(self):
        green, blue, red, ink, gold = "#81b29a", "#454866", "#e07a5f", "#343434", "#e9a13b"
        M = VMobjectFromSVGPath(MANIM_SVG_PATHS[0]).flip(RIGHT).center()
        M.set(stroke_width=0).scale(7 * cst.DEFAULT_FONT_SIZE * cst.SCALE_FACTOR_PER_FONT_POINT)
        M.set_fill(ink, 1).shift(2.25 * LEFT + 1.5 * UP)
        circle = Circle(color=green, fill_opacity=1).shift(LEFT)
        square = Square(color=blue, fill_opacity=1).shift(UP)
        play = Triangle(color=red, fill_opacity=1).rotate(-PI / 2).shift(RIGHT * 0.95)
        logo = VGroup(VGroup(play, square, circle), M)
        logo.scale_to_fit_width(config.frame_width * 0.72).move_to(0.25 * LEFT + 0.3 * DOWN)
        corner = square.get_corner(UR)
        big = sparkle(0.95, pinch=0.24, color=gold).move_to(corner + 0.05 * UR)
        small = sparkle(0.42, pinch=0.24, color=gold).move_to(corner + np.array([-1.05, 0.55, 0]))
        self.add(logo, big, small)

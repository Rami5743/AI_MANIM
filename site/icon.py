from manim import *
from manim.mobject.logo import MANIM_SVG_PATHS, VMobjectFromSVGPath
import manim.constants as cst

config.pixel_width = config.pixel_height = 1024
config.frame_width = config.frame_height = 6.6
config.background_color = "#ece6e2"

class Icon(Scene):
    def construct(self):
        green, blue, red, ink = "#81b29a", "#454866", "#e07a5f", "#343434"
        M = VMobjectFromSVGPath(MANIM_SVG_PATHS[0]).flip(RIGHT).center()
        M.set(stroke_width=0).scale(7 * cst.DEFAULT_FONT_SIZE * cst.SCALE_FACTOR_PER_FONT_POINT)
        M.set_fill(ink, 1).shift(2.25 * LEFT + 1.5 * UP)
        circle = Circle(color=green, fill_opacity=1).shift(LEFT)
        square = Square(color=blue, fill_opacity=1).shift(UP)
        # the one change: the triangle is a play button, pointing right
        play = Triangle(color=red, fill_opacity=1).rotate(-PI / 2).shift(RIGHT * 0.95)
        logo = VGroup(VGroup(play, square, circle), M)
        logo.scale_to_fit_width(config.frame_width * 0.80).move_to(ORIGIN)
        self.add(logo)

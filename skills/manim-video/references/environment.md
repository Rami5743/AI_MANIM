# The toolchain

Manim Community, a LaTeX distribution, FFmpeg. On a fresh Debian or Ubuntu
container, as root. Start it in the background at the beginning of the session —
it takes several minutes and roughly 4 GB of disk, and stage 5 cannot begin
without it.

```bash
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y --no-install-recommends \
  build-essential pkg-config python3-dev python3-venv \
  libcairo2-dev libpango1.0-dev \
  ffmpeg \
  texlive-latex-base texlive-latex-recommended texlive-latex-extra \
  texlive-fonts-recommended texlive-fonts-extra texlive-science \
  texlive-pictures cm-super dvisvgm

python3 -m venv /opt/manim-venv
/opt/manim-venv/bin/pip install --upgrade pip
/opt/manim-venv/bin/pip install manim
```

A virtual environment rather than `pip --break-system-packages`, because recent
Debian and Ubuntu mark the system Python as externally managed. Everything after
this runs as `/opt/manim-venv/bin/manim` and `/opt/manim-venv/bin/python`.

What each piece is for:

| Package | Why |
|---|---|
| `texlive-latex-extra` | `standalone` and `preview`, the document class Manim's `MathTex` compiles against |
| `dvisvgm` | turns the compiled DVI into the SVG that Manim parses into glyphs |
| `cm-super` | Computer Modern as scalable Type 1, so formulas stay sharp at 1080p |
| `texlive-science` | `amsmath`, `amssymb`, `mathtools` |
| `libcairo2-dev`, `libpango1.0-dev` | the rasteriser and the text shaper, the latter being what makes `Text` handle Hebrew |
| `ffmpeg` | writes the mp4, and is what `scripts/frames.py` and `scripts/assemble.py` call |

## The smoke test

Run it before stage 5. It exercises the three things that break independently:
the Python package, LaTeX through `MathTex`, and Pango through `Text`.

```python
# smoke.py
from manim import *

class Smoke(Scene):
    def construct(self):
        formula = MathTex(r"\sum_{p\le x}\frac{1}{p}=\log\log x+M+o(1)")
        hebrew = Text("בדיקה", font="DejaVu Sans").next_to(formula, DOWN)
        circle = Circle().shift(2 * DOWN).set_color(BLUE)
        self.play(Write(formula))
        self.play(FadeIn(hebrew), Create(circle))
        self.wait(0.5)
```

```bash
/opt/manim-venv/bin/manim -ql smoke.py Smoke
```

It passes when an mp4 is written **and** a frame read out of it shows the
formula, the Hebrew word with its letters in the right order, and the circle.
An exit code of 0 is not the test — `scripts/frames.py at` on the result is.

## Fonts

`fc-list :lang=he family` lists what can set Hebrew. `DejaVu Sans` and
`FreeSerif` arrive with the packages above and both work. Name one explicitly in
every `Text` that holds Hebrew — the default font is not guaranteed to cover it,
and a missing glyph is drawn as a blank rather than raising.

## Disk

The partial movie files Manim caches under `media/` grow faster than the
renders. They are regenerable, so delete them rather than commit them, and put
`media/` in the repository's `.gitignore`. What is committed per scene is
`scene.py` and the one approved mp4 under `out/`.

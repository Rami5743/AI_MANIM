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

## Without root (a sandbox such as Cowork's)

No `apt-get`: everything goes into a user-space prefix from conda-forge, which
brings Manim together with cairo, pango and FFmpeg.

```bash
P="$HOME/manim-tools"; mkdir -p "$P" && cd "$P"
curl -fsSL https://conda.anaconda.org/conda-forge/linux-64/micromamba-2.10.0-0.tar.bz2 \
  | tar -xj bin/micromamba                 # or any newer micromamba build listed there
export MAMBA_ROOT_PREFIX="$P/mamba"
./bin/micromamba create -y -p "$P/env" -c conda-forge python=3.12 manim
export PATH="$P/env/bin:$PATH"             # manim, python, ffmpeg, ffprobe
```

Verified from scratch, without root: Manim 0.22.1 with cairo, pango, FFmpeg
and ffprobe, in under a minute, from `conda.anaconda.org` alone.

**LaTeX is the hard part.** conda-forge's `texlive-core` is bare — no
`standalone`, no `preview`, no `dvisvgm` — and `MathTex` fails with it. The
usual user-space LaTeX is TinyTeX, then the packages Manim needs:

```bash
curl -fsSL https://yihui.org/tinytex/install-bin-unix.sh | sh
export PATH="$HOME/.TinyTeX/bin/x86_64-linux:$PATH"
tlmgr install standalone preview amsmath amsfonts mathtools dvisvgm cm-super \
  doublestroke relsize setspace babel-english
```

This needs `yihui.org` (or its GitHub releases) and a CTAN mirror, which a
sandbox's network may block; it has not been verified in such a sandbox. If
the network allows only package registries, ask the user to allow those hosts,
or to run stage 4 where LaTeX can be installed. Without LaTeX there is no
`MathTex`, and a mathematical video cannot be made — say so at once rather than
working around it.

## Renders longer than a command may run

Some sandboxes stop a command after a few minutes. Manim writes every
animation of a scene to its own partial file as soon as it is finished, and a
rerun reuses those that are already there, so a render can be done in pieces:
run it, and if it is cut off, run it again — it continues from the last
finished animation. **Before each rerun, delete the partial file the
interruption left half-written**, or the rerun takes it as finished and fails
to join the pieces:

```bash
part=<media_dir>/videos/scene/<quality>/partial_movie_files/<SceneClass>
for f in "$part"/*.mp4; do ffprobe -v error "$f" >/dev/null 2>&1 || rm -f "$f"; done
```

Verified: a scene cut off mid-render, cleaned this way and rendered again,
came out identical frame for frame to an uninterrupted render. Where
background processes survive the command, running the render with `nohup …
&` and checking on it is simpler.

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

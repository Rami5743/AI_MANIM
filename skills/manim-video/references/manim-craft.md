# Manim craft

Manim Community Edition. Verified against **0.22.1**.

## The style is the default

The look asked for is 3Blue1Brown's, and Manim's defaults already are it:
black background, white strokes, `BLUE`/`YELLOW`/`GREEN`/`RED` for accents,
`MathTex` set in Computer Modern. So **set no theme and import no style file.**
Every line of configuration spent on appearance is a line that moves the video
away from the target.

What is worth setting, and nothing else:

| Setting | Where | Value |
|---|---|---|
| resolution and frame rate | the render command | `-qm` while working, `-qh` for the approved take |
| colour of an object that carries meaning | at construction | from the built-in palette |
| `font_size` | at construction | the defaults are tuned for 1080p, change one only when a label does not fit |

The frame is 8 units high and `config.frame_width` wide — 14.22 at 16:9. An
object placed past ±7.1 horizontally or ±4 vertically is off screen, and that is
the single most common defect in a first draft.

**Keep the band below $y\approx-2.9$ free.** That is where burned-in
subtitles go, two lines of them, and an axis placed at $y=-3$ has its numbers
covered.

## The idioms worth using

| Want | Use |
|---|---|
| a formula | `MathTex(r"…")` — raw string, always |
| a formula with prose in it | `MathTex(r"\pi(x)=\#\{p\le x\}")`, prose inside `\text{…}` |
| one formula turning into another | `TransformMatchingTex(a, b)` |
| a label following an object | `always_redraw(lambda: label.next_to(dot, UP))` |
| a number counting up | `DecimalNumber` with a `ValueTracker` and `add_updater` |
| a graph | `Axes(...)` then `axes.plot(f, x_range=…)` |
| a point on a graph | `axes.c2p(x, y)` — never raw coordinates |
| drawing a curve left to right | `Create(curve, run_time=t, rate_func=linear)` |
| highlighting part of a formula | `tex[0][3:7].set_color(YELLOW)`, or index by `substrings_to_isolate` |
| stacking objects | `VGroup(...).arrange(DOWN, buff=0.4)` |
| fitting a group to the frame | `group.scale_to_fit_width(12)` |

`rate_func=linear` matters more than it looks. Manim's default easing makes an
animation start and end slowly, which is right for a move and wrong for anything
the narration tracks in real time — a curve being traced, a counter climbing.

## Timing

`self.play(..., run_time=t)` and `self.wait(t)` are the only two clocks, and
their sum is the scene's duration. Use `scripts/timing.py`: it reads the
scene's `timing.json` (cue and pause times) and plays every animation **at an
absolute time** — `T.play(self, anim, at=T.cue(3).start, run_time=0.8)`, and
`T.finish(self)` at the end. Its clock is `scene.renderer.time`, the video
actually rendered, not a running sum of `run_time`s, so the rounding of each
animation to whole frames cannot accumulate into drift.

Keep every time a multiple of 0.05 s. At 60 fps that is exactly three frames,
and the final render then lands on the planned duration to the frame. At the
30 fps of the draft quality it is a frame and a half, and a 45 s draft comes
out about 0.15 s short — expected, and not worth fixing.

Look pauses up by a substring of their label, and make the substring unique:
two pauses labelled "... fades out" in one scene are a lookup error.

## Hebrew on screen

Hebrew goes through **`MarkupText`**, never through `Tex` or `MathTex`, and not
through `Text` either. Pango applies the bidirectional algorithm and shapes
the letters correctly for both, but in Manim 0.22.1 **`Text` renders a single
Hebrew word with no space as an empty mobject** — `Text("שלום")` has no
submobjects and draws nothing, silently — while `MarkupText("שלום")` works.
Escape the string (`xml.sax.saxutils.escape`) before handing it over.

```python
MarkupText("כמה מספרים ראשוניים יש עד איקס?", font="DejaVu Sans", font_size=40)
```

**Fade Hebrew in; do not `Write` it.** `Write` draws the glyphs in submobject
order, which for Hebrew is from the last letter of the line to the first, so
the viewer sees the end of the phrase appear first.

Name the font. `DejaVu Sans` and `FreeSerif` both cover Hebrew and both are
installed by `references/environment.md`; the default font may not. Verified:
both render the line above with the letters in the right order and the question
mark on the left.

A line that mixes Hebrew with a formula is two mobjects, not one — a `Text` for
the Hebrew and a `MathTex` for the formula, arranged with `VGroup(...).arrange`.
Putting a formula inside a Hebrew `Text` gets it reordered.

## The animation rules

How things move, appear, disappear and keep time — zooms, changes of scale,
motion versus fades, timing against the narration — is in
`references/animation-rules.md`, the rulebook. Below are only the
implementation notes for the helpers that carry those rules out.

## Implementing the rules

- **Zooms**: `scripts/zoomline.py` draws a number line whose visible range and
  place on screen follow a `ValueTracker` `alpha`: give it
  `frame(alpha) -> (lo, hi, x0, x1, y)`, the tick steps, and the candidate
  numbers as `{value: (tex, level)}`. A number of level $L$ is visible when $L$
  values span enough screen. Candidates far from what is ever in view can be
  left out: a level-$L$ number is only visible while about $15L$ is in view.
- **Changes of scale**: `scripts/rescale.py` takes the map `xmap(n, t)`, the
  old and new ticks, and the old and new numbers as `{value: tex}`. A value
  present in both gets one label that morphs between its two notations, and
  `lin_to_log_map` builds the Box–Cox map. Two traps it handles:
  `Mobject.interpolate` does not recurse into a formula's glyphs (interpolate
  every member of `family_members_with_points()`, as `Transform` does), and
  aligning a long notation with a short one pads the short one with copies of
  its own glyphs drawn on top of each other, which looks bold — make the copies
  transparent so that they fade out as the morph completes.
- **Mapping pieces of formulas**: print the glyph order of each `MathTex` once
  (index, centre, height) and slice by it. A `\frac` is numerator, bar,
  denominator. A big `\left|` is several glyphs stacked. Assert the glyph
  count in the code, so a changed formula fails loudly rather than
  mis-mapping.
- **Motion when the data changes**: `ReplacementTransform` between two
  polylines works point by point even when their point counts differ. Use it
  when a plot's curve becomes another (a 20% curve going back to 1%).

## Pitfalls

- **A `MathTex` that fails to compile** stops the render with the LaTeX log
  attached. Read the log. It is almost always an unescaped backslash from
  forgetting the `r` prefix, or a package the template does not load.
- **Indexing into a `MathTex`** is by glyph, and the glyph count is not the
  character count. Use `substrings_to_isolate=[...]` at construction and index
  by substring, or print `len(tex[0])` once and index from what you see.
- **`Transform` between objects of different shape** produces a smear. Use
  `TransformMatchingTex` for formulas and `ReplacementTransform` when the old
  object should stop existing.
- **An object added with `self.add` and never removed** survives into the next
  `self.play` and into screenshots. If the plan says the scene leaves it behind,
  that is correct. If not, `FadeOut` it.
- **`always_redraw` with a closure over a loop variable** captures the last
  value. Bind it with a default argument.
- **Partial movie files** are cached under `media/videos/…/partial_movie_files`
  and are reused. After editing a scene, if the render looks unchanged, pass
  `--disable_caching`.
- **`Indicate` on an `ImageMobject` tints the whole picture** in the
  indicate colour. Highlight a portrait with `Circumscribe` instead.
- **`Indicate` scales**, and a scaled line or curve overruns its axes. Pass
  `scale_factor=1` for a flash without growth.
- **`NumberLine(x_range=[1780, 1920, 10])` drops its last ticks** (floating
  point in the tick range of a line that does not start near 0). Build the
  line on `[0, 140, 10]` and offset `n2p`.
- **Removing a slice of a group that was added whole does nothing.**
  `self.remove(group[:-1])` leaves everything on screen; remove the group and
  add back what should stay.
- **`GrowFromEdge` scales both dimensions.** To grow a block upward at a fixed
  width, transform a flat copy of it into it.
- **Rendering at `-qh` is roughly eight times `-qm`.** Stay at `-qm` for the
  whole fix loop and go to `-qh` once.

## The render commands

```bash
# draft, while fixing: 1280x720 at 30 fps
/opt/manim-venv/bin/manim -qm --media_dir ./media scene.py SceneName

# a single frame, for checking a layout without rendering the animation
/opt/manim-venv/bin/manim -qm -s --media_dir ./media scene.py SceneName

# the approved take: 1920x1080 at 60 fps, written where the plan wants it
/opt/manim-venv/bin/manim -qh --media_dir ./media \
  -o ../../out/02-counting-primes.mp4 scene.py SceneName
```

`-o` is relative to the media directory's video folder, so check where the file
actually landed rather than trusting the flag. Manim prints the absolute path of
what it wrote on the last `INFO` line, and that line is the one to believe.

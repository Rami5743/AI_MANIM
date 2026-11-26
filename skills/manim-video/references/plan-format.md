# The format of the plan files

Three files carry the plan: `scenes.md` for the whole video, and
`description.md` plus `subtitles.srt` for each scene. Their shape is fixed so
that a project can be picked up by reading them and nothing else.

## `scenes.md`

```markdown
# <Project title> — scene list

| field | value |
|---|---|
| source script | `script/script.md` |
| resolution | 1920×1080, 60 fps |
| draft quality | `-qm` (1280×720, 30 fps) |
| reading rate | 5.05 syllables per second, formulas as read aloud |
| inter-cue gap | 0.15 s |
| scene head / tail silence | 0.8 s |
| total planned | 7:42 |

| # | slug | subject | planned | starts at | inherits | state |
|---|---|---|---|---|---|---|
| 01 | title-card | the question in one sentence | 0:34 | 0:00 | — | approved |
| 02 | counting-primes | π(x) as a staircase | 1:12 | 0:34 | the staircase axes | rendered |
| 03 | the-guess | x/log x laid over it | 0:58 | 1:46 | axes and staircase from 02 | planned |

## Open decisions

- `[fill] 02` the staircase is drawn to x = 100, the script does not say how far.
- `[fill] 03` the comparison curve is drawn in YELLOW, matching the title card.
```

The state column is the project's progress bar, and the four values mean:

| state | what is true |
|---|---|
| `planned` | `description.md` and `subtitles.srt` exist and are committed |
| `implemented` | `scene.py` exists and renders without an exception |
| `rendered` | a draft render exists and has been inspected at least once |
| `approved` | the final render matches the plan, is committed, and was handed to the user |

## `description.md`

```markdown
# Scene 02 — counting-primes

**Subject.** The prime-counting function as a staircase that climbs by one at
every prime.

**Duration.** 1:12 (72.0 s), of which 0.8 s head silence and 0.8 s tail.

**Inherits.** Nothing. Opens on an empty frame.

**Leaves behind.** `axes` and `staircase`, both still on screen, for scene 03.

## Assets

| file | what it is | source | licence |
|---|---|---|---|
| `assets/gauss.jpg` | portrait of Gauss | commons.wikimedia.org/wiki/File:… | public domain |

## Objects

| name | what | position | style |
|---|---|---|---|
| `axes` | `Axes(x_range=[0,100,10], y_range=[0,30,5])` | centred, `width=10` | default |
| `staircase` | step function of π(x) | on `axes` | `YELLOW`, `stroke_width=3` |
| `label` | `MathTex(r"\pi(x)")` | next to the top of the staircase, `UP+RIGHT` | `YELLOW` |

## Formulas

Written out exactly as they will be rendered.

- `label`: `\pi(x)`
- `defn`: `\pi(x)=\#\{p\le x : p \text{ prime}\}`

## Timeline

| from | to | cue | what happens |
|---|---|---|---|
| 0.0 | 0.8 | — | head silence, empty frame |
| 0.8 | 3.4 | 1 | `Create(axes)`, run_time 2.0, then 0.6 s hold |
| 3.4 | 8.1 | 2–3 | `Write(defn)` at the top, run_time 1.5, held to the end of cue 3 |
| 8.1 | 20.0 | 4–6 | the staircase is drawn left to right, `Create(staircase)`, run_time 11.0, `rate_func=linear` so that it tracks the narration |
| … | | | |
| 71.2 | 72.0 | — | tail silence, nothing moves |

Every row's `to` is the next row's `from`. The last `to` is the scene's
duration, and it equals the end of the last cue plus the tail silence.

## Notes

- `[fill]` the script says "up to a hundred or so"; x = 100 was chosen so that
  the staircase has 25 steps and stays legible at 1080p.
- `[fill]` the narration mentions Gauss but does not ask for the portrait. It
  is shown small in the corner during cues 7–9 and removed after.
```

The timeline is the part stage 5 transcribes, so it carries real numbers and
real animation names. "The staircase appears" is not a plan. `Create(staircase)`
with `run_time=11.0` and `rate_func=linear` is.

## `subtitles.srt`

Standard SRT, times from the start of the scene, cue numbering from 1 in every
scene — `scripts/assemble.py` renumbers and shifts them in stage 6.

```
1
00:00:00,800 --> 00:00:03,400
כמה מספרים ראשוניים יש עד למספר נתון?

2
00:00:03,550 --> 00:00:06,900
נסמן את הכמות הזאת בפאי של איקס.
```

A formula the narration speaks is written in the subtitle as plain text —
`p₁%(n)`, `ln(n)`, `n!` — never as LaTeX. Inside a Hebrew cue, **wrap every
such run in a left-to-right isolate, U+2066 … U+2069**. Without it the bidi
algorithm mirrors the parentheses and moves the `%`: "ב-p₁%(n)" was burned in
as "ב-n)%p₁(". Do it when writing the file, not by hand.

**Timing against the narration follows `references/animation-rules.md`,
section 1:** an animation starts with its cue, silence only where an
animation outlasts its cue, and the first cue of a scene is held longer — a
`("say", text, seconds)` item holds a cue for at least that long.

**One source for the plan's times and the code's.** Give every scene a
`timeline.py` beside `description.md`: a list of rows
`(key, anchor, offset, run_time, what)`, where the anchor is a cue number, a
substring of a pause label, an absolute time or `("after", key)`.
`scripts/timeline_md.py`, run from the project directory, writes the Timeline
table of `description.md` from it, and the scene code takes every time from
it — `T.play(self, anim, **T.row("key"))` (`scripts/timing.py`). A plan
edited by hand drifts from the render the first time a cue changes length.
Generated from the same rows, it cannot.

Generate the cues rather than typing the times. A good shape: one Python file
holding each scene's narration as a list of cues (each a string, word for word
from the script) and silent stretches `("pause", seconds, label)` where a stage
direction needs time; a script turns it into every scene's `subtitles.srt` and
a `timing.json` with the absolute start and end of every cue and pause, which
the scene code then plays against (`scripts/timing.py`). Retiming the video is
then one edit and one run.

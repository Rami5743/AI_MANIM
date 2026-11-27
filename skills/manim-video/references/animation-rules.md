# The animation rules

These rules govern how things move, appear, disappear and keep time in every
video made with this skill. Most were laid down by the user while reviewing
the first project (a nine-minute video on the Prime Number Theorem, in the
`Rami5743/PNT` repository under `video/pnt-intro/`). The rest were learned
from defects found in its drafts. They apply when the plan is written
(stage 3) and again when it is implemented (stage 5). A plan that breaks one of
them is a wrong plan, not a creative choice.

Each rule names its origin: **(user)** for a rule the user gave, **(review)**
for one learned from a draft.

## 1. Time: the picture follows the words

**1.1 An animation starts with the cue that speaks of it.** (user) The 2 is
written while the narration asks how many times 2 appears, not after the
sentence ends. A formula that the narration describes ("we bound the ratio from
above and below") is written during that sentence. A portrait appears while
its person is named.

**1.2 Silence only where an animation outlasts its cue.** (user) A silent stretch
after a cue is planned only when the animation that started with the cue needs
more time than the cue lasts — a sweep that traces a graph for ten seconds, a
zoom that cannot be hurried. A stage direction is not a reason for a pause. It
belongs to the sentence it follows or precedes.

**1.3 The first cue of a scene is held long enough to be read** with the picture
that opens the scene. (user) Hold it for about 3 s, longer than its length alone
would ask for.

**1.4 One source of times.** (review) Anchor every animation to a cue or a pause
(plus an offset) in one file per scene, `timeline.py`. The plan's timeline table
and the code both read it (`scripts/timeline_md.py`, `scripts/timing.py`), so a
change in a cue's length moves plan and render together.

**1.5 A change of narration rate retimes everything, and refits the waits.**
(user) The animations are anchored to cues (1.4), so they move with them on
their own. But the silent stretches that only waited for an animation to
finish are now wrong: longer cues often cover the animation, and the wait must
shrink or go (1.2). Recompute each such stretch as what its animation still
needs — the latest end of an animation started before it, or chained
("after") to one that was, minus its start, rounded up to 0.1 s — and remove
it when that is nothing. Leaving out the chained ones is the trap: a chain
that began in the cue runs on into the stretch. A stretch that holds
an animation of its own (a row anchored to it, such as a sweep or a final
fade) keeps its length. Then every scene is rendered again, and delivered
again.

**1.6 The rate is in syllables, formulas as read aloud.** (user) How long a
cue takes is how long it takes to say: count its syllables, and count a
formula or a number by the words it is read with ($r_{1\%}$ is "אר אחוז"),
not by its characters. `scripts/syllables.py`.

**1.7 A long silence becomes narration when the user writes it.** (user) If
the user adds a sentence that describes an animation already on screen — in
the PNT video, "נרוץ על כל המספרים בטווח זה…" during the sliding window —
the animation is re-anchored to start with that sentence (1.1), and the
silent stretch that held it becomes a wait for what is left of it (1.2).

**1.8 Punctuation is time, and cues end at it.** (user) A narrator stops at
the end of a sentence and breathes at a comma, so the timing gives those stops
their time, between cues and inside them. A cue ends at a sentence or a comma,
never inside a phrase; an animation that belongs to the second half of a long
cue starts at its words (1.1), not at the cue.

## 2. Change moves, coming and going fades

**2.1 When something changes, it moves; when it appears or goes away, it
fades.** (user) A formula rewritten, a label renamed, a curve replaced by
another curve of the same plot, a caption whose number changes: the old object
**turns into** the new one by motion. Only what has no successor fades out, and
only what has no predecessor fades in.

**2.2 Map the pieces by meaning.** (user, review) When the two sides do not match
glyph for glyph, say what becomes what and move each piece into the piece it
becomes. In the PNT video, the long factorisation became the product formula
like this: `n!` and `=` into theirs, the bases 2, 3, 5 into the single $p$, the
first term of each exponent into the general term $\lfloor n/p^k\rfloor$, the
rest of each exponent into $\sum_{k\ge1}$, and the product dots into $\prod$.
Mapping everything into everything is still motion, but it turns into a
smear.

**2.3 Matching transforms are a trap.** (review) `TransformMatchingShapes` and
`TransformMatchingTex` fade every glyph they fail to match, which breaks 2.1
silently. Use them only when the two sides really share their pieces, and look
at the frames in the middle of the transition.

**2.4 A label changes with its object.** (user) When the curve on screen changes
from 5% to 20%, its label `r_{5\%}(n)` turns into `r_{20\%}(n)` by `Transform`.
It is not faded out and replaced.

## 3. Zooms

**3.1 A zoom stretches the axis.** (user) The axis itself stretches, and the
ticks move along it. It is not one number line morphing into another, which
reads as a window growing over a fixed axis.

**3.2 Ticks and numbers are attached to their values.** (user) Every tick and
number travels with its value as the axis stretches or shrinks.

**3.3 Finer ticks come and go with the space.** (user) As the axis stretches,
finer ticks and numbers fade in when the gap between them opens up. As it
shrinks, they fade out when they crowd. The thresholds are in screen units: a
number needs about its own width, plus a margin.

**3.4 Constant zoom speed.** (review) Interpolate the visible width
geometrically, not linearly.

**3.5 A zoom continues to the scale that is needed.** (user) If the next thing to
be shown lives at another scale, the zoom goes all the way there in one
movement. Do not zoom part way and then cut. In the PNT video, the zoom out
from 9900–10100 went on to 0–$10^6$, and only then did the window start to
slide.

**3.6 What marks a range is drawn from its values.** (review) A highlighted
window or a shaded band is defined by the values it covers, so it stretches or
shrinks with the axis on its own.

`scripts/zoomline.py` implements 3.1–3.4 and 3.6.

## 4. Changes of scale

**4.1 One map for everything.** (user) Switching an axis between linear and
logarithmic, or any rescaling, moves every curve point, tick and number from
where the old scale put its value to where the new scale puts it,
continuously, all by the same map.

**4.2 A number that exists in both scales is one object.** (user) It travels
with its value and **changes notation while travelling**: 1000000 turns into
$10^6$ on its way. It never fades out in one place while its successor fades in
somewhere else.

**4.3 Numbers and ticks of one scale only stay attached to their values.** (user)
Those of the old scale fade as they crowd or leave the axis. Those of the new
scale fade in while travelling with their values from where the old scale had
them — from beyond the edge, if that is where they were.

**4.4 Choose the map so that the values in view stay in view.** (review) For
linear to logarithmic, use the Box–Cox family $g_\lambda(n)=(n^\lambda-1)/\lambda$
with $\lambda$ going from 1 to 0, while the visible range moves from the old
interval to the new one. Straight-line interpolation of positions is wrong:
values beyond the old range then race in during the last frames.

**4.5 A different quantity is not a change of scale.** (review) When the axis
starts measuring something else — $p$ becoming $1/p$, $r$ becoming
$r/\ln n$ — there is no correspondence between the old numbers and the new
ones. Then the old numbers fade out and the new ones fade in.

`scripts/rescale.py` implements 4.1–4.4.

## 5. Formulas on screen

**5.1 What is written as an equality is exact.** (user) A truncated decimal in an
equality carries its dots: $\ln n-\ln100=\ln n-4.6\ldots$. Otherwise the
equality before it is false. Use $\approx$ where only an approximation is
meant.

**5.2 The argument of a log taken on screen is in parentheses** when it is more
than one symbol. (user) Write $\ln(n!)$ and $\ln\big(\prod\cdots\big)$, not
$\ln n!$. A single-letter argument may stay bare: $\ln p$.

**5.3 A formula on screen agrees with the narration.** (review) When the
narration and the formula say different things (which of two series is $a$
times the other), the formula is not changed to match a mistake. The
discrepancy goes to the user as a question, and the narration is fixed by
them.

## 6. Layout and text

**6.1 Keep the bottom band free.** (review) Burned-in subtitles take the band
below about $y=-2.9$, two lines of them. Plots, labels and timelines stay above
it.

**6.2 Nothing touches.** (review) Labels, formulas and portraits must not overlap
or touch, whether in the plan's positions or mid-animation. When two things
compete for a place, move the one that matters less. Do not shrink both.

**6.3 Hebrew on screen is `MarkupText`, and it fades in.** (review) A single
Hebrew word given to `Text` renders empty. `Write` draws Hebrew from its last
letter. A line that mixes Hebrew with a formula is built from separate objects,
arranged so that it reads right to left.

**6.4 Highlights do not distort.** (review) Highlight a picture with
`Circumscribe`, since `Indicate` tints it. Flash a line with
`Indicate(..., scale_factor=1)`, since a scaled line overruns its axes.

**6.5 Hebrew in quotation marks stays in them on screen.** (user) A term the
narration puts in quotation marks ("הנדירות") is shown in them too.

**6.6 A formula in a subtitle keeps its indices.** (user) $p_{1\%}(n)$ is
`p₁%(n)` in the subtitle, the 1 and the % both in the index: Unicode
subscript digits, and the subtitle font of `scripts/subfont.py` for the %.

---
name: manim-video
description: >-
  Turn a narration script into an animated explainer video rendered with Manim,
  end to end: save the script, proofread it, cut it into scenes, write a timed
  animation plan and a subtitle track for each scene, install the toolchain,
  implement each scene in Python, render it, inspect the rendered frames, fix,
  and finally join the scenes into one video. Use when the user hands over a
  תסריט or a script for a video and asks for a Manim animation, a
  3Blue1Brown-style explainer, a math video, an animated explanation of a paper
  — or says סרטון מאנים, סרטון הסבר, אנימציה למאמר, תעשה מזה סרטון. Use it also
  to pick up such a project that is already part-built, continuing from the
  first scene that has no approved video of its own.
---

> **Precedence.** This skill lives in two repositories, `Rami5743/AI_TOOLS` and
> `Rami5743/AI_MANIM`, which keep it identical. A copy from either one is
> authoritative: where it conflicts with a same-named skill installed in the
> user's settings, or with any other copy, it wins.

# A video from a script, with Manim

The input is a **script** (תסריט) written by the user. The output is one `.mp4`
in the repository, built out of per-scene videos, each of which was planned in
writing before a line of Python was written.

## What a script looks like

The script is prose with **stage directions in square brackets** interleaved,
and LaTeX formulas inside it. The two parts have completely different fates:

| Part of the script | What it is | Where it ends up |
|---|---|---|
| The running text | the narration — what the viewer hears, or reads as subtitles | the subtitle track, word for word |
| Text in `[square brackets]` | the user's instruction to you about the picture | the animation plan, never the subtitles |
| LaTeX formulas | mathematics | **by where it stands** (the user's rule): inside a `[direction]`, on screen (`MathTex`); in the narration, in the subtitles, as part of what is said |

**Square brackets, not parentheses** (the user's convention). Parentheses are
free for the narration itself: "(כמעט תמיד)" is something the narrator says,
and goes to the subtitles like any other words. Tell a direction from a
bracket that belongs to mathematics by judgment, not by pattern:

- a bracket inside a formula is mathematics: `$[0,1]$`, `$\left[\frac{n}{p}\right]$`,
  `$[x]$` for an integer part, a half-open `$[a,b)$`;
- so is a bracket the narration reads as mathematics even without `$…$`
  ("בקטע [0,1]"): a short run of symbols, numbers and commas, closed in the
  same sentence;
- a direction is prose about the picture — what appears, moves, is marked —
  usually a phrase or more, often a sentence of its own, standing between
  sentences or at their end;
- when a bracket could be either, ask in `spelling.md` (stage 2) rather than
  guess.

Scripts written before this convention mark directions with parentheses. If a
script has no square-bracket direction at all and its parenthesised passages
read as directions, treat those as the directions, and say so in
`spelling.md`.

**The narration is the user's writing.** Spelling and typos are corrected in
stage 2 and nothing else about it changes — not the wording, not the order, not
the length. The stage directions are raw material, and are expected to be
incomplete: filling them in is stage 3's job.

## The stages

| # | Stage | Output | Saved |
|---|---|---|---|
| 1 | The script arrives | `script/script-original.<ext>`, byte for byte as given | yes |
| 2 | Proofreading | `script/script.md` | yes |
| 3 | The plan | `scenes.md` and one directory per scene | once per scene |
| 4 | The toolchain | nothing in the project | — |
| 5 | Implementation | `scene.py` and `out/NN-slug.mp4` per scene | once per scene |
| 6 | Integration | `final/<project>.mp4` and `final/<project>.srt` | yes |

**Saving a step** means what the place allows, decided once at the start:

- in a git repository you can push from: commit, and push;
- in a git repository you cannot push from (a sandbox that blocks pushes, as
  Cowork does): commit, and tell the user once that the pushes are theirs to
  make;
- with no repository at all — a working folder, a container of your own:
  nothing more than the files in the project directory.

Wherever the skill says *commit* or *push* below, read *save*. In every case
the files are handed to the user in chat as they are finished: that is the
delivery, and it never depends on a repository.

Stages run in order and do not interleave, with one exception: stage 4 is pure
setup and is started in the background at the very beginning, so that the
toolchain is ready by the time stage 5 needs it.

## Layout

The project lives in a directory of its own — in the repository the user
names, or, with no repository, in the working folder (a folder the user
connected, or your own container) — `video/<project-slug>/` unless they say
otherwise.

```
video/<project-slug>/
  script/
    script-original.md      # exactly as handed over
    script.md               # stage 2: the same script, spelling corrected
    spelling.md             # stage 2: what was changed, and what was left alone
  scenes.md                 # the master file
  scenes/
    01-<slug>/
      description.md        # the animation plan: shot list with timings
      subtitles.srt         # this scene's narration, cut into cues
      assets/               # images and data downloaded for this scene
      scene.py              # stage 5
      out/01-<slug>.mp4     # stage 5, the approved render
  final/
    <project-slug>.mp4
    <project-slug>.srt
```

Scene directories are numbered from `01` with a two-digit prefix, so that the
lexical order is the order of the video. A slug is two or three words, lowercase
and hyphenated, in English even when the script is in Hebrew — it is a path, not
a title.

## The animation rules

`references/animation-rules.md` is the rulebook for how things move, appear,
disappear and keep time. Most of it was laid down by the user. Read it before
writing any plan, and again before implementing. In short:

- **Time.** An animation starts with the cue that speaks of it. Silence only
  where an animation outlasts its cue. The first cue of a scene is held about
  3 s. One `timeline.py` per scene feeds both the plan and the code.
- **Change moves, coming and going fades.** What changes turns into what it
  becomes, piece by piece and by meaning: formulas, labels, captions,
  curves. Only what appears fades in, and only what goes away fades out.
- **Zooms.** The axis stretches, ticks and numbers travel with their values,
  finer ones fade in as space opens and out as they crowd, the width changes
  geometrically, and the zoom goes all the way to the scale that is needed.
- **Changes of scale.** One map moves every point, tick and number. A number
  present in both scales changes notation while travelling (1000000 into
  $10^6$). The map keeps the values in view in view (Box–Cox for linear to
  log). A different quantity on the axis is not a change of scale: fade.
- **Formulas.** An equality on screen is exact (4.6…, not 4.6). A log's
  compound argument is in parentheses. A formula never bends to match a
  mistake in the narration: that is a question for the user.
- **Layout.** Keep the subtitle band free, nothing touches, Hebrew is
  `MarkupText` and fades in, and highlights do not distort.

## Stage 1 — the script arrives

Save it under `script/` **unchanged**, in the format it arrived in, and commit
it before touching anything. That file is the reference every later dispute is
settled against, so it never gets edited. If the user pasted the script into
chat rather than uploading a file, write the paste to `script-original.md`
verbatim and say in the commit message that it came from chat.

## Stage 2 — proofreading

Produce `script/script.md`: the same script with spelling, typos and obvious
grammatical slips corrected, and nothing else.

The rules are below, complete. (If a `fix-spelling` skill is installed, it
is the same discipline for a paper; these rules are what it comes to for a
script.) The whole design is one boundary: **a correction that is certain goes
in; one that is not goes to the user as a question, never into the file.**

**Read it all, in order, at the pace of reading** — not with a spell checker or
a search for suspicious words, which miss the typo that makes a real word (form
for from, a dropped word, a verb that no longer agrees). Read the formulas
closely enough to see which letter stands for what, and read the stage
directions too. Keep a list while reading (the line, the exact string, the
correction, certain or not) and apply it afterwards: editing while reading is
how the reading stops being careful.

**Corrected, when certain:**

- spelling, including a proper name spelled wrong;
- a typo that makes a real word, where the sentence leaves no doubt;
- a doubled word, a word plainly dropped;
- grammar: agreement, number, gender, a wrong preposition in a fixed phrase;
- punctuation that is plainly wrong, an unmatched bracket or quotation mark;
- a slip of the pen inside a formula: a variable called by the wrong name, an
  index the rest of the line fixes otherwise, a mismatched delimiter.

**Certain** means you can name the rule that is broken, and there is exactly
one correction. It is not certain when two corrections are reasonable and say
different things, when the sentence might be right under another reading, when
the usage might be the user's own (check the rest of the script first), when
the correction depends on what the mathematics says rather than on the
sentence, or when the phrase is merely clumsy — that is style. When in doubt,
it is not certain.

**Never touched:** the wording, the order and the length of the narration
(style is not corrected, and not reported either unless it is ambiguous); the
user's terminology and anything the script defines; spelling variants used
consistently (in Hebrew, full or defective spelling; in English, British or
American); and the mathematics. A slip of the pen is a place where the formula
and what the script means came apart; a value, an exponent, a sign, a
quantifier or the direction of an inequality is a claim, and a claim that
looks wrong is reported, never repaired.

Apply the corrections with a script, as exact strings, aborting if a string
does not occur the expected number of times — never a loose replacement of a
short word.

`script/spelling.md` holds the report, in three sections, each item tagged so
the user can answer by quoting the tag. Tags are assigned once and never
reused; a later pass appends with the next free number.

| Section | Tags | What |
|---|---|---|
| Corrections applied | `A1`, `A2`, … | before and after, so the user can spot-check the silent edits |
| Left for the user | `Q1`, `Q2`, … | the text, the candidate corrections, why it is not certain |
| Other things noticed | `O1`, `O2`, … | anything else seen on the way: a direction that contradicts the narration, a formula that looks wrong, a term used before it is introduced |

While reading, also normalise the mechanical shape of the file, which is not a
change to the script: one scene-sized paragraph per block, bracketed
directions kept on their own lines where they already stand alone, LaTeX in
`$…$` and `$$…$$`. List in `spelling.md` every bracket you read as
mathematics rather than as a direction, and every one you were unsure of.

Commit, and give the user `script.md` and `spelling.md` in chat.

## Stage 3 — the plan

This is the stage that decides whether the video works. It is done in full, for
every scene, **before any Python is written**.

### 3a. Cut the script into scenes

A scene is **one idea**, not one shot and not one screenful. It may begin and
end mid-picture: objects are allowed to survive from the end of one scene into
the beginning of the next, and saying so explicitly is part of the plan. What
forces a cut is a change of subject, not a fade to black.

Aim at 30–90 seconds a scene. A scene past two minutes is two ideas that have
not been separated yet. A scene under fifteen seconds belongs to its neighbour
unless it is a deliberate beat.

### 3b. Write the animation plan for each scene

`description.md`, in the format of `references/plan-format.md`. It is detailed
enough that the Python is transcription rather than invention, and it obeys
`references/animation-rules.md`:

- every object on screen, with its position, scale and colour;
- every formula **written out in the exact LaTeX that will be rendered**, not
  described in words. A formula the script left vague is pinned down here, and
  the choice is recorded;
- every transition, named by the Manim animation that will perform it;
- what the scene inherits from the previous one and what it leaves behind.

Where the script's stage direction is silent — and it usually is —
decide, and mark the decision with `[fill]` so that the user can see at a glance
what was yours rather than theirs.

### 3c. Fetch what the scene needs from outside

Portraits, historical plots, logos, a table of data. Download them into the
scene's `assets/`, one directory per scene even if two scenes share an image,
and record in `description.md` where each file came from and whether it may be
used. An asset whose licence cannot be established is replaced by a drawing
made in Manim, and the substitution is noted.

### 3d. Time it

Every element of the plan carries a start time and a duration, relative to the
start of its own scene, and the scene's total is the sum. Timing follows one
rule:

> **The subtitle track is the clock.** The animation is timed to the narration,
> never the other way round.

So 3e comes before the timeline is finalised, and the timeline is built on top
of the cue times rather than beside them.

### 3e. Cut the narration into subtitles

`subtitles.srt`, standard SRT, times relative to the start of the scene — stage
6 shifts them.

| Rule | Value |
|---|---|
| Reading rate | 5.05 **syllables** per second, every formula and number counted as it is read aloud |
| Cue duration | `max(1.8 s, syllables / 5.05)`, rounded up to 0.1 s |
| Longest cue | 7.1 s — split it instead |
| Gap between cues | 0.15 s |
| Lines per cue | at most 2 |
| Characters per line | at most 42 |
| Where to break | at a clause boundary, never inside a formula and never between a number and its unit |

**Measure the rate in syllables, never in characters** (the user's rule). A
formula is short on the page and long in the mouth: imagine it read aloud and
count that — $r_{1\%}$ is "אר אחוז", $\ln p/p$ is "לוג פה חלקי פה". The project
keeps a table of how each formula and number of its narration is read
(`readings.py` beside `narration.py`), and `scripts/syllables.py` counts a cue
from it: a run with no reading is an error, not a zero. Hebrew words written
without vowels are estimated from their letters (see the script).

The rate is the user's: the first project began at 13 characters per second,
which on its narration was 5.94 syllables per second, and the user settled on
15% below that, the shortest and longest cue growing in proportion. Record it
at the top of `scenes.md`, so that recalibrating the whole video is one edit
in one place (and see `references/animation-rules.md`, 1.5, for what else a
change of rate means). A scene gets a 0.8 s silent beat before its first cue
and after its last.

A formula in a subtitle keeps its indices: $p_{1\%}(n)$ is written `p₁%(n)`,
with the Unicode subscript digits, and the % is shown as an index too by the
subtitle font that `scripts/subfont.py` builds (Unicode has no subscript %).
Burn previews and the final video with that font, and use it for the subtitles
of any web page that plays the videos.

Add nothing to the narration and drop nothing from it. A stage direction
never becomes a subtitle; a parenthesis in the narration always does.

### 3f. One directory per scene

`description.md`, `subtitles.srt`, `assets/`. No `scene.py` yet — stage 3 plans
and stage 5 implements, and mixing them is how a plan ends up written to match
the code that already exists.

### 3g. Deliver each scene as it is finished

Scene by scene, not all at the end. For each one, in this order:

1. save the scene directory on its own (commit and push where possible);
2. zip the directory to the scratchpad and hand the user the zip;
3. paste `description.md` and `subtitles.srt` into the chat reply.

The chat copy is not a courtesy. It is how the user reviews the plan while the
next scene is being written, and a correction arriving mid-stage is cheap
exactly because of it.

### 3h. The master file

`scenes.md` lists the scenes in order: number, slug, one-line subject, planned
duration, cumulative start time, what it inherits from the scene before it, and
its state (`planned`, `implemented`, `rendered`, `approved`). It carries the
reading rate, the resolution and frame rate, and the running total. It is
rewritten at the end of every scene in stages 3 and 5, and it is the file to
read first when picking the project up again.

## Stage 4 — the toolchain

Python, Manim Community, a LaTeX distribution, FFmpeg. With root (a container
of your own, a cloud session), the system packages; without it (a sandbox
such as Cowork's), the user-space route of `references/environment.md`. Some
sandboxes limit how long one command may run (a few minutes): render a long
scene in pieces, as that file describes — Manim keeps every finished
animation and an interrupted render picks up where it stopped. Install as in
`references/environment.md`, started in the background at the beginning of the
session. Verify with the smoke test in that file before stage 5 begins — a
missing LaTeX package shows up as a failed render twenty minutes later and is
easy to mistake for a bug in the scene.

## Stage 5 — implementation

One scene at a time, to completion. The graphic style is **Manim's defaults**,
which are the 3Blue1Brown style: dark background, white strokes, the built-in
palette for accents. Do not set a theme, do not import a style file, do not
restyle what the defaults already do. How things move, appear, disappear and
keep time is `references/animation-rules.md`, the rules the user laid down for
every video. `references/manim-craft.md` holds the idioms, the pitfalls, the
notes on the helpers and the rendering commands.

The loop, per scene:

1. write `scene.py` from `description.md`;
2. render at draft quality;
3. **look at the result** — extract frames and read them, as
   `references/review-loop.md` describes. A render that exits 0 has not been
   checked. Text runs off the frame, objects overlap, a `MathTex` comes out
   with the wrong spacing, an animation ends before its subtitle does, and none
   of that raises an exception;
4. fix and go back to 2.

Leave the loop only when the render matches `description.md` — every element
present, in the described place, at the described time, and the last animation
finishing with the last subtitle. Then render at final quality, and:

1. save `scene.py`, `out/NN-slug.mp4` and a preview with the subtitles
   burned in (`references/review-loop.md`), and update `scenes.md` to
   `approved` (commit and push where possible);
2. give the user both videos in chat, named, with the scene number and the
   duration.

Then the next scene. A scene is never left half-implemented to start another.

**Every approved render is delivered, and delivery is logged.** Handing the
user the files is part of approving a scene, not an optional extra: right
after saving, send both videos, then record the delivery with
`scripts/deliveries.py record <project> <scene>`. The log keeps the hash of the
render that was sent, so a scene that is re-rendered after a correction counts
as undelivered until it is sent again. Re-rendering several scenes is no
reason to batch their delivery: send each as it is approved.

## Stage 6 — integration

**First run `scripts/deliveries.py check <project>`, and do not integrate
while it fails.** It lists every scene whose current render the user has not
been sent; send those, record them, and only then go on. (The first project
built with this skill integrated before its last scene had been delivered, and
the user had to ask for it.)

Join the approved scene videos in the order of `scenes.md`, and merge the
subtitle files with the cumulative offsets, into `final/`. Use
`scripts/assemble.py`. Check the join: play the seams, confirm no scene was
dropped and no subtitle drifted, and confirm the total matches `scenes.md`.

**Redo only what changed.** A fix to one scene re-renders that scene, and a
neighbour only if it inherits the changed picture (the next scene opens on the
last frame of this one). Everything is re-rendered only when every scene's
timing changes, as with a new reading rate. Joining encodes nothing: the
scenes are joined by stream copy, and with `--burn` the burned-in copy is the
scenes' own subtitled previews joined the same way, as long as each preview
is newer than its render and its subtitles. So a tool that regenerates
subtitles or timings must leave a file untouched when its content is the same,
or every preview looks stale and the whole video is burned again.

Save the final video and its subtitle track (commit and push where possible),
and hand the user the file in chat.

### Another language

**Subtitles in another language** are a translation cue by cue: one line per
cue of the narration, in the same order, each taking exactly the times of the
cue it translates, written to `scenes/*/subtitles.<lang>.srt`. Keep the
translation in one file next to the narration, and stop when its count and the
cues' disagree. Measure its rate the same way (syllables, formulas as read
aloud in that language) and tighten the wording of any cue that runs fast —
the times stay those of the narration. `scripts/assemble.py` merges them into
`final/<name>.<lang>.srt`.

**A version of the video in another language** changes nothing but the words
on screen. Do it with one switch, never with a copy of a scene: every on-screen
text is defined once with its translations, and the language is chosen at
render time (an environment variable). A line that mixes words with a formula
is built from pieces in reading order, so that right to left and left to right
come from the same code; check that the main language renders exactly as
before (compare the points). Only the scenes whose words differ, and those
that open on their last frame, are rendered again, into `out-<lang>/`; every
other scene is shared. `scripts/assemble.py --project <p> --lang <lang>
--burn` joins the version and its subtitled previews into
`final/<name>.<lang>.mp4`.

## How the run is driven

- **The stages run one after another without stopping for approval.** The user
  asked for the whole pipeline, and every question that comes up is recorded in
  `spelling.md` or marked `[fill]` in a plan rather than asked mid-run.
- **Every step is saved and every step is shown.** Nothing finished waits
  unsaved, and nothing finished is described in chat without the file itself
  being handed over. The project directory (and its repository, where there is
  one) is the record, the chat is the review channel, and both get the same
  thing.
- **At every natural pause — the end of a scene in stage 3, the end of a scene
  in stage 5 — check for new instructions from the user and adopt them before
  starting the next scene.** A correction to a scene already approved is applied
  where it lands and the scenes after it are checked for the same mistake. A
  correction that changes the plan — a different range, a dropped curve — goes
  into the affected `description.md` files first, back to `planned`, and the
  scenes are rebuilt from the edited plans; the scene the run was on waits.
- In a repository, work on the branch the session is on, and do not open a
  pull request unless asked.

## The boundary

- The narration is not rewritten. Stage 2 corrects, stage 3 cuts into cues, and
  that is all that ever happens to the user's words.
- The mathematics is not changed. A formula in the script that looks wrong is
  reported, not corrected — the exception is a slip of the pen that stage 2 is
  certain of (see its rules).
- The plan is not retrofitted to the code. If stage 5 shows that a scene cannot
  be built as planned, edit `description.md` first, say why in the commit
  message, and then write the Python against the edited plan.

## Reference

| File | What is in it |
|---|---|
| `references/animation-rules.md` | **the rules** for timing, motion versus fades, zooms, changes of scale, formulas and layout on screen |
| `references/plan-format.md` | the exact shape of `description.md`, `subtitles.srt` and `scenes.md`, with a worked example |
| `references/manim-craft.md` | the default style, the idioms worth using, Hebrew on screen, the pitfalls, the render commands |
| `references/review-loop.md` | how to actually inspect a rendered video, and the checklist to inspect it against |
| `references/environment.md` | installing the toolchain, and the smoke test |
| `scripts/frames.py` | contact sheets and single frames out of a rendered video |
| `scripts/assemble.py` | joining the scene videos and merging the subtitle files |
| `scripts/timing.py` | the clock a scene plays against: animations at the absolute times of `timing.json`, or at the rows of the scene's `timeline.py` (`T.row`) |
| `scripts/timeline_md.py` | writes a scene's Timeline table in `description.md` from its `timeline.py` |
| `scripts/zoomline.py` | a number line that really zooms — the axis stretches and ticks travel with their values |
| `scripts/deliveries.py` | the log of renders sent to the user; `check` must pass before integration |
| `scripts/rescale.py` | a change of scale (linear to log, any rescaling): one map for curves, ticks and numbers, numbers morphing between notations |
| `scripts/syllables.py` | the length of a cue in syllables, formulas counted as read aloud from the project's table of readings |
| `scripts/subfont.py` | the subtitle font ("Subtitle Sans"), in which a % after a subscript digit is a subscript too; `--burnable` for burning with libass, `--web` for a page |

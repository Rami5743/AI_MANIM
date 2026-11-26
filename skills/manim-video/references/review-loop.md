# Looking at the render

A Manim render that exits 0 proves that the Python ran. It proves nothing about
the video. Everything that actually goes wrong in a scene goes wrong silently:

- text or a formula sticking out of the frame;
- two objects overlapping where the plan wanted them apart;
- a `MathTex` compiled but spaced wrongly, or the wrong glyph highlighted;
- an animation that finishes ten seconds before its subtitle, or after it;
- an object the previous `self.play` was supposed to remove, still there;
- a curve drawn with the default easing where the plan said `linear`, so that
  it races the narration and then waits.

So the loop is: render, **look**, fix. Not: render, read the log, commit.

## How to look

Frames are read with the Read tool, which is the only way they are seen.
`scripts/frames.py` produces them.

```bash
# 1. the whole scene at a glance — one frame every half second, tiled and labelled
python3 <skill>/scripts/frames.py sheet media/videos/scene/720p30/Scene.mp4 review/

# 2. the moments the plan names — full resolution, one file each
python3 <skill>/scripts/frames.py at media/videos/scene/720p30/Scene.mp4 review/ 0.9 8.2 20.0 71.5

# 3. the arithmetic
python3 <skill>/scripts/frames.py info media/videos/scene/720p30/Scene.mp4
```

Both commands print the absolute path of every file. Read the contact sheets
first — they catch layout and continuity in one look. Then read a full frame at
each row of the timeline table in `description.md`, because a tile 360 pixels
wide will not show a subscript set wrongly.

A static layout needs no video at all. `manim -qm -s` writes a single PNG and
takes seconds, which is the right tool while a formula is being positioned.

## The checklist

Against `description.md`, per scene:

| Check | How |
|---|---|
| **Duration** | `frames.py info` against the scene's planned duration. More than 0.1 s apart means the `run_time`s and `wait`s do not add up to what was planned. |
| **The last cue** | the final subtitle ends before the tail silence, and nothing moves after it. |
| **Every object in the plan** | present, at the stated position, in the stated colour, at the stated time. |
| **Nothing outside the frame** | no glyph touching an edge in any tile. |
| **Nothing overlapping** | unless the plan asked for it. |
| **Formulas** | each one read character by character against the LaTeX in the plan's formula list. This is where a dropped subscript hides. |
| **What is inherited** | the first frame holds exactly what the previous scene left behind, and nothing else. |
| **What is left behind** | the last frame holds exactly what the next scene expects. |
| **Easing** | a traced curve or a climbing counter advances by equal steps across consecutive tiles. Tiles that bunch at the ends mean the default easing is still in place. |

A failure of the last three is a continuity break, and it is worth re-reading
the neighbouring scene's plan rather than patching this one.

## Subtitled previews

Hand the user each scene with its subtitles burned in, besides the clean
render: a silent video with no narration cannot be followed otherwise. With
FFmpeg's `subtitles` filter (libass), two settings decide whether Hebrew comes
out right:

```bash
ffmpeg -i out/NN-slug.mp4 -vf "subtitles=subtitles.srt:force_style='FontName=DejaVu Sans,FontSize=16,Encoding=-1,Outline=1.2,MarginV=8'" preview/NN-slug-subtitled.mp4
```

- `Encoding=-1` makes libass take each line's base direction from its text.
  Without it every line is laid out left to right and the full stop of a
  Hebrew cue lands on its right.
- `FontSize=16` and `MarginV=8` keep two lines inside the bottom band that the
  scenes leave free.

Then read a frame with a cue that holds a formula, and one with a two-line
cue, before calling the preview done.

## When the fix is to the plan

Sometimes the render is faithful and the plan was wrong — a formula does not fit
at the size it was given, an animation cannot take the time it was allotted.
Then edit `description.md` first, say in the commit message what changed and
why, and write the Python against the edited plan. The plan is the record of
what the video is meant to be, and a plan edited to match code that already
exists records nothing.

## Leaving the loop

Leave it when the checklist passes, not when the render stops being obviously
wrong. Then render once at `-qh`, run `frames.py info` on the final file to
confirm the duration survived the quality change, and only then commit.

# AI_MANIM

A Claude Code plugin with one skill, **manim-video**: hand Claude a narration
script (prose, with the picture described in parentheses and the formulas in
LaTeX) and it produces an animated explainer video with
[Manim](https://www.manim.community/), in the style of 3Blue1Brown:

1. saves and proofreads the script;
2. cuts it into scenes, and writes for each a timed plan and a subtitle track;
3. installs Python, Manim and LaTeX;
4. implements each scene, renders it, looks at the frames, fixes, and
   delivers it;
5. joins the scenes into one video, with and without burned-in subtitles.

The rules it animates by (how a zoom moves, when things fade and when they
move, how the picture keeps time with the narration) are in
`skills/manim-video/references/animation-rules.md`.

## Installing

```bash
claude plugin marketplace add Rami5743/AI_MANIM
claude plugin install ai-manim@ai-manim
```

The same skill is also part of `Rami5743/AI_TOOLS`; the two copies are kept
identical automatically (see `CLAUDE.md`).

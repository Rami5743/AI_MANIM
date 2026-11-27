# AI_MANIM

A Claude Code plugin with one skill, **manim-video**: hand Claude a narration
script (prose, with directions for the picture in [square brackets] and the
formulas in LaTeX) and it produces an animated explainer video with
[Manim](https://www.manim.community/), in the style of 3Blue1Brown.

**The page about it, in Hebrew and English: https://rami5743.github.io/AI_MANIM/**
— what it does, how to write a script, and a ready prompt.

## Installing

```bash
claude plugin marketplace add Rami5743/AI_MANIM
claude plugin install ai-manim@ai-manim
```

Or download the skill alone,
[manim-video.zip](https://github.com/Rami5743/AI_MANIM/releases/latest/download/manim-video.zip),
and unzip it into `~/.claude/skills/` (or a project's `.claude/skills/`).

The rules it animates by (how a zoom moves, when things fade and when they
move, how the picture keeps time with the narration) are in
`skills/manim-video/references/animation-rules.md`.

A second skill, **hebrew-tts**, gives such a video a spoken Hebrew narration:
a speech engine (Azure) reads every word from IPA with its stress marked, one
sentence at a time at its subtitle's time (`skills/hebrew-tts/SKILL.md`).

Both skills are also part of `Rami5743/AI_TOOLS`; the two copies of each are
kept identical (see `CLAUDE.md`).

# AI_MANIM

This repository is a **Claude Code marketplace** whose content is one
**plugin** holding two **skills**: `manim-video`, which turns a narration
script into an animated explainer video rendered with Manim, and
`hebrew-tts`, which makes a speech engine read a Hebrew narration right (the
spoken narration of such a video).

## Layout

```
.claude-plugin/
  marketplace.json   # marketplace manifest: lists the one plugin, source "./"
  plugin.json        # plugin manifest: name, version, "skills": ["./skills"]
skills/
  manim-video/       # the skill: SKILL.md, references/, scripts/
  hebrew-tts/        # the spoken Hebrew narration: SKILL.md, references/, scripts/
.github/
  scripts/sync_manim.py   # keeps both skills identical with AI_TOOLS (see below)
  workflows/skill-zip.yml # publishes the skill as a zip (release "skill")
index.html           # the page about the skill (GitHub Pages), Hebrew and English
site/                # the page's icons, and icon.py that renders them with Manim
.nojekyll
```

## The page

`index.html` is the skill's public page, served by GitHub Pages from `main`
at https://rami5743.github.io/AI_MANIM/. Hebrew is the default; every piece of
text exists in both languages (`data-l="he"` / `data-l="en"`), and the flag
buttons switch between them (`#en` in the address opens English). Keep the
two languages saying the same thing.

The page is short on purpose (the owner cut it down): what the skill does and
what it needs, how to write a script (a table and one plain, uncoloured
example), and a ready prompt that only says where to get the skill. **A change
to the skill that changes any of that (the script format, where it runs, how
to get it) is a change to the page too**, in the same session. Do not grow the
page back into a manual: the skill itself is the manual.

The download is the release asset
`https://github.com/Rami5743/AI_MANIM/releases/latest/download/manim-video.zip`,
rebuilt by `.github/workflows/skill-zip.yml` on every push that changes the
skill. It uses the token GitHub gives every run; no secret is involved.

## The mirrored skills

`skills/manim-video/` and `skills/hebrew-tts/` exist, identical, in two repositories:
`Rami5743/AI_MANIM` (this one) and `Rami5743/AI_TOOLS` (the owner's general
plugin). Either copy may be edited, from any session.

**Rule: every change to `skills/manim-video/` or `skills/hebrew-tts/` is synced to the other
repository in the same session, before the work is reported done.** Nothing
does it automatically.

1. Edit, bump `version` in `.claude-plugin/plugin.json` and the mirrored
   `metadata.version` in `.claude-plugin/marketplace.json`, validate (below),
   commit, push to `main`.
2. Sync, and check that it took:

   ```bash
   python3 .github/scripts/sync_manim.py             # sync, and push both
   python3 .github/scripts/sync_manim.py --check     # must print "in sync"
   ```

   The script uses the session's own git access. If this session cannot push
   to `Rami5743/AI_TOOLS`, attach it (in a cloud session, with the `add_repo`
   tool); if that is refused, tell the user the copies now differ, and why.
3. If only one copy changed since they last agreed, the script copies it; if
   both changed, it merges them three ways and pushes the merge to both; if
   both changed the same lines, it changes nothing and exits with an error —
   show the conflict to the user, merge by hand in either copy, push, and run
   it again.
4. Never edit the other repository's copy by hand to "help" the sync, and
   never copy a whole directory over the other one: that drops whatever was
   edited there since the last sync. Edit one copy; the sync carries it.

Each commit the script makes bumps the patch version of the plugin of the
repository it commits to. `sync_manim.py` is the same file in both
repositories but is **not** carried by the sync: a change to it is made by
hand in both.

## Validating

```bash
claude plugin validate .
claude plugin validate skills --strict
claude plugin validate .claude-plugin/plugin.json
```

## Rules

- Work on `main`. No feature branches or pull requests unless asked.
- `name` in a skill's frontmatter equals its directory name.
- Nothing is committed here that is not one of the two skills, a manifest, the sync, the
  zip workflow, the page (`index.html`, `site/`, `.nojekyll`), the README, or
  these notes.

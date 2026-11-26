# AI_MANIM

This repository is a **Claude Code marketplace** whose content is one
**plugin** holding one **skill**, `manim-video`: it turns a narration script
into an animated explainer video rendered with Manim.

## Layout

```
.claude-plugin/
  marketplace.json   # marketplace manifest: lists the one plugin, source "./"
  plugin.json        # plugin manifest: name, version, "skills": ["./skills"]
skills/
  manim-video/       # the skill: SKILL.md, references/, scripts/
.github/
  scripts/sync_manim.py   # keeps the skill identical with AI_TOOLS (see below)
```

## The mirrored skill

`skills/manim-video/` exists, identical, in two repositories:
`Rami5743/AI_MANIM` (this one) and `Rami5743/AI_TOOLS` (the owner's general
plugin). Either copy may be edited, from any session.

**Rule: every change to `skills/manim-video/` is synced to the other
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
- `name` in the skill's frontmatter equals its directory name.
- Nothing is committed here that is not the skill, a manifest, the sync, or
  these notes.

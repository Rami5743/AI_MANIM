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
  workflows/sync-manim-video.yml   # the mirror (see below)
  scripts/sync_manim.py
```

## The mirrored skill

`skills/manim-video/` exists, identical, in two repositories:
`Rami5743/AI_MANIM` (this one) and `Rami5743/AI_TOOLS` (the owner's general
plugin). Either copy may be edited, from any session. Keeping them identical
is the job of `.github/scripts/sync_manim.py`, which the workflow
`.github/workflows/sync-manim-video.yml` runs after every push to `main` that
touches the skill, in either repository:

- if only one copy changed since they last agreed, it is copied to the other;
- if both changed, their edits are merged three ways, and the merge goes to
  both;
- if both changed the same lines, nothing changes and the run fails (GitHub
  e-mails the owner). Then merge by hand in either copy and push; the next
  run finds them equal, or copies the result.

Each commit the sync makes bumps the patch version of the plugin of the
repository it commits to.

**When you edit the skill:**

1. Edit, bump `version` in `.claude-plugin/plugin.json` and the mirrored
   `metadata.version` in `.claude-plugin/marketplace.json`, validate (below),
   commit, push to `main`.
2. If this session can push to the other repository too, sync now instead of
   waiting for the workflow, and check that it took:

   ```bash
   python3 .github/scripts/sync_manim.py
   python3 .github/scripts/sync_manim.py --check
   ```

   The second must print `in sync`. A conflict is reported, not resolved:
   show it to the user.
3. Never edit the other repository's copy by hand to "help" the sync, and
   never copy a whole directory over the other one: that drops whatever was
   edited there since the last sync. Edit one copy; the sync carries it.

The sync files (`sync-manim-video.yml`, `sync_manim.py`) are themselves the
same in both repositories, but are **not** carried by the sync. A change to
them is made by hand in both.

The workflow needs the repository secret `SYNC_TOKEN` in both repositories:
a fine-grained personal access token with *Contents: Read and write* on both.
Without it the workflow fails at its first step and says so; the skill is then
synced only when a session runs the script.

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

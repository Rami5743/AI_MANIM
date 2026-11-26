#!/usr/bin/env python3
"""Keep skills/manim-video identical in Rami5743/AI_TOOLS and Rami5743/AI_MANIM.

This file is the same in both repositories. Run it from a checkout of either
one, on main ("here"). The other repository is "there".

    python3 .github/scripts/sync_manim.py --check   # report, change nothing
    python3 .github/scripts/sync_manim.py           # sync, and push both

Nothing runs it automatically: the rule in both repositories' CLAUDE.md is
that the session that changes the skill runs it, right after pushing, and
checks with --check that the two copies agree. It uses the session's own git
credentials; no token or secret is involved.

It decides by content, not by who pushed last. The git tree hash of the skill
directory names its exact contents, and is the same in both repositories for
the same contents. When the two differ, it merges three ways. The base is the
state both sides agreed on most recently: the tree that both histories held at
the same time, latest (by commit times). Each side's change since then is
applied to the other.

    only one side changed since the base   that side is copied to the other
    both changed, and the merge is clean   the merge goes to both
    both changed the same lines            nothing changes, exit 1: show the
                                           conflict to the user, merge by hand
                                           in either copy, push, and run again

Every commit it makes bumps the patch version of that repository's plugin
(.claude-plugin/plugin.json, and metadata.version of marketplace.json), since
consumers see an update only through the version.
"""
import argparse, os, re, subprocess, sys, tempfile

PATH = "skills/manim-video"
PAIR = ("Rami5743/AI_TOOLS", "Rami5743/AI_MANIM")
BRANCH = "main"


def git(*args, cwd=None, check=True, env=None):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                       env={**os.environ, **(env or {})})
    if check and r.returncode:
        sys.exit(f"git {' '.join(args)} failed:\n{r.stderr.strip()}")
    return r


def out(*args, **kw):
    return git(*args, **kw).stdout.strip()


def this_repo():
    if os.environ.get("GITHUB_REPOSITORY"):
        return os.environ["GITHUB_REPOSITORY"]
    url = out("remote", "get-url", "origin")
    m = re.search(r"([^/:]+/[^/]+?)(?:\.git)?/?$", url)
    return m.group(1) if m else url


def other_repo(here):
    names = [p.lower() for p in PAIR]
    if here.lower() not in names:
        sys.exit(f"{here} is not one of {PAIR}")
    return PAIR[1 - names.index(here.lower())]


def fetch():
    """Full history of both main branches. Blobs are not needed for the
    decision (only trees are), so they are filtered where possible."""
    unshallow = ["--unshallow"] if out("rev-parse", "--is-shallow-repository") == "true" else []
    for remote in ("origin", "there"):       # explicit refspecs: a clone may lack them
        git("fetch", "-q", "--filter=blob:none", *(unshallow if remote == "origin" else []),
            remote, f"+refs/heads/{BRANCH}:refs/remotes/{remote}/{BRANCH}")


def tree(ref):
    r = git("rev-parse", "-q", "--verify", f"{ref}:{PATH}", check=False)
    return r.stdout.strip() or None


def history(ref):
    """The periods of ref's history: (tree of the skill directory, from, until),
    in commit times; the last period is open."""
    rows = out("log", "--reverse", "--format=%H %ct", ref, "--", PATH).splitlines()
    periods = []
    for i, line in enumerate(rows):
        c, start = line.split()
        until = int(rows[i + 1].split()[1]) if i + 1 < len(rows) else float("inf")
        t = tree(c)
        if t:
            periods.append((t, int(start), until))
    return periods


def last_agreement(ha, hb):
    """The tree both sides had at the same time, most recently: the base."""
    best = None
    for ta, sa, ua in ha:
        for tb, sb, ub in hb:
            if ta == tb and max(sa, sb) <= min(ua, ub):
                if best is None or max(sa, sb) >= best[1]:
                    best = (ta, max(sa, sb))
    return best and best[0]


def merge(base, ours, theirs):
    env = {"GIT_AUTHOR_NAME": "sync", "GIT_AUTHOR_EMAIL": "sync@localhost",
           "GIT_COMMITTER_NAME": "sync", "GIT_COMMITTER_EMAIL": "sync@localhost"}
    c = {k: out("commit-tree", t, "-m", k, env=env)
         for k, t in (("base", base), ("ours", ours), ("theirs", theirs))}
    r = git("merge-tree", "--write-tree", "--name-only", "--no-messages",
            f"--merge-base={c['base']}", c["ours"], c["theirs"], check=False)
    lines = r.stdout.strip().splitlines()
    if r.returncode == 0:
        return lines[0], []
    return None, lines[1:]


def bump(worktree):
    """Patch +1 in plugin.json; marketplace.json's metadata.version follows."""
    pj = os.path.join(worktree, ".claude-plugin", "plugin.json")
    mj = os.path.join(worktree, ".claude-plugin", "marketplace.json")
    if not os.path.exists(pj):
        return None
    text = open(pj, encoding="utf-8").read()
    m = re.search(r'"version"\s*:\s*"(\d+)\.(\d+)\.(\d+)"', text)
    if not m:
        return None
    new = f"{m.group(1)}.{m.group(2)}.{int(m.group(3)) + 1}"
    open(pj, "w", encoding="utf-8").write(
        text[:m.start()] + f'"version": "{new}"' + text[m.end():])
    if os.path.exists(mj):
        t = open(mj, encoding="utf-8").read()
        t2 = re.sub(r'("metadata"\s*:\s*\{[^{}]*?"version"\s*:\s*")[^"]*(")',
                    lambda k: k.group(1) + new + k.group(2), t, count=1)
        open(mj, "w", encoding="utf-8").write(t2)
    return new


def commit_tree_to(remote, new_tree, message):
    """Commit new_tree as PATH on top of remote/main, bump, push."""
    if tree(f"{remote}/{BRANCH}") == new_tree:
        return True
    with tempfile.TemporaryDirectory() as wt:
        git("worktree", "add", "-q", "--detach", wt, f"{remote}/{BRANCH}")
        try:
            git("rm", "-r", "-q", "--ignore-unmatch", PATH, cwd=wt)
            git("read-tree", f"--prefix={PATH}/", "-u", new_tree, cwd=wt)
            version = bump(wt)
            git("add", "-A", PATH, ".claude-plugin", cwd=wt)
            msg = message + (f"\n\nPlugin version {version}." if version else "")
            git("commit", "-q", "-m", msg, cwd=wt)
            r = git("push", "-q", remote, f"HEAD:{BRANCH}", cwd=wt, check=False)
            if r.returncode:
                return False
        finally:
            git("worktree", "remove", "--force", wt, check=False)
    return True


def once(here, there, check_only):
    fetch()
    ta, tb = tree(f"origin/{BRANCH}"), tree(f"there/{BRANCH}")
    sha_a = out("rev-parse", "--short", f"origin/{BRANCH}")
    sha_b = out("rev-parse", "--short", f"there/{BRANCH}")
    if ta is None and tb is None:
        sys.exit(f"{PATH} exists in neither repository")
    if ta == tb:
        print(f"in sync: {PATH} is tree {ta[:10]} in both")
        return True
    if tb is None:
        plan = [("there", ta, f"Sync {PATH} from {here}@{sha_a}")]
        what = f"{PATH} is missing in {there}"
    elif ta is None:
        plan = [("origin", tb, f"Sync {PATH} from {there}@{sha_b}")]
        what = f"{PATH} is missing in {here}"
    else:
        base = last_agreement(history(f"origin/{BRANCH}"), history(f"there/{BRANCH}"))
        if base is None:
            sys.exit("the two copies never agreed; merge them by hand")
        merged, conflicts = merge(base, ta, tb)
        if merged is None:
            print(f"::error::both copies of {PATH} were edited and the edits "
                  f"conflict in: {', '.join(conflicts)}. Nothing was changed. "
                  f"Merge by hand ({here}@{sha_a}, {there}@{sha_b}).")
            sys.exit(1)
        if merged == ta:
            plan = [("there", ta, f"Sync {PATH} from {here}@{sha_a}")]
            what = f"{there} is behind {here}"
        elif merged == tb:
            plan = [("origin", tb, f"Sync {PATH} from {there}@{sha_b}")]
            what = f"{here} is behind {there}"
        else:
            msg = f"Merge the edits to {PATH} in {here}@{sha_a} and {there}@{sha_b}"
            plan = [("origin", merged, msg), ("there", merged, msg)]
            what = "both were edited; the edits merge cleanly"

    print(what)
    if check_only:
        for remote, _, _ in plan:
            print(f"  would update {here if remote == 'origin' else there}")
        return True
    for remote, new_tree, msg in plan:
        if not commit_tree_to(remote, new_tree, msg):
            return False
        print(f"  updated {here if remote == 'origin' else there}")
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="report, change nothing")
    args = ap.parse_args()

    os.chdir(out("rev-parse", "--show-toplevel"))
    here = this_repo()
    there = other_repo(here)
    if git("remote", "get-url", "there", check=False).returncode:
        git("remote", "add", "there", f"https://github.com/{there}.git")

    for attempt in range(3):         # a push loses a race: fetch and decide again
        if once(here, there, args.check):
            return
        print("  a push was rejected; trying again")
    sys.exit("could not push after 3 attempts")


if __name__ == "__main__":
    main()

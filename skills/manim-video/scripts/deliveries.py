#!/usr/bin/env python3
"""The log of what the user has been sent, so that nothing approved is left
undelivered and nothing is integrated before it was delivered.

    python3 deliveries.py record video/proj 03-sliding-window 04-rarity
    python3 deliveries.py check  video/proj      # exit 1 if anything is unsent

A scene counts as delivered when the sha256 of its current out/*.mp4 is the one
recorded at the time it was handed over. A re-render therefore makes it
undelivered again until it is sent again. Run `check` before stage 6, and do
not integrate while it fails.
"""
import hashlib, json, os, sys


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def renders(project):
    out = {}
    scenes = os.path.join(project, "scenes")
    for name in sorted(os.listdir(scenes)):
        d = os.path.join(scenes, name, "out")
        if os.path.isdir(d):
            mp4 = [f for f in os.listdir(d) if f.endswith(".mp4")]
            if mp4:
                out[name] = os.path.join(d, mp4[0])
    return out


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("record", "check"):
        sys.exit(__doc__)
    cmd, project = sys.argv[1], sys.argv[2]
    log_path = os.path.join(project, "deliveries.json")
    log = json.load(open(log_path)) if os.path.exists(log_path) else {}
    current = renders(project)
    if cmd == "record":
        for name in sys.argv[3:]:
            if name not in current:
                sys.exit(f"{name}: no render under scenes/{name}/out")
            log[name] = digest(current[name])
            print(f"recorded {name}")
        json.dump(log, open(log_path, "w"), indent=1, sort_keys=True)
        return
    missing = [n for n, p in current.items() if log.get(n) != digest(p)]
    for n in current:
        print(f"  {'SENT  ' if n not in missing else 'UNSENT'} {n}")
    if missing:
        print(f"\n{len(missing)} scene(s) not delivered in their current version: {' '.join(missing)}")
        sys.exit(1)
    print("\nevery scene was delivered in its current version")


if __name__ == "__main__":
    main()

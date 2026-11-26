#!/usr/bin/env python3
"""Write the Timeline section of a scene's description.md from its timeline.py.
Run from the project directory (the one holding scenes/):
    python3 /path/to/skills/manim-video/scripts/timeline_md.py 10-factorial
"""
import os, sys
PROJECT = os.getcwd()
sys.path.insert(0, PROJECT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timing import Timing, resolve   # scripts/timing.py, beside this file

LEAD = """Every animation starts with the cue that speaks of it (the user's rule);
a silent stretch is left only where an animation outlasts its cue. This table
is generated from `timeline.py`, which the code reads too."""


def main(key):
    d = os.path.join(PROJECT, "scenes", key)
    T = Timing(os.path.join(d, "scene.py"))
    import importlib.util
    spec = importlib.util.spec_from_file_location("timeline", os.path.join(d, "timeline.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    rows = resolve(mod.ROWS, T)
    def cue_of(t):
        started = [n for n, c in T.cues.items() if c.start <= t + 1e-6]
        if not started:
            return "—"
        n = max(started)
        return str(n) if t < T.cues[n].end - 1e-6 else "—"
    lines = ["## Timeline", "", LEAD, "", "| from | to | cue | what happens |", "|---|---|---|---|",
             f"| 0.00 | 0.80 | — | {getattr(mod, 'HEAD', 'still frame, as the previous scene left it')} |"]
    last = 0.8
    for k, (start, rt, text) in sorted(rows.items(), key=lambda kv: kv[1][0]):
        lines.append(f"| {start:.2f} | {start + rt:.2f} | {cue_of(start)} | {text}; run_time {rt} |")
        last = max(last, start + rt)
    lines.append(f"| {last:.2f} | {T.duration:.2f} | — | hold, through the last cue and the tail |")
    lines.append("")
    p = os.path.join(d, "description.md")
    s = open(p).read()
    i = s.index("## Timeline"); j = s.index("## Notes")
    s = s[:i] + "\n".join(lines) + "\n" + s[j:]
    import re
    s = re.sub(r"\*\*Duration\.\*\* [0-9.]+ s", f"**Duration.** {T.duration:g} s", s, count=1)
    open(p, "w").write(s)
    print(f"{key}: {len(rows)} rows, {T.duration} s")


if __name__ == "__main__":
    for k in sys.argv[1:]:
        main(k)

"""Read a scene's timing.json and keep an explicit clock while building it.

    T = Timing(__file__)
    T.cue(3).start      # absolute start of cue 3, in seconds
    T.play(self, anim, at=5.10, run_time=0.8)   # waits until 5.10, then plays
    T.finish(self)      # waits until the planned duration
"""
import json, os


class _Span:
    def __init__(self, start, end):
        self.start, self.end = start, end


class Timing:
    def __init__(self, scene_file):
        here = os.path.dirname(os.path.abspath(scene_file))
        self.here = here
        with open(os.path.join(here, "timing.json"), encoding="utf-8") as f:
            data = json.load(f)
        self.duration = data["duration"]
        self.cues = {c["n"]: _Span(c["start"], c["end"]) for c in data["cues"]}
        self.cue_data = {c["n"]: c for c in data["cues"]}
        self.pauses = [(e["label"], _Span(e["start"], e["end"])) for e in data["events"] if e["kind"] == "pause"]
        self.clock = 0.0

    def cue(self, n):
        return self.cues[n]

    def words(self, n, phrase):
        """When the narration of cue n reaches the given words: the cue's start
        plus the time of the word the phrase begins in (timing.json carries
        "words": [character index, seconds] for every word of a cue)."""
        c = self.cue_data[n]
        i = c["text"].find(phrase)
        if i < 0 or c["text"].find(phrase, i + 1) >= 0:
            raise KeyError(f"cue {n} has {'no' if i < 0 else 'more than one'} {phrase!r}: {c['text']}")
        if "words" not in c:
            raise KeyError("timing.json has no word times; regenerate it")
        t = max((sec for idx, sec in c["words"] if idx <= i), default=0.0)
        return c["start"] + t

    def pause(self, key):
        """A pause by its index or by a substring of its label."""
        if isinstance(key, int):
            return self.pauses[key][1]
        hits = [span for label, span in self.pauses if key in label]
        if len(hits) != 1:
            raise KeyError(f"{len(hits)} pauses match {key!r}")
        return hits[0]

    @staticmethod
    def now(scene):
        """Seconds of video actually rendered so far. Using this rather than a
        running sum of run_times absorbs the rounding of every animation to
        whole frames, so the scene cannot drift."""
        return scene.renderer.time

    def wait_until(self, scene, t):
        dt = round(t - self.now(scene), 4)
        if dt > 1e-3:
            scene.wait(dt)
        elif dt < -0.05:
            raise RuntimeError(f"timeline overrun: at {self.now(scene):.3f}, asked to wait until {t:.3f}")

    def play(self, scene, *anims, at=None, run_time=1.0, **kw):
        if at is not None:
            self.wait_until(scene, at)
        scene.play(*anims, run_time=run_time, **kw)

    def finish(self, scene):
        self.wait_until(scene, self.duration)


    # ---- the scene's timeline.py: one source for the plan's table and the code

    def _load_rows(self):
        if hasattr(self, "_rows"):
            return
        import importlib.util
        spec = importlib.util.spec_from_file_location("timeline", os.path.join(self.here, "timeline.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self._rows = resolve(mod.ROWS, self)

    def row(self, key):
        """at= and run_time= of a row of timeline.py, for T.play(..., **T.row(key))."""
        self._load_rows()
        start, rt, _ = self._rows[key]
        return dict(at=start, run_time=rt)


def resolve(rows, T):
    """rows: (key, anchor, offset, run_time, text). anchor: a cue number, a
    substring of a pause label, an absolute time (float), ("after", key), or
    ("words", n, "phrase") — when the narration of cue n reaches those words."""
    out = {}
    for key, anchor, offset, rt, text in rows:
        if isinstance(anchor, tuple) and anchor[0] == "after":
            base = out[anchor[1]][0] + out[anchor[1]][1]
        elif isinstance(anchor, tuple) and anchor[0] == "words":
            base = T.words(anchor[1], anchor[2])
        elif isinstance(anchor, int):
            base = T.cue(anchor).start
        elif isinstance(anchor, str):
            base = T.pause(anchor).start
        else:
            base = float(anchor)
        out[key] = (round(base + offset, 3), rt, text)
    return out

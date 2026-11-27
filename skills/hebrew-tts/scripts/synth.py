#!/usr/bin/env python3
"""Speak an SSML narration one sentence at a time, each at its subtitle's time.

    python3 synth.py narration.ssml timing.json out.m4a [--voice V] [--cache DIR]

narration.ssml: one <s> per sentence, a <mark name="..-NN"/> at the start of
each cue (NN = the cue's number in timing.json); its xml:lang is used.
timing.json: the manim-video format, {"duration": s, "cues": [{"n", "start",
"end"}, ...]}. Writes an audio file exactly `duration` long: every sentence
starts at the start of its first cue, loudness -16 LUFS / -1.5 dBTP.

Each sentence is one request (its marks and comments removed) and is cached
by its text and voice, so after a fix only the changed sentences are spoken
again. Prints, for each sentence, where its speech ends and where the next
starts, and warns when it runs into the next (Azure's trailing silence is not
counted).
"""
import argparse, json, os, re, subprocess, sys, wave
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from azure import cached, document  # noqa: E402

LOUD = "loudnorm=I=-16:TP=-1.5"


def speech_end(path):
    """Seconds to the last sample louder than about -44 dBFS."""
    with wave.open(path) as w:
        n, rate, raw = w.getnframes(), w.getframerate(), w.readframes(w.getnframes())
    step = rate // 100
    last = 0
    for i in range(0, n - step, step):
        chunk = raw[2 * i:2 * (i + step)]
        peak = max(abs(int.from_bytes(chunk[j:j + 2], "little", signed=True)) for j in range(0, len(chunk), 8))
        if peak > 200:
            last = i + step
    return last / rate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ssml"); ap.add_argument("timing"); ap.add_argument("out")
    ap.add_argument("--voice", default="he-IL-HilaNeural")
    ap.add_argument("--cache", default=".tts-cache")
    ap.add_argument("--region", default=None)
    a = ap.parse_args()

    ssml = open(a.ssml, encoding="utf-8").read()
    lang = re.search(r'xml:lang="([^"]+)"', ssml).group(1)
    tj = json.load(open(a.timing, encoding="utf-8"))
    cues = {c["n"]: c for c in tj["cues"]}
    sentences = re.findall(r"<s>(.*?)</s>", ssml, flags=re.S)
    starts, files = [], []
    for s in sentences:
        first = int(re.search(r'<mark name="[^"]*?(\d+)"\s*/>', s).group(1))
        starts.append(cues[first]["start"])
        body = re.sub(r"<!--.*?-->|<mark[^>]*/>", "", s)
        files.append(cached(document(body, a.voice, lang), a.cache, a.region))
    for i, (t, f) in enumerate(zip(starts, files)):
        end = t + speech_end(f)
        nxt = starts[i + 1] if i + 1 < len(starts) else tj["duration"]
        print(f"{t:7.2f}  speech ends {end:7.2f}  next {nxt:7.2f}" + ("  OVERLAP" if end > nxt - 0.05 else ""))

    inputs = sum((["-i", f] for f in files), [])
    parts = [f"[{i}:a]adelay={int(round(t * 1000))}:all=1[s{i}]" for i, t in enumerate(starts)]
    graph = ";".join(parts) + ";" + "".join(f"[s{i}]" for i in range(len(files))) + \
        f"amix=inputs={len(files)}:normalize=0,{LOUD},apad,atrim=0:{tj['duration']:.3f}[a]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", graph, "-map", "[a]",
                    "-c:a", "aac", "-b:a", "160k", a.out], check=True)
    print(a.out)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Variants of one whole sentence, for the user to choose by ear.

    python3 ab.py variants.json outdir [--voice V]

variants.json: {"A-current": "<SSML body of the whole sentence>", "B-...": ...}
(the body as it goes inside <s>, phonemes already converted). Writes
outdir/<label>.mp3 for each, and prints each variant's speech length:
a swallowed sound makes it shorter, an extra vowel or an unwanted pause
longer. The numbers choose which variants are worth playing, never which is
right: send the files and ask the user.

Always the whole sentence: a fragment changes the intonation, and confuses
both the engine and the listener.
"""
import argparse, json, os, subprocess, sys, wave
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from azure import cached, document  # noqa: E402


def speech_length(path):
    with wave.open(path) as w:
        n, rate, raw = w.getnframes(), w.getframerate(), w.readframes(w.getnframes())
    step, loud = rate // 100, []
    for i in range(0, n - step, step):
        chunk = raw[2 * i:2 * (i + step)]
        if max(abs(int.from_bytes(chunk[j:j + 2], "little", signed=True)) for j in range(0, len(chunk), 8)) > 300:
            loud.append(i)
    return (loud[-1] - loud[0]) / rate if loud else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("variants"); ap.add_argument("outdir")
    ap.add_argument("--voice", default="he-IL-HilaNeural")
    ap.add_argument("--cache", default=".tts-cache")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    for label, body in json.load(open(a.variants, encoding="utf-8")).items():
        wav = cached(document(body, a.voice), a.cache)
        mp3 = os.path.join(a.outdir, label + ".mp3")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-b:a", "128k", mp3], check=True)
        print(f"{label:24s} speech {speech_length(wav):.2f} s   {mp3}")


if __name__ == "__main__":
    main()

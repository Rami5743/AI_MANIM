#!/usr/bin/env python3
"""Join the approved scene videos into one video, and their subtitle files
into one subtitle track.

    python3 assemble.py --project video/pnt-intro
    python3 assemble.py --project video/pnt-intro --out final/whole.mp4 --burn

With `--project`, the scene directories are `<project>/scenes/*/`, taken in
lexical order — which is why they are numbered `01`, `02`, …. Each contributes
the one `.mp4` under its `out/` and, if present, its `subtitles.srt`. The
default output is `<project>/final/<project name>.mp4` with the merged track
beside it. Subtitles in other languages, `subtitles.<lang>.srt` in the scene
directories (same times as the scene's cues), are merged the same way into
`<project name>.<lang>.srt`; the burned-in copy carries the main track only. `--burn` also writes `<name>-subtitled.mp4`, the same video with
the subtitles burned into the picture. With `--project`, when every scene has
a subtitled preview (`preview/<name>-subtitled.mp4`) at least as new as its
render and its subtitles, those are joined by stream copy: nothing is encoded
again, and a scene that did not change keeps its preview. Otherwise the whole
video is burned from the merged track (in the style of the previews), in the
subtitle font of subfont.py when `<project>/fonts/SubtitleSans.ttf` exists (or
`--fonts DIR`).

Scenes can also be listed by hand:

    python3 assemble.py --videos a.mp4 b.mp4 --subs a.srt b.srt --out whole.mp4

Each subtitle file's times are relative to the start of its own scene. They are
shifted by the measured duration of everything before it, so the merge is exact
only if the videos handed in are the ones the subtitles were written against.

Needs ffmpeg and ffprobe on PATH. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys

CUE = re.compile(
    r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})\s*-->\s*"
    r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})"
)


def need(tool: str) -> str:
    path = shutil.which(tool)
    if path is None:
        sys.exit(f"{tool} is not on PATH. See references/environment.md.")
    return path


def duration(video: str) -> float:
    out = subprocess.run(
        [need("ffprobe"), "-v", "error", "-print_format", "json",
         "-show_format", video],
        capture_output=True, text=True, check=True,
    ).stdout
    return float(json.loads(out)["format"]["duration"])


def parse_srt(path: str) -> list[tuple[float, float, str]]:
    """Return (start, end, text) per cue. Blank-line separated blocks."""
    with open(path, encoding="utf-8-sig") as handle:
        blocks = re.split(r"\n\s*\n", handle.read().strip())
    cues = []
    for block in blocks:
        lines = [line for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        match = None
        body_from = 0
        for index, line in enumerate(lines[:2]):
            match = CUE.search(line)
            if match:
                body_from = index + 1
                break
        if not match:
            sys.exit(f"{path}: a block has no timing line:\n{block}")
        h1, m1, s1, ms1, h2, m2, s2, ms2 = match.groups()
        start = int(h1) * 3600 + int(m1) * 60 + int(s1) + int(ms1.ljust(3, '0')) / 1000
        end = int(h2) * 3600 + int(m2) * 60 + int(s2) + int(ms2.ljust(3, '0')) / 1000
        cues.append((start, end, "\n".join(lines[body_from:])))
    return cues


def stamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def collect(project: str) -> tuple[list[str], list[str | None], list[str]]:
    scenes_dir = os.path.join(project, "scenes")
    if not os.path.isdir(scenes_dir):
        sys.exit(f"no scenes directory at {scenes_dir}")
    videos, subs, names = [], [], []
    for name in sorted(os.listdir(scenes_dir)):
        scene = os.path.join(scenes_dir, name)
        out = os.path.join(scene, "out")
        if not os.path.isdir(out):
            print(f"  skipping {name}: no out/ directory, so it is not approved")
            continue
        mp4s = sorted(f for f in os.listdir(out) if f.endswith(".mp4"))
        if not mp4s:
            print(f"  skipping {name}: out/ holds no .mp4")
            continue
        if len(mp4s) > 1:
            sys.exit(f"{out} holds {len(mp4s)} videos. Leave exactly one.")
        videos.append(os.path.join(out, mp4s[0]))
        srt = os.path.join(scene, "subtitles.srt")
        subs.append(srt if os.path.exists(srt) else None)
        names.append(name)
    if not videos:
        sys.exit("no approved scene videos found")
    return videos, subs, names


def burned_previews(videos: list[str], subs: list[str | None]) -> list[str] | None:
    """The scenes' own subtitled previews (preview/<name>-subtitled.mp4, beside
    out/), when every scene has one at least as new as its render and its
    subtitles. Joining them by stream copy gives the burned-in video without
    encoding anything again: a scene that did not change keeps the preview it
    already had. None if any scene lacks a current preview."""
    found = []
    for video, srt in zip(videos, subs):
        scene = os.path.dirname(os.path.dirname(os.path.abspath(video)))
        name = os.path.splitext(os.path.basename(video))[0]
        prev = os.path.join(scene, "preview", name + "-subtitled.mp4")
        if not os.path.exists(prev):
            return None
        newest = max([os.path.getmtime(video)] + ([os.path.getmtime(srt)] if srt else []))
        if os.path.getmtime(prev) < newest:
            return None
        found.append(prev)
    return found


# The style of the burned-in subtitles: the one review-loop.md uses for previews.
# Encoding=-1 lets libass take the base direction of each line from its text,
# which a right-to-left subtitle needs.
STYLE = ("FontName={font},FontSize=16,Encoding=-1,PrimaryColour=&H00FFFFFF,"
         "OutlineColour=&H00000000,BorderStyle=1,Outline=1.2,Shadow=0,MarginV=8")


def esc(path: str) -> str:
    return path.replace("\\", "\\\\").replace(":", r"\:").replace("'", r"\'")


def concat(videos: list[str], out: str, burn: str | None, fonts: str | None = None) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    listing = os.path.abspath(out) + ".concat.txt"
    with open(listing, "w", encoding="utf-8") as handle:
        for video in videos:
            handle.write(f"file '{os.path.abspath(video)}'\n")

    base = [need("ffmpeg"), "-y", "-v", "error",
            "-f", "concat", "-safe", "0", "-i", listing]
    if burn:
        # With the subtitle font of subfont.py: burn a copy in which the
        # subscript % is written out, since libass applies no contextual forms.
        if fonts:
            from subfont import burnable
            copy = os.path.abspath(out) + ".burn.srt"
            with open(copy, "w", encoding="utf-8") as handle:
                handle.write(burnable(open(burn, encoding="utf-8").read()))
            burn = copy
            vf = (f"subtitles='{esc(burn)}':fontsdir='{esc(fonts)}'"
                  f":force_style='{STYLE.format(font='Subtitle Sans')}'")
        else:
            vf = f"subtitles='{esc(burn)}':force_style='{STYLE.format(font='DejaVu Sans')}'"
        attempts = [base + ["-vf", vf,
                            "-c:v", "libx264", "-pix_fmt", "yuv420p",
                            "-crf", "18", out]]
    else:
        attempts = [
            base + ["-c", "copy", out],
            base + ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", out],
        ]
    for index, cmd in enumerate(attempts):
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            if index:
                print("  stream copy did not take, so the scenes were re-encoded")
            os.remove(listing)
            return
        last = result.stderr.strip()
    os.remove(listing)
    sys.exit("ffmpeg failed:\n" + last)


def merge_subs(subs: list[str | None], offsets: list[float], out: str) -> int:
    cues = []
    for srt, offset in zip(subs, offsets):
        if srt is None:
            continue
        for start, end, text in parse_srt(srt):
            cues.append((start + offset, end + offset, text))
    cues.sort(key=lambda cue: cue[0])
    with open(out, "w", encoding="utf-8") as handle:
        for index, (start, end, text) in enumerate(cues, 1):
            handle.write(f"{index}\n{stamp(start)} --> {stamp(end)}\n{text}\n\n")
    return len(cues)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", help="the project directory, holding scenes/")
    parser.add_argument("--videos", nargs="+", help="scene videos, in order")
    parser.add_argument("--subs", nargs="+",
                        help="scene subtitle files, in the same order; "
                             "write - for a scene that has none")
    parser.add_argument("--out", help="the joined video")
    parser.add_argument("--fonts", help="directory holding SubtitleSans.ttf (subfont.py); "
                        "default <project>/fonts when it exists")
    parser.add_argument("--burn", action="store_true",
                        help="burn the merged subtitles into the picture as well")
    args = parser.parse_args()

    if args.project:
        videos, subs, names = collect(args.project)
        out = args.out or os.path.join(
            args.project, "final",
            os.path.basename(os.path.abspath(args.project)) + ".mp4")
    elif args.videos:
        videos = args.videos
        names = [os.path.basename(v) for v in videos]
        subs = [None if s == "-" else s for s in (args.subs or [])]
        subs += [None] * (len(videos) - len(subs))
        if not args.out:
            sys.exit("--out is required with --videos")
        out = args.out
    else:
        sys.exit("pass --project, or --videos with --out")

    offsets, total = [], 0.0
    print("scene                                     duration    starts at")
    for name, video in zip(names, videos):
        offsets.append(total)
        length = duration(video)
        print(f"  {name:<38} {length:7.2f} s  {total:8.2f} s")
        total += length
    print(f"  {'total':<38} {total:7.2f} s"
          f"   ({int(total) // 60}:{total % 60:05.2f})")

    srt_out = os.path.splitext(out)[0] + ".srt"
    os.makedirs(os.path.dirname(os.path.abspath(srt_out)) or ".", exist_ok=True)
    count = merge_subs(subs, offsets, srt_out)
    print(f"\nwrote {os.path.abspath(srt_out)}  ({count} cues)")
    if args.project:
        # subtitles in other languages: scenes/*/subtitles.<lang>.srt, merged
        # with the same offsets into final/<name>.<lang>.srt
        langs = sorted({f[len("subtitles."):-len(".srt")]
                        for v in videos
                        for f in os.listdir(os.path.dirname(os.path.dirname(v)))
                        if f.startswith("subtitles.") and f.endswith(".srt") and f != "subtitles.srt"})
        for lang in langs:
            per_scene = []
            for v in videos:
                path = os.path.join(os.path.dirname(os.path.dirname(v)), f"subtitles.{lang}.srt")
                per_scene.append(path if os.path.exists(path) else None)
            lang_out = os.path.splitext(out)[0] + f".{lang}.srt"
            n = merge_subs(per_scene, offsets, lang_out)
            missing = sum(p is None for p in per_scene)
            note = f", {missing} scene(s) without" if missing else ""
            print(f"wrote {os.path.abspath(lang_out)}  ({n} cues{note})")

    concat(videos, out, None)
    if args.burn:
        burned = os.path.splitext(out)[0] + "-subtitled.mp4"
        previews = burned_previews(videos, subs) if args.project else None
        if previews:
            concat(previews, burned, None)
            print(f"wrote {os.path.abspath(burned)}  (the scenes' subtitled previews, joined)")
            if abs(duration(burned) - total) > 0.25:
                print("  WARNING: the joined previews are not the length of the video.")
            print(f"wrote {os.path.abspath(out)}  ({duration(out):.2f} s)")
            return
        print("  some scene has no current subtitled preview: burning the whole video")
        fonts = args.fonts
        if fonts is None and args.project:
            fonts = os.path.join(args.project, "fonts")
        if fonts and not os.path.exists(os.path.join(fonts, "SubtitleSans.ttf")):
            fonts = None
        concat(videos, burned, srt_out, os.path.abspath(fonts) if fonts else None)
        if fonts:
            os.remove(os.path.abspath(burned) + ".burn.srt")
        print(f"wrote {os.path.abspath(burned)}  (subtitles burned in)")
    print(f"wrote {os.path.abspath(out)}  ({duration(out):.2f} s)")
    if abs(duration(out) - total) > 0.25:
        print("  WARNING: the joined video is not the sum of its scenes. "
              "Check that every scene was rendered with the same codec, "
              "resolution and frame rate.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Pull still frames out of a rendered video so that they can be looked at.

A render that exited 0 has not been checked. These two commands are how it gets
checked:

    python3 frames.py sheet out/02-counting-primes.mp4 review/
    python3 frames.py at    out/02-counting-primes.mp4 review/ 0.9 8.2 20.0

`sheet` tiles one frame every half second into contact sheets, each labelled
with its timestamp. `at` writes one full-resolution frame per timestamp given.
Both print the absolute path of every file they write; read those files with
the Read tool, which is the only way the frames are actually seen.

Needs ffmpeg and ffprobe on PATH. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
]


def need(tool: str) -> str:
    path = shutil.which(tool)
    if path is None:
        sys.exit(f"{tool} is not on PATH. See references/environment.md.")
    return path


def probe(video: str) -> dict:
    out = subprocess.run(
        [need("ffprobe"), "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", video],
        capture_output=True, text=True, check=True,
    ).stdout
    data = json.loads(out)
    stream = next(s for s in data["streams"] if s["codec_type"] == "video")
    num, den = (stream.get("r_frame_rate") or "0/1").split("/")
    return {
        "duration": float(data["format"]["duration"]),
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "fps": (float(num) / float(den)) if float(den) else 0.0,
        "frames": stream.get("nb_frames"),
    }


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def font_file() -> str | None:
    for candidate in FONT_CANDIDATES:
        if os.path.exists(candidate):
            return candidate
    return None


def cmd_info(args: argparse.Namespace) -> None:
    info = probe(args.video)
    print(f"{args.video}")
    print(f"  duration {info['duration']:.3f} s")
    print(f"  {info['width']}x{info['height']} at {info['fps']:.3f} fps")
    print(f"  frames   {info['frames']}")


def cmd_sheet(args: argparse.Namespace) -> None:
    info = probe(args.video)
    os.makedirs(args.outdir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(args.video))[0]
    pattern = os.path.join(args.outdir, f"{stem}_sheet_%03d.png")

    label = ""
    font = font_file()
    if font and not args.no_timestamps:
        label = (
            f",drawtext=fontfile={font}:text='%{{pts\\:hms}}'"
            ":x=4:y=4:fontsize=16:fontcolor=white:box=1:boxcolor=black@0.7:boxborderw=3"
        )

    vf = (
        f"fps={args.fps}{label},scale={args.width}:-1,"
        f"tile={args.cols}x{args.rows}:padding=4:margin=4:color=0x303030"
    )
    result = run([need("ffmpeg"), "-y", "-v", "error", "-i", args.video,
                  "-vf", vf, "-fps_mode", "vfr", pattern])
    if result.returncode != 0 and label:
        # drawtext is the only part that can be missing from a build of ffmpeg.
        vf = (f"fps={args.fps},scale={args.width}:-1,"
              f"tile={args.cols}x{args.rows}:padding=4:margin=4:color=0x303030")
        result = run([need("ffmpeg"), "-y", "-v", "error", "-i", args.video,
                      "-vf", vf, "-fps_mode", "vfr", pattern])
        label = ""
    if result.returncode != 0:
        sys.exit("ffmpeg failed:\n" + result.stderr.strip())

    per_sheet = args.cols * args.rows
    written = sorted(f for f in os.listdir(args.outdir)
                     if f.startswith(f"{stem}_sheet_") and f.endswith(".png"))
    print(f"{info['duration']:.2f} s of video, one frame every "
          f"{1 / args.fps:.2f} s, {per_sheet} frames to a sheet"
          f"{'' if label else ' (no timestamp labels in this ffmpeg build)'}")
    for index, name in enumerate(written):
        first = index * per_sheet / args.fps
        last = min(((index + 1) * per_sheet - 1) / args.fps, info["duration"])
        print(f"  {os.path.join(os.path.abspath(args.outdir), name)}"
              f"   covers {first:6.2f} s – {last:6.2f} s, left to right, top row first")


def cmd_at(args: argparse.Namespace) -> None:
    os.makedirs(args.outdir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(args.video))[0]
    for time in args.times:
        out = os.path.join(os.path.abspath(args.outdir),
                           f"{stem}_t{time:07.2f}.png".replace(".", "_", 1))
        result = run([need("ffmpeg"), "-y", "-v", "error", "-ss", f"{time}",
                      "-i", args.video, "-frames:v", "1", out])
        if result.returncode != 0:
            sys.exit("ffmpeg failed:\n" + result.stderr.strip())
        print(f"  {out}   t = {time:.2f} s")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_info = sub.add_parser("info", help="duration, resolution, frame rate")
    p_info.add_argument("video")
    p_info.set_defaults(func=cmd_info)

    p_sheet = sub.add_parser("sheet", help="tiled contact sheets of the whole video")
    p_sheet.add_argument("video")
    p_sheet.add_argument("outdir")
    p_sheet.add_argument("--fps", type=float, default=2.0,
                         help="frames sampled per second of video (default 2)")
    p_sheet.add_argument("--cols", type=int, default=5)
    p_sheet.add_argument("--rows", type=int, default=4)
    p_sheet.add_argument("--width", type=int, default=360,
                         help="width of one tile in pixels (default 360)")
    p_sheet.add_argument("--no-timestamps", action="store_true")
    p_sheet.set_defaults(func=cmd_sheet)

    p_at = sub.add_parser("at", help="one full-resolution frame per timestamp")
    p_at.add_argument("video")
    p_at.add_argument("outdir")
    p_at.add_argument("times", type=float, nargs="+")
    p_at.set_defaults(func=cmd_at)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

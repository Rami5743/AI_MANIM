#!/usr/bin/env python3
"""Cut the dead air out of the finished, narrated video: every stretch in
which the picture is frozen and no narration (in any language) says anything
for more than KEEP seconds (default 1.5, the user's rule) is cut to KEEP.
Nothing else changes: no animation and no spoken word is touched; the
subtitle times move with the cuts.

    python3 trim.py --project video/proj --langs he,en [--name proj] [--keep 1.5]

Run it last, after the narration is laid under each scene, before publishing.
The first language is the main one (its files carry no language suffix).
Reads, per scene, scenes/<key>/voiced/<key>.<lang>.mp4 (picture and
narration), preview/<key>-subtitled.mp4 and preview/<key>-<lang>-subtitled.mp4
(burned subtitles), subtitles.srt and subtitles.<lang>.srt. Writes the same,
cut, to scenes/<key>/trimmed/, the cuts to <project>/cuts.json, and the whole
video to final/trimmed/: <name>.<lang>.mp4, <name>.<lang>-subtitled.mp4,
<name>.srt and <name>.<lang>.srt. Renders, timing.json and narration are left
as they are, so a scene re-rendered later is simply trimmed again.

How: a stretch inside a scene keeps KEEP/2 on each side of the cut; a stretch
at a seam (the end of one scene and the start of the next) is one stretch and
keeps KEEP across the seam; the end of the last scene is cut to KEEP. Freezes
are found with ffmpeg freezedetect (back-to-back reports joined: one long
freeze is often reported in pieces), silences with silencedetect at -40 dB.
Measured on the result, the stretches come out at KEEP to KEEP + 0.2 s.
"""
import argparse, json, os, re, subprocess, sys

PROJECT, NAME, LANGS, KEEP = ".", "video", ["he"], 1.5
FREEZE = "freezedetect=n=0.002:d=0.4"
SILENCE = "silencedetect=n=-40dB:d=0.4"


def run(*cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def duration(path):
    return float(run("ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "csv=p=0", path).stdout)


def spans(log, word, total):
    """[(start, end)] from ffmpeg's freeze_/silence_ start/end lines."""
    out, start = [], None
    for k, v in re.findall(rf"{word}_(start|end): ([0-9.]+)", log):
        if k == "start":
            start = float(v)
        elif start is not None:
            out.append((start, float(v)))
            start = None
    if start is not None:
        out.append((start, total))
    return out


def merged(sp, gap=0.08):
    """freezedetect reports one long freeze as several back to back: join them."""
    out = []
    for a, b in sorted(sp):
        if out and a - out[-1][1] <= gap:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def frozen(path, total):
    return merged(spans(run("ffmpeg", "-nostats", "-i", path, "-map", "0:v", "-vf", FREEZE, "-f", "null", "-").stderr,
                        "freeze", total))


def silent(path, total):
    return merged(spans(run("ffmpeg", "-nostats", "-i", path, "-map", "0:a", "-af", SILENCE, "-f", "null", "-").stderr,
                        "silence", total))


def intersect(a, b):
    out = []
    for s1, e1 in a:
        for s2, e2 in b:
            s, e = max(s1, s2), min(e1, e2)
            if e > s:
                out.append((s, e))
    return sorted(out)


def dead_air(key):
    d = os.path.join(PROJECT, "scenes", key, "voiced")
    files = [os.path.join(d, f"{key}.{lang}.mp4") for lang in LANGS]
    total = duration(files[0])
    s = [(0.0, total)]
    for f in files:                 # every language's picture frozen, every narration silent
        s = intersect(intersect(s, frozen(f, total)), silent(f, total))
    return total, s


def plan(keys):
    """Scene-relative cuts {key: [(a, b), ...]}."""
    info = {k: dead_air(k) for k in keys}
    cuts = {k: [] for k in keys}
    eps = 0.06
    for i, k in enumerate(keys):
        total, s = info[k]
        for a, b in s:
            if a > eps and b < total - eps and b - a > KEEP:      # inside the scene
                cuts[k].append((a + KEEP / 2, b - KEEP / 2))
    for i, k in enumerate(keys):                                   # seams
        total, s = info[k]
        tail = next((total - a for a, b in s if b >= total - eps), 0.0)
        if i + 1 < len(keys):
            n = keys[i + 1]
            head = next((b for a, b in info[n][1] if a <= eps), 0.0)
        else:
            n, head = None, 0.0
        if tail + head <= KEEP:
            continue
        keep_tail = min(tail, max(KEEP / 2, KEEP - head))
        keep_head = min(head, KEEP - keep_tail)
        if tail > keep_tail:
            cuts[k].append((total - tail + keep_tail, total))
        if n and head > keep_head:
            cuts[n].append((0.0, head - keep_head))
    return {k: sorted(v) for k, v in cuts.items()}


def keep_expr(cuts):
    return "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in cuts)


def cut_media(src, dst, cuts, audio=True):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    # every file is encoded the same way, cut or not, so that they concatenate
    e = keep_expr(cuts) if cuts else "0"
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", src,
           "-vf", f"select='not({e})',setpts=N/FRAME_RATE/TB"]
    if audio:
        cmd += ["-af", f"aselect='not({e})',asetpts=N/SR/TB", "-c:a", "aac", "-b:a", "160k", "-ar", "48000"]
    else:
        cmd += ["-an"]
    cmd += ["-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", dst]
    r = run(*cmd)
    if r.returncode:
        sys.exit(r.stderr[-1500:])


def shift(t, cuts):
    s = 0.0
    for a, b in cuts:
        if t >= b:
            s += b - a
        elif t > a:
            return a - s
    return t - s


def srt_times(text):
    def ts(x):
        h, m, rest = x.split(":"); sec, ms = rest.split(",")
        return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000
    return ts


def fmt(t):
    t = max(0.0, t)
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def cut_srt(src, dst, cuts, offset=0.0):
    ts = srt_times(None)
    out = []
    for block in open(src, encoding="utf-8").read().strip().split("\n\n"):
        lines = block.split("\n")
        m = re.match(r"(\S+) --> (\S+)", lines[1])
        a, b = shift(ts(m.group(1)), cuts) + offset, shift(ts(m.group(2)), cuts) + offset
        out.append((a, b, lines[2:]))
    return out


def write_srt(dst, cues):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        for i, (a, b, lines) in enumerate(cues, 1):
            f.write(f"{i}\n{fmt(a)} --> {fmt(b)}\n" + "\n".join(lines) + "\n\n")


def concat(files, dst):
    lst = dst + ".txt"
    open(lst, "w").write("".join(f"file '{f}'\n" for f in files))
    r = run("ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", dst)
    os.remove(lst)
    if r.returncode:
        sys.exit(r.stderr[-1500:])


def main():
    global PROJECT, NAME, LANGS, KEEP
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--langs", default="he")
    ap.add_argument("--name", default=None)
    ap.add_argument("--keep", type=float, default=1.5)
    a = ap.parse_args()
    PROJECT, LANGS, KEEP = os.path.abspath(a.project), a.langs.split(","), a.keep
    NAME = a.name or os.path.basename(PROJECT)
    main_lang = LANGS[0]
    suffix = {l: ("" if l == main_lang else f".{l}") for l in LANGS}
    keys = sorted(os.listdir(os.path.join(PROJECT, "scenes")))
    cuts = plan(keys)
    json.dump({k: [[round(x, 3), round(y, 3)] for x, y in v] for k, v in cuts.items()},
              open(os.path.join(PROJECT, "cuts.json"), "w"), indent=1)
    print(f"{sum(len(v) for v in cuts.values())} stretches cut, "
          f"{sum(y - x for v in cuts.values() for x, y in v):.1f} s removed")

    full = {f"{l}{s}": [] for l in LANGS for s in ("", "-sub")}
    srts = {l: [] for l in LANGS}
    offset = 0.0
    for k in keys:
        d = os.path.join(PROJECT, "scenes", k)
        t = os.path.join(d, "trimmed")
        c = cuts[k]
        for l in LANGS:
            dst = os.path.join(t, f"{k}.{l}.mp4")
            cut_media(os.path.join(d, "voiced", f"{k}.{l}.mp4"), dst, c)
            full[l].append(dst)
            prev = f"{k}-subtitled.mp4" if l == main_lang else f"{k}-{l}-subtitled.mp4"
            tmp = os.path.join(t, f"_{l}.mp4")
            r = run("ffmpeg", "-v", "error", "-y", "-i", os.path.join(d, "preview", prev),
                    "-i", os.path.join(d, "voiced", f"{k}.{l}.mp4"), "-map", "0:v", "-map", "1:a",
                    "-c", "copy", "-shortest", tmp)
            if r.returncode:
                sys.exit(r.stderr[-800:])
            dst = os.path.join(t, f"{k}.{l}-subtitled.mp4")
            cut_media(tmp, dst, c)
            os.remove(tmp)
            full[f"{l}-sub"].append(dst)
            name = f"subtitles{suffix[l]}.srt"
            cues = cut_srt(os.path.join(d, name), None, c)
            write_srt(os.path.join(t, name), cues)
            srts[l] += [(x + offset, y + offset, z) for x, y, z in cues]
        offset += duration(os.path.join(t, f"{k}.{main_lang}.mp4"))
        print(f"{k}: {len(c)} cut(s), {sum(y - x for x, y in c):.2f} s")

    f = os.path.join(PROJECT, "final", "trimmed")
    os.makedirs(f, exist_ok=True)
    for l in LANGS:
        concat(full[l], os.path.join(f, f"{NAME}.{l}.mp4"))
        concat(full[f"{l}-sub"], os.path.join(f, f"{NAME}.{l}-subtitled.mp4"))
        write_srt(os.path.join(f, f"{NAME}{suffix[l]}.srt"), srts[l])
    print(f"whole video: {offset:.2f} s")


if __name__ == "__main__":
    main()

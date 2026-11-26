#!/usr/bin/env python3
"""How long a cue takes to say: its syllables, formulas counted as read aloud.

The reading rate of a video is measured in syllables per second, not in
characters: a formula is short on the page and long in the mouth ($r_{1\\%}$ is
three characters and "אר אחוז" three syllables), and a long Hebrew word written
without vowels hides its syllables in a few letters.

    from syllables import count
    READINGS = {"r₁%(n)": "אר אחוז של אן", "ln(n)": "לוג אן", "5%": "חמישה אחוז"}
    count("נסמן את הפונקציה הזאת ב-r₁%(n)", READINGS)   # -> syllables

    python3 syllables.py "טקסט לבדיקה" [--readings readings.json]

Rules:
  - every run of the text that is not a Hebrew or English word (a formula, a
    number, a symbol) must have its spoken form in READINGS, which the project
    keeps next to its narration; a run with no reading is an error, so no
    formula is silently counted as nothing. Longest readings are matched first.
  - a Hebrew word written without vowel points has, as an estimate,
    round(0.55 x its letters) syllables, at least 1. Checked by hand on the
    narration of the first project: right on four words out of five, off by one
    on the rest, with no lean either way, so a cue of a few words comes out
    right.
  - an English word has one syllable per group of vowels (y counted as a
    vowel), less a silent final e, at least 1.
"""
import json, math, re, sys

HEB = re.compile(r"[א-תװ-ײ]+")
LAT = re.compile(r"[A-Za-z]{2,}")
NEUTRAL = re.compile(r"[\s,.:;?!\"'״׳()\-–—⁦-⁩]+")


def hebrew_word(w):
    return max(1, math.floor(0.55 * len(w) + 0.5))


def english_word(w):
    w = w.lower()
    n = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and not w.endswith(("le", "ee")) and n > 1:
        n -= 1
    return max(1, n)


def spoken(text, readings):
    """The text with every formula replaced by its reading. Raises KeyError
    naming the first run that has none."""
    keys = sorted(readings, key=len, reverse=True)
    pattern = re.compile("|".join(re.escape(k) for k in keys)) if keys else None
    out, i = [], 0
    while i < len(text):
        m = pattern.match(text, i) if pattern else None
        # a reading must not start inside a word: "ln" in "ln(n)" yes, "n" in "ברור" no
        if m and (i == 0 or not text[i - 1].isalnum()):
            out.append(" " + readings[m.group(0)] + " ")
            i = m.end()
            continue
        for rx in (HEB, LAT, NEUTRAL):
            m = rx.match(text, i)
            if m:
                out.append(m.group(0))
                i = m.end()
                break
        else:
            j = i
            while j < len(text) and not (HEB.match(text, j) or NEUTRAL.match(text, j)):
                j += 1
            raise KeyError(f"no reading for {text[i:j]!r} in: {text}")
    return "".join(out)


def count(text, readings=None):
    said = spoken(text, readings or {})
    return (sum(hebrew_word(w) for w in HEB.findall(said))
            + sum(english_word(w) for w in LAT.findall(said)))


def main():
    args = sys.argv[1:]
    readings = {}
    if "--readings" in args:
        k = args.index("--readings")
        readings = json.load(open(args[k + 1], encoding="utf-8"))
        del args[k:k + 2]
    for text in args:
        print(count(text, readings), spoken(text, readings).strip(), sep="\t")


if __name__ == "__main__":
    main()

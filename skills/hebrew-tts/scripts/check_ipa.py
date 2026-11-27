#!/usr/bin/env python3
"""Check Hebrew IPA before it is sent to Azure.

    python3 check_ipa.py lexicon.json            # {"word": "ipa", ...}
    python3 check_ipa.py --text "nesaˈmen et"    # one string

Reports: symbols outside Azure's he-IL phone set (they are not rejected; they
come out as some other sound), words of more than one syllable with no stress
mark, more than one primary stress in a word, and a one-syllable word on
STRESS_ME without its mark (content words that fuse with the next word when
unstressed: "די קל לענות" was read "די קלה לענות"). Exit 1 if anything is
reported.
"""
import json, re, sys

ALLOWED = set("aeiouɡgʔfvszʃxhmnlrʁjʒpbtdk͡ˈˌ")
STRESS_ME = {"kal", "tov", "kan", "rak", "ra", "ɡraf", "tur", "loɡ", "sxum", "klum",
             "ʃuv", "kt͡sat", "po", "jeʃ", "ex", "kxu",
             # letter names, also inside a formula's reading
             "en", "ej", "i", "ar", "pi"}


def problems(word):
    p = []
    bad = set(word) - ALLOWED
    if bad:
        p.append("symbols outside the he-IL set: " + "".join(sorted(bad)))
    syll = len(re.findall("[aeiou]", word))
    if syll > 1 and "ˈ" not in word:
        p.append("no stress mark")
    if word.count("ˈ") > 1:
        p.append("more than one primary stress")
    if syll == 1 and word.lstrip("ʔ") in STRESS_ME:
        p.append("one-syllable content word without a stress mark")
    return p


def main():
    if sys.argv[1:2] == ["--text"]:
        items = {w: w for w in " ".join(sys.argv[2:]).split()}
    else:
        items = json.load(open(sys.argv[1], encoding="utf-8"))
    n = 0
    for key, ipa in items.items():
        for w in ipa.split():
            for msg in problems(w):
                print(f"{key}: {w}: {msg}")
                n += 1
    print(f"{n} problem(s)")
    sys.exit(1 if n else 0)


if __name__ == "__main__":
    main()

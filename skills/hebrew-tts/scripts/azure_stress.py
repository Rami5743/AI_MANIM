#!/usr/bin/env python3
"""Standard IPA -> the IPA Azure's Hebrew voices read right.

    python3 azure_stress.py "nesaˈmen et haˈfunktsja"    # nesameˈn et hafuˈnktsja

Azure's he-IL voices read a stress mark as marking the vowel BEFORE it (found
by ear: "nesaˈmen" came out neSAmen, "nesameˈn" nesaMEN), and know no ˌ. So
every ˈ or ˌ moves to just after the vowel of its own syllable. Keep the
lexicon in standard IPA and convert only when building the SSML.

    to_azure(ipa)                 the conversion, word by word
    join(prefix, formula)         a Hebrew prefix hyphened to a formula ("מ-n"):
                                  one word, stress on the formula, a glottal
                                  stop between two vowels ("me" + "en" -> "meˈʔen")
    phoneme(ipa, text)            the <phoneme> element, converted and escaped
"""
import sys
from xml.sax.saxutils import escape, quoteattr

VOWELS = "aeiou"


def to_azure(ipa):
    def word(w):
        out, pending = [], False
        for ch in w:
            if ch in "ˈˌ":
                pending = True
                continue
            out.append(ch)
            if pending and ch in VOWELS:
                out.append("ˈ")
                pending = False
        return "".join(out)
    return " ".join(word(w) for w in ipa.split(" "))


def join(prefix, formula):
    first = formula.split(" ")[0]
    if "ˈ" not in first:
        formula = "ˈ" + formula
    glottal = "ʔ" if prefix[-1:] in VOWELS and formula.lstrip("ˈ")[:1] in VOWELS else ""
    return prefix + glottal + formula


def phoneme(ipa, text):
    return f'<phoneme alphabet="ipa" ph={quoteattr(to_azure(ipa))}>{escape(text)}</phoneme>'


if __name__ == "__main__":
    print(to_azure(" ".join(sys.argv[1:])))

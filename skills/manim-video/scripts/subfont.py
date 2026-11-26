#!/usr/bin/env python3
"""A subtitle font in which a % written after a subscript digit is a subscript
too: p₁%(n) is shown with the 1 and the % both in the index.

Unicode has subscript digits (₀…₉) but no subscript percent sign, and neither
SRT nor WebVTT can lower or shrink part of a line. So the subtitle text keeps
the plain "p₁%(n)" — readable in any player — and the font does the rest: a
contextual substitution (OpenType `calt`, which libass and browsers apply by
default) replaces % by a copy scaled like the font's own subscript digits,
whenever it follows one of them, or another such %.

    python3 subfont.py <out-dir> [--web subtitles.srt ...]
    python3 subfont.py --burnable in.srt out.srt

writes <out-dir>/SubtitleSans.ttf (family "Subtitle Sans", from DejaVu Sans)
and, with --web, SubtitleSans.woff2 cut down to the characters of the given
files plus Hebrew, Latin and punctuation, for a web page.

libass applies no contextual substitution, so for burning the subscript % is
written explicitly, at a private code point (U+E025) that only this font has:
burn a copy made by `--burnable`, never hand that copy to a viewer.

Burn subtitles with it:   subfont.py --burnable x.srt /tmp/x.srt
                          subtitles=/tmp/x.srt:fontsdir=<out-dir>:force_style='FontName=Subtitle Sans,...'
On a web page:            @font-face { font-family: "Subtitle Sans"; src: url(SubtitleSans.woff2); }
                          video::cue { font-family: "Subtitle Sans", sans-serif; }

Needs fontTools (and brotli for --web): the Manim venv has fontTools.
"""
import argparse, os, sys

BASE = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FAMILY = "Subtitle Sans"
FILE = "SubtitleSans"
SUBDIGITS = [0x2080 + i for i in range(10)]
# libass (burned-in subtitles) does not apply contextual substitutions, so the
# subscript % also gets a private code point, and burnable() writes it.
SUBPERCENT = 0xE025


def burnable(text):
    """The text with every % that follows a subscript digit (or such a %)
    replaced by SUBPERCENT: for burning with libass only, never for a file a
    viewer gets."""
    out = []
    for ch in text:
        if ch == "%" and out and (0x2080 <= ord(out[-1]) <= 0x2089 or ord(out[-1]) == SUBPERCENT):
            ch = chr(SUBPERCENT)
        out.append(ch)
    return "".join(out)


def build(out_dir, base=BASE):
    from fontTools.ttLib import TTFont
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.ttLib.tables import otTables as ot
    from fontTools.otlLib.builder import buildSingleSubstSubtable, buildLookup, buildCoverage

    font = TTFont(base)
    cmap = font.getBestCmap()
    glyf, hmtx = font["glyf"], font["hmtx"]
    digits = [cmap[c] for c in SUBDIGITS if c in cmap]

    # the scale of the font's subscript digits: "₁" against "1"
    one, sub_one = glyf[cmap[0x31]], glyf[cmap[0x2081]]
    s = (sub_one.yMax - sub_one.yMin) / (one.yMax - one.yMin)
    dy = sub_one.yMin - one.yMin * s

    pct = cmap[0x25]
    pen = TTGlyphPen(glyf)
    glyf[pct].draw(TransformPen(pen, (s, 0, 0, s, 0, dy)), glyf)
    new = pct + ".sub"
    glyf[new] = pen.glyph()
    adv, lsb = hmtx[pct]
    hmtx[new] = (round(adv * s), round(lsb * s))
    for table in font["cmap"].tables:
        if table.isUnicode():
            table.cmap[SUBPERCENT] = new
    order = font.getGlyphOrder()
    if new not in order:
        order = order + [new]
    font.setGlyphOrder(order)
    glyf.setGlyphOrder(order)

    # % -> %.sub after a subscript digit or a %.sub
    gsub = font["GSUB"].table
    lookups = gsub.LookupList.Lookup
    single = buildLookup([buildSingleSubstSubtable({pct: new})])
    lookups.append(single)
    single_index = len(lookups) - 1
    chain = ot.ChainContextSubst()
    chain.Format = 3
    chain.BacktrackGlyphCount = 1
    chain.BacktrackCoverage = [buildCoverage(digits + [new], font.getReverseGlyphMap())]
    chain.InputGlyphCount = 1
    chain.InputCoverage = [buildCoverage([pct], font.getReverseGlyphMap())]
    chain.LookAheadGlyphCount = 0
    chain.LookAheadCoverage = []
    rec = ot.SubstLookupRecord()
    rec.SequenceIndex, rec.LookupListIndex = 0, single_index
    chain.SubstCount, chain.SubstLookupRecord = 1, [rec]
    lookups.append(buildLookup([chain]))
    gsub.LookupList.LookupCount = len(lookups)

    feature = ot.Feature()
    feature.FeatureParams = None
    feature.LookupListIndex = [len(lookups) - 1]
    feature.LookupCount = 1
    record = ot.FeatureRecord()
    record.FeatureTag, record.Feature = "calt", feature
    records = gsub.FeatureList.FeatureRecord + [record]
    new_index = len(records) - 1
    # HarfBuzz finds a feature by binary search: the list must stay sorted by tag
    order = sorted(range(len(records)), key=lambda i: (records[i].FeatureTag, i))
    moved = {old: new for new, old in enumerate(order)}
    gsub.FeatureList.FeatureRecord = [records[i] for i in order]
    gsub.FeatureList.FeatureCount = len(records)
    for script in gsub.ScriptList.ScriptRecord:
        systems = [script.Script.DefaultLangSys] + [r.LangSys for r in script.Script.LangSysRecord]
        for ls in systems:
            if ls is None:
                continue
            ls.FeatureIndex = sorted(moved[i] for i in ls.FeatureIndex + [new_index])
            ls.FeatureCount = len(ls.FeatureIndex)
            if ls.ReqFeatureIndex != 0xFFFF:
                ls.ReqFeatureIndex = moved[ls.ReqFeatureIndex]

    for rec in font["name"].names:
        if rec.nameID in (1, 16):
            rec.string = FAMILY
        elif rec.nameID == 4:
            rec.string = FAMILY
        elif rec.nameID == 6:
            rec.string = FILE
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, FILE + ".ttf")
    font.save(path)
    return path


def web(ttf, out_dir, texts):
    from fontTools import subset
    chars = set("".join(texts))
    chars |= {chr(c) for c in range(0x20, 0x7F)} | {chr(c) for c in range(0x5D0, 0x5EB)}
    chars |= {chr(c) for c in SUBDIGITS} | set("–—…״׳⁦⁧⁨⁩‏‎")
    opts = subset.Options()
    opts.layout_features = ["*"]
    opts.flavor = "woff2"
    opts.name_IDs = ["*"]
    f = subset.load_font(ttf, opts)
    sub = subset.Subsetter(opts)
    sub.populate(text="".join(sorted(chars)))
    sub.subset(f)
    path = os.path.join(out_dir, FILE + ".woff2")
    subset.save_font(f, path, opts)
    return path


def main():
    if sys.argv[1:2] == ["--burnable"]:
        src, dst = sys.argv[2:4]
        open(dst, "w", encoding="utf-8").write(burnable(open(src, encoding="utf-8").read()))
        return
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("out_dir")
    ap.add_argument("--base", default=BASE)
    ap.add_argument("--web", nargs="*", default=None, help="subtitle files whose characters the web font keeps")
    a = ap.parse_args()
    ttf = build(a.out_dir, a.base)
    print("wrote", ttf)
    if a.web is not None:
        texts = [open(p, encoding="utf-8").read() for p in a.web]
        print("wrote", web(ttf, a.out_dir, texts))


if __name__ == "__main__":
    main()

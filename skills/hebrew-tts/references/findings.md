# What was found, and how

Each finding below came from a native speaker's complaint about Azure's
`he-IL-HilaNeural`, was tested with variants of the whole sentence, and was
kept when the speaker chose the fixed variant. In chronological order of the
mistakes, which is roughly the order in which they will be met again.

## 1. The he-IL phone set (Azure docs, "speech-ssml-phonetic-sets")

| IPA | as in | IPA | as in | IPA | as in |
|---|---|---|---|---|---|
| i | איש | p | פסקל | ʃ | שולחן |
| e | אש | b | בדס | x | חתול, אוכל |
| a | אף | t | טיפה | h | הולך |
| o | אות | d | דבר | t͡s | צדק |
| u | עוגה | k | כתב | m | מאוד |
| | | ɡ | גדול | n | נפש |
| | | ʔ | אביב, שיעור | l | לשון |
| | | f | פילטר | ʁ | ראשון |
| | | v | וילון | j | ילד |
| | | s | שמלה, כסף | ʒ | ז'אנר |
| | | z | זאב | tʃ | צ'יפס |
| | | | | dʒ | ג'ונגל |

Measured: the voice treats r/ʁ, x/χ, ts/t͡s, g/ɡ, e/ɛ, o/ɔ as the same sound
(identical audio), so a transcription is not fragile about these. A symbol
outside the set is not rejected; it produces some other sound. Check every
transcription against the table (`scripts/check_ipa.py`).

The table lists **no stress mark** for Hebrew (other languages have one).

## 2. Niqqud makes it worse

Full niqqud was the first attempt, on the theory that the engine misreads
because Hebrew is unpointed. It was worse:

- **kamatz katan** read as kamatz: כָּל → "kal";
- **dagesh** in a letter where modern Hebrew does not hear it (ג ד ת ט ק נ)
  makes the engine double the consonant: גַּם, דֵּי, תְּשׁוּבָה, הַקּוֹל came out
  40-100 ms longer than unpointed, and sounded odd ("as if a vowel was
  added"). Removing those dagesh helped that, but not the rest;
- the stress was still wrong (נסמן read "neSAmen"), and niqqud has no way to
  say where the stress is: a meteg was ignored, and an accent sign changed the
  sound unpredictably.

Partial niqqud (only ambiguous words) did not fix the stress either. Use IPA.

## 3. Where the stress mark goes

With IPA, the stress came out one syllable early everywhere — "Ashkenazi from
the first word" (ננסה as "neNAse"). Four spellings of נסמן in the same
sentence, judged by ear:

| ph | heard |
|---|---|
| plain text (no `<phoneme>`) | right, in that sentence |
| `nesamen` (no mark) | right |
| `nesameˈn` (mark after the stressed vowel) | right |
| `nesaˈmen` (standard IPA: mark before the syllable) | **wrong**: neSAmen |

So the voice attaches `ˈ` to the vowel **before** it. Keep standard IPA in
the lexicon (it is what a person reads) and convert when building the SSML:
`scripts/azure_stress.py`. After the conversion, "liskaˈla", "nesameˈn",
"hamispariˈm" are what the engine gets. A secondary stress `ˌ` is converted
the same way (the voice knows no `ˌ`).

## 4. Words that run together, or vanish

| complaint | cause | fix (chosen by ear) |
|---|---|---|
| "די קל לענות" read "די קלה לענות" | unstressed one-syllable word fuses with the next | stress mark on every one-syllable content word: `ˈkal`, `ˈtov`, `ˈkan`, `ˈrak`, `ˈɡraf`, `ˈloɡ` |
| "וכך הלאה" read as one word | x+h across the boundary | glottal stop at the start of the second: `ʔˈhalʔa` |
| "בסיס e": e swallowed | `basis i` → "basisi" | `ˈʔi` (glottal stop + stress), as a separate `<phoneme>` |
| the כ of כפונקציה almost unheard | unstressed prefix syllable reduced | secondary stress: `ˌkeˈfunktsja` (Azure: `keˈfuˈnktsja`) |
| a pause before a lone "n" at a sentence's end | unstressed one-syllable `<phoneme>` | stress mark on every one-syllable formula reading |
| "זה" mangled at the end of "נרוץ על כל המספרים בטווח זה," | an unstressed word ending a phrase | the SSML builder stresses the last word before punctuation or at the end of a cue (here 4 more words: זה, כך, כאן) |
| the same pause before "n" at the end of "p₁%(n)" ("pi axuz ʃel ʔen") | the unstressed letter name inside a longer reading | stress mark on **every** letter name and "log" in every reading (`ˈpi aˈxuz ʃel ˈʔen`); 3.15 s → 2.55 s |
| "מ-n" with a pause, like a comma | the hyphen; a space was no better | prefix + formula as one `<phoneme>`: `meˈʔen` |
| a pause before "e" like a comma | a `<break>` inserted to separate it | no break; glottal stop instead |

| רימן always "riMAN", whatever the stress mark | the engine's own reading of the name wins: the variant with the mark on "ri" was the same audio as plain text | two adjacent `<phoneme>`s, no space: `riˈ` + `man` |

Before playing variants, check they differ from each other and from plain
text (decode both, compare samples): five of nine "different" spellings of
רימן came out the same audio.

Variants that were judged worse: a short `<break>` between words (heard as a
comma); spelling the letter as Hebrew text (`<sub alias="אִי">`); a glottal
stop after the word instead of before the next.

## 5. Pronunciations that were wrong in the transcription itself

The engine said what it was told; the transcription was wrong:

- **טווח** is `tvax`, not the segolate `tevax`; and **בטווח** `beˈtvax`, not
  `baˈtvax` (the definite form is grammatical before הזה, but nobody says it).
  The same for באחוזים נמוכים: indefinite, `be-`.
- **הפעיל, past, 3rd plural and 3rd feminine**: penult stress — `vehoˈxixu`,
  `himˈt͡siʔu`, `ʃehoˈvila`. Easy to get wrong by analogy with פיעל
  (`ʃiʔaˈru`, final stress).
- **סְכוּם** (a sum) `sxum`, with x; the verb לִסְכֹּם `lisˈkom`, with k.
- **מלמעלה ומלמטה**: `mileˈmala umileˈmata` (spoken), not `milˈmala`.
- **ויכולה**: `vixoˈla`, not `vijxoˈla`.
- **מהפכנית**: spoken `mahapxaˈnit`, not the grammar book's `mahpexaˈnit`.
- **Names**: ask how a name is said; do not assume the original language's
  stress, nor the Hebrew default. רימן is RI-man, and the engine needed the
  split of §4 to say it.
- final ע is not a glottal stop: מידע `meˈda`.
- **ונסה** in a text that means "we will try" is a typo for וננסה; fix the
  text, not the reading.

## 6. Voices

- `he-IL-HilaNeural` and `he-IL-AvriNeural` honour IPA; the user chose Hila.
- `he-IL-Hila:DragonLatestNeural` (HD): better from plain text, but with IPA
  it slid into a strong American accent mid-sentence ("בקירוב טוב מאוד" and on),
  and dropped vowels (במקום without its i). Plain text cannot be corrected word
  by word, so HD was dropped.
- The English voices (`en-US-AndrewMultilingualNeural`, `en-US-AvaMultilingual
  Neural`) need nothing of this; `<sub alias>` for formulas is enough.

## 7. Synthesis

- One request per sentence (the `<s>` of the SSML, marks and comments
  removed), placed at the start of the sentence's first cue with ffmpeg
  `adelay`, mixed, loudness-normalised (-16 LUFS, -1.5 dBTP), padded to the
  scene's length (`apad` — without it `-shortest` cut the scene at the last
  word and the whole video came out 20 s short).
- Azure adds ~0.9 s of silence after a sentence; when checking that a sentence
  ends before the next starts, measure where the speech ends, not the file.
- The F0 tier answers 429 to bursts; wait (Retry-After, or 10 s, 20 s, ...)
  and retry. An interrupted run must not leave an empty audio file in the
  cache (write to a temporary name, then rename).

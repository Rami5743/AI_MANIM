---
name: hebrew-tts
description: >-
  Make a speech engine read Hebrew correctly: narration for a video, a
  voice-over, an audio version of a text. Writes every Hebrew word in IPA with
  its stress for Azure text to speech (the he-IL voices Hila and Avri), lays
  each sentence at its subtitle's time, and fixes mispronunciations one word at
  a time with the user's ear as the judge. Use when the user asks for הקראה,
  קריינות, קול, הקראת AI, text to speech, TTS, SSML, Azure Speech, or narration
  in Hebrew, or complains that the reading is wrong: הטעמה שגויה, ניקוד שגוי,
  נשמע אשכנזי, מבטא אמריקאי, מילה נבלעת, שתי מילים נקראות כמילה אחת, הפסקה לא
  במקום.
---

# Hebrew text to speech

Speech engines misread unpointed Hebrew, and **niqqud does not fix it**: the
engine reads a kamatz katan as a kamatz (כָּל came out "kal"), and doubles a
consonant under a dagesh it does not need (גַּם, דֵּי, תְּשׁוּבָה came out long and
odd). What works is to take the reading out of the engine's hands: every
Hebrew word as `<phoneme alphabet="ipa" ph="...">word</phoneme>`, with its
stress marked, and the text inside left as it is (unpointed).

Everything below was found with Azure's `he-IL-HilaNeural`, one finding per
complaint of a native speaker, and kept only when the speaker heard it fixed.
`references/findings.md` has each finding with its evidence;
`references/lexicon.md` the words whose reading was settled by ear.

## The method

1. **Write every word in IPA** (`references/findings.md` §1 has the he-IL
   phone set: five vowels a e i o u, and p b t d k ɡ ʔ f v s z ʃ x h t͡s m n l
   ʁ j ʒ tʃ dʒ). Standard notation in the source: `ˈ` before the stressed
   syllable, `ˌ` before a secondary stress. Modern spoken Hebrew, not the
   grammar book: טווח is `tvax`, כמו `kmo`, צריכים `t͡sriˈxim`;
   but בדיוק `bediˈjuk`. Check the pattern stress: הפעיל in the past is stressed
   on the penult (`hoˈvila`, `vehoˈxixu`, `himˈt͡siʔu`); a noun and a verb
   spelled alike differ (סכום `sxum`). The article is heard or not by the
   phrase: "בטווח הזה" `baˈtvax`, but "בטווח זה" `beˈtvax`; "כשלראשוני p"
   (any prime) `keʃeleriʃoˈni`. Ask when unsure; the user hears it at once.

2. **Convert the stress for Azure** with `scripts/azure_stress.py`: Azure's
   Hebrew voices read a `ˈ` as marking **the vowel before it**, so every mark
   moves to just after the vowel of its syllable (`nesaˈmen` → `nesameˈn`).
   Written the standard way, the stress lands one syllable early, and the
   whole text sounds Ashkenazi.

3. **Mark what the engine otherwise runs together** (all heard, all fixed):
   - a one-syllable content word gets a stress mark (`ˈkal`, `ˈtov`, `ˈkan`):
     unmarked, "די קל לענות" came out "די קלה לענות". Function words (של, את,
     זה, לא) stay unmarked;
   - a Latin letter is read by its name, and a name that begins with a vowel
     begins with a glottal stop: e `ˈʔi`, n `ˈʔen`, a `ˈʔej`, r `ʔar` — without
     it "בסיס e" ran into "basisi". p is `ˈpi`. **Every** letter name carries
     its stress mark, also inside a longer formula reading ("pi axuz ʃel
     ˈʔen"): an unstressed "en" at the end of a formula made the engine pause
     0.6 s before it, twice, in different scenes;
   - a word that fuses with the one before gets a glottal stop at its start:
     "וכך הלאה" → `ʔˈhalʔa`;
   - a short unstressed prefix that disappears gets a secondary stress:
     כפונקציה `ˌkeˈfunktsja`;
   - a word whose stress the engine keeps wrong whatever the IPA says
     (רימן: every mark came out "riMAN"; check that a variant differs from
     plain text before playing it) is said as two adjacent `<phoneme>`s with
     no space: `<phoneme ph="riˈ">רי</phoneme><phoneme ph="man">מן</phoneme>`;
   - **the last word of a phrase** (before punctuation, or the last of a cue)
     gets a stress mark if it has none: unstressed, "זה" at the end of
     "בטווח זה," came out wrong. Do it in the SSML builder, for every word,
     not in the lexicon;
   - a Hebrew prefix joined to a formula by a hyphen ("מ-n", "ב-p₁%(n)") makes
     one `<phoneme>` with it, stress on the formula, a glottal stop between two
     vowels: `meˈʔen`. The hyphen made the engine pause; so did a space.

4. **Synthesize one sentence per request** (`scripts/synth.py`), and lay each
   at the start of its first subtitle. The engine's pace then never drifts
   from the picture. Cache each sentence by its text and voice, so that fixing
   one word costs one sentence. The free tier (F0) answers 429 when asked too
   often: wait and try again.

5. **Let the user judge, and make judging cheap** (`scripts/ab.py`): when a
   word is wrong, synthesize **the whole sentence** in 2-4 variants, labelled
   A, B, C, and ask which is right. Never a fragment: a cut sentence confuses
   the engine and the listener. Do not argue with what the user hears; you
   cannot hear. Each answer goes into the lexicon and, if it is a pattern, into
   the rules above.

## The voice

The HD voice (`he-IL-Hila:DragonLatestNeural`) with IPA sounds better — the
user preferred its tone — but it fails more: once it slid into an American
accent for a whole sentence, and it reads some words differently from the
standard voice from the same IPA (עכשיו as `ˈaxʃav` came out wrong; `axˈʃav`
right). So: HD by default, with a **per-sentence fallback** to
`he-IL-HilaNeural` (a list of sentences, keyed by their first cue).

The user's rule for choosing, settled after many rounds:
- when a sentence is wrong and the transcription shows **a clear cause**
  (a wrong vowel, a missing syllable, a stress mark in the wrong place),
  fix the IPA and keep HD;
- when there is **no clear cause**, do not offer variants: move the sentence
  to the standard voice at once, and send the user just that sentence;
- a sentence already moved stays moved.

In the PNT video 11 of about 90 sentences ended on the standard voice:
an accent drift, a dropped e, ולז'נדר, במקום (its i dropped), ההרמוני
(stress), לסכום, "גם כך אנחנו עובדים בערך", and "מה שאומר" (מה misread).

**Switching voices re-opens everything settled with the other one.** After
the switch to HD, words the user had approved (e, עכשיו) came out wrong
again, and the user had to find them. Before reporting a switch done, list
every sentence whose reading was settled by ear (the lexicon), render them
in the new voice, and send them in one file (below) for one listening.

## English

`en-US-Andrew:DragonHDLatestNeural` (Andrew, HD) — the user's choice among
seven (Andrew, Ava, Emma, Brian; HD, HD Omni, HD V3, standard). English needs
none of the Hebrew machinery: plain text, formulas as `<sub alias>`, the HD
voice without fallbacks. Two things carry over: one request per sentence at
its cue, and the dead-air trim — English is read at 71% of the subtitle time,
so it leaves long pauses (up to 5 s) unless trimmed (manim-video,
`scripts/trim.py`). (The HD Omni voice of Brian ran sentences into the next
cue; check the overlap report of `scripts/synth.py`.)

## Working with the user

- **Check yourself before asking.** The user will not listen to the whole
  video again and again. After any change, find the places that could have
  broken (the lexicon, the fallback list, sentences that changed) and give
  the user **one file**: each sentence after a short beep, with a numbered
  table of start times and what to listen for. Ask only about what you
  cannot check.
- **Variants: few, whole sentences, verified distinct** (decode and compare;
  several "different" spellings come out as the same audio), labelled A, B,
  C, in one file with times. Not variants for what the rules above decide.
- **Never leave a request unanswered**, even one asked mid-task or one the
  user did not follow up: a link asked for, a question left open (an answer
  given inside a long message is easily missed: repeat it short).

## Measuring without ears

You cannot hear the result, but you can measure it (`scripts/ab.py` prints
each variant's speech length). A swallowed sound shortens the sentence, an
unwanted pause or an extra vowel lengthens it: "בסיס e" was 0.1 s longer than
"בסיס" alone when e was swallowed, 0.3 s when it was said. Use this to choose
which variants to play to the user, never instead of the user. (Two syntheses
of the same input are not byte-identical, so equality tests prove nothing.)

## Setup

- **Key:** in a cloud session, ask for it with the credential form for the
  host `<region>.tts.speech.microsoft.com`, header `Ocp-Apim-Subscription-Key`
  (no prefix); the proxy adds it, and the scripts send a placeholder.
  Elsewhere, `AZURE_SPEECH_KEY`. Never take a key in chat.
- **Region:** `scripts/*.py --region westeurope` (the resource's region).
- **Docs:** the he-IL phone set is on learn.microsoft.com,
  "speech-ssml-phonetic-sets"; it lists no stress mark for Hebrew, which is
  why step 2 was found by ear.
- **Credit:** the Azure portal's Cost Management, or
  microsoftazuresponsorships.com/Balance for a trial account; characters
  spoken are the speech resource's metric "Synthesized Characters".

## With manim-video

The manim-video skill cuts the narration into timed cues (`timing.json`) and
writes `readings.py` (how each formula is read). This skill adds the IPA of
each cue and of each reading, builds the SSML (one `<s>` per sentence, a
`<mark>` per cue), and `scripts/synth.py` writes each scene's narration as an
audio file as long as the scene, to be put under its video. The subtitles
never carry the IPA or any niqqud.

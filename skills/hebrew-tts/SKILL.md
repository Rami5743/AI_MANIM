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
   grammar book: טווח is `tvax`, בטווח `beˈtvax`, כמו `kmo`, צריכים `t͡sriˈxim`;
   but בדיוק `bediˈjuk`. Check the pattern stress: הפעיל in the past is stressed
   on the penult (`hoˈvila`, `vehoˈxixu`, `himˈt͡siʔu`); a noun and a verb
   spelled alike differ (סְכוּם `sxum`, לִסְכֹּם `lisˈkom`).

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
     it "בסיס e" ran into "basisi". p is `ˈpi`;
   - a word that fuses with the one before gets a glottal stop at its start:
     "וכך הלאה" → `ʔˈhalʔa`;
   - a short unstressed prefix that disappears gets a secondary stress:
     כפונקציה `ˌkeˈfunktsja`;
   - a word whose stress the engine keeps wrong whatever the IPA says
     (רימן: every mark came out "riMAN"; check that a variant differs from
     plain text before playing it) is said as two adjacent `<phoneme>`s with
     no space: `<phoneme ph="riˈ">רי</phoneme><phoneme ph="man">מן</phoneme>`;
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

`he-IL-HilaNeural` (or `he-IL-AvriNeural`) with IPA. The HD voice
(`he-IL-Hila:DragonLatestNeural`) reads plain text more fluently, but with IPA
it drifted into a heavy American accent mid-sentence, and plain text cannot be
corrected. Use HD only for text with no IPA at all, and only if the user
prefers it.

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

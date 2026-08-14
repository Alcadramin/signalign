# Baseline: speech wav2vec2 + gold lyrics forced alignment

- **Model:** torchaudio WAV2VEC2_ASR_BASE_960H (speech-only, English chars)
- **Pipeline:** Demucs htdemucs vocal stem → CTC forced alignment of gold
  lyric text (`scripts/run_bench.py`)
- **Gold:** JamendoLyrics 79 tracks, difficulty buckets hand-assigned by ear
  (buckets.csv, annotator: alca, 2026-08-14)
- **Commit:** run at `8736027`, scored with `eval/score.py`
- **Raw:** `wav2vec2_base_gold_lyrics.json`

| bucket | words | MAE ms | MedAE ms | PCO@100 | PCO@200 | PCO@300 |
|---|---|---|---|---|---|---|
| buried | 3181 | 149 | 48 | 77.9% | 91.3% | 94.8% |
| clean | 11257 | 134 | 39 | 78.8% | 91.3% | 94.5% |
| held | 951 | 66 | 32 | 88.0% | 96.7% | 97.7% |
| melisma | 1270 | 117 | 54 | 74.0% | 91.3% | 95.0% |
| rap | 4921 | 214 | 42 | 82.9% | 93.1% | 94.9% |
| **all** | 21580 | 150 | 41 | 79.7% | 91.9% | 94.8% |

## Reading

- Medians are healthy everywhere (32–54ms); the buckets differ in their
  **tails**. Rap has the worst MAE (214ms — catastrophic misses on dense
  passages) while keeping a fine median. Melisma has the worst PCO@100
  (74% — onsets systematically smeared, not catastrophically lost).
- Held is the *easiest* bucket for a speech model, not the hardest —
  long stable vowels give CTC plenty of signal.
- Coverage is 1.00 by construction in forced mode (every lyric word gets a
  span); coverage only discriminates in ASR-transcript mode.

## Per-language (same run, `--group-by language`)

| language | words | MAE ms | MedAE ms | PCO@100 |
|---|---|---|---|---|
| English | 5693 | 292 | 68 | 68.2% |
| French | 5461 | 126 | 29 | 81.2% |
| German | 5157 | 90 | 43 | 84.5% |
| Spanish | 5269 | 81 | 29 | 86.1% |

Counterintuitive: English worst despite the English char vocabulary. Driver
is a handful of catastrophic tracks, not a uniform shift — worst offenders
(Pure_Mids 1029ms, Tom_Orlando 953ms, Ridgway 860ms, Avercage 659ms) are all
English. Root cause uninvestigated (candidates: long instrumental sections
derailing global CTC alignment, production density). Bucket mix per language
is roughly even, so buckets don't explain it.

## Zoo row 2: WhisperX medium (ASR path — no lyrics input possible)

Run: `uvx whisperx --model medium --compute_type int8` per track, auto
language detect (one failure: German rap misdetected as Khmer, rerun with
`--language de`). Raw: `whisperx_medium.json`.

| bucket | words | cov | MAE ms | MedAE ms | PCO@100 | PCO@300 |
|---|---|---|---|---|---|---|
| buried | 3181 | 0.48 | 1847 | 72 | 28.1% | 34.7% |
| clean | 11257 | 0.56 | 2480 | 55 | 39.1% | 47.6% |
| held | 951 | 0.68 | 855 | 57 | 43.7% | 57.2% |
| melisma | 1270 | 0.61 | 1637 | 74 | 38.5% | 49.7% |
| rap | 4921 | 0.58 | 2171 | 42 | 44.4% | 48.5% |
| **all** | 21580 | **0.56** | **2187** | **54** | **38.9%** | **46.5%** |

Reading: WhisperX drops 44% of sung words and misplaces entire segments by
seconds (Whisper hallucinations on music — e.g. Amara.org subtitle credits
transcribed into a song). Local timing of found words is fine (54ms MedAE).
The failure mode is transcription + segment placement, not frame precision.
Whisper language ID is also unreliable on singing (Khmer misdetection).

This is the project's core gap, quantified: lyrics-informed alignment
(150ms MAE, 100% coverage) vs the best available ASR-path tool (2187ms,
56% coverage) on identical audio and gold.

## Caveats

- Non-English tracks (~half the set) are aligned with an English char
  vocabulary after ASCII folding — works, but likely inflates errors in
  FR/DE/ES; per-language breakdown TODO.
- Numbers are near published SOTA (DAFx25: 216ms MAE / 41ms MedAE), but
  protocols differ (segmentation, tie-breaking, language handling). Do NOT
  claim parity publicly before a same-protocol comparison.

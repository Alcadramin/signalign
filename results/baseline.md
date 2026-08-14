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

## Caveats

- Non-English tracks (~half the set) are aligned with an English char
  vocabulary after ASCII folding — works, but likely inflates errors in
  FR/DE/ES; per-language breakdown TODO.
- Numbers are near published SOTA (DAFx25: 216ms MAE / 41ms MedAE), but
  protocols differ (segmentation, tie-breaking, language handling). Do NOT
  claim parity publicly before a same-protocol comparison.

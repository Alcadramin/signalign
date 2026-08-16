# Gate calibration: alignment_score threshold vs actual onset error

Method: factory over all 79 bench tracks (correct lyrics supplied), 1250
segments joined to gold via LCS word matching; per-segment median onset
error vs the segment's mean CTC posterior (`alignment_score`). Sweep in
`gate_calibration.json`; commit `9f63125`, scored against bucketed gold.

## Headline

**CTC score is a weak predictor of onset error when lyrics are correct.**
Ungated, 88% of segments are already ≤100ms median error (42ms overall
median). Score-gating trades data for almost no precision:

| min_score | kept | median err | ≤100ms |
|---|---|---|---|
| 0.00 | 100% | 42ms | 88.3% |
| **0.15** | **93%** | **40ms** | **90.5%** |
| 0.30 | 56% | 41ms | 89.9% |
| 0.50 | 13% | 51ms | 87.4% |

Chosen default: **min_score = 0.15** (elbow — everything past it discards
data without improving quality; 0.5 was strictly worse on both axes).

## Per-bucket notes

- **rap**: score-gating works unusually well — at 0.3, 99% of kept segments
  ≤100ms. But overall rap segments are fine anyway (87% ungated).
- **buried / held**: score punishes these buckets brutally (0.3 keeps only
  19% / 60%) with no error improvement — low CTC confidence reflects
  acoustics, not misalignment. Do NOT raise the global threshold; it
  disproportionately deletes exactly the hard-case data the corpus wants.
- **melisma**: worst ungated bucket (84% ≤100ms) and score doesn't separate
  good from bad within it.

## Implication for the factory

With *verified* lyrics, the score gate is a light trash filter, not a
quality ranking — `cer_vs_lyrics` (wrong/partial lyrics detection) is the
load-bearing gate. Unverified-lyrics sources will need recalibration;
this table is the method to do it.

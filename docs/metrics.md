# Metrics

`eval/score.py` is the single source of truth for these. All numbers are
reported **per difficulty bucket** (see docs/schema.md) plus an overall row —
the buckets are the point.

## Word-level onset metrics

Words are matched between prediction and gold by position within the segment
(same lyrics, same order). For each matched word, onset error is
`|pred_start − gold_start|`.

- **Mean Absolute Onset Error (ms)** — mean onset error over all words.
- **Median Absolute Onset Error (ms)** — median of the same; robust to
  catastrophic misses that wreck the mean.
- **PCO@τ (Percentage of Correct Onsets)** — fraction of words with onset
  error < τ, at τ ∈ {100, 200, 300} ms.

## Reporting

- Baseline row = unmodified speech wav2vec2 CTC aligner (Phase 0 stack).
- Every model row is a delta against the baseline.
- Every row in `results/` carries the commit hash + config that produced it.

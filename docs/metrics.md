# Metrics

`eval/score.py` is the single source of truth for these. All numbers are
reported **per difficulty bucket** (see docs/schema.md) plus an overall row —
the buckets are the point.

## Matching policy

Segments are matched by `id`. Within a segment, predicted words are matched
to gold words by longest-common-subsequence over normalized text (lowercase,
alphanumerics + apostrophe only) — this tolerates ASR insertions/deletions
and punctuation drift. A gold word with no match is a **miss**.

## Word-level onset metrics

For each matched word, onset error is `|pred_start − gold_start|`.

- **Coverage** — matched gold words / all gold words. Reported per bucket;
  misses are a real failure mode (Whisper drops ~30% of words on fast rap).
- **Mean Absolute Onset Error (ms)** — mean onset error over *matched* words.
- **Median Absolute Onset Error (ms)** — median of the same; robust to
  catastrophic misses that wreck the mean.
- **PCO@τ (Percentage of Correct Onsets)** — words with onset error < τ,
  at τ ∈ {100, 200, 300} ms, **divided by all gold words** — a missed word
  counts as an incorrect onset. Strict by design.

## Reporting

- Baseline row = unmodified speech wav2vec2 CTC aligner (Phase 0 stack).
- Every model row is a delta against the baseline.
- Every row in `results/` carries the commit hash + config that produced it.

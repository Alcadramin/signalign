# Evaluation protocol

`score.py` is the single source of truth for metrics (spec: `docs/metrics.md`).

## Score a prediction

```bash
uv run eval/score.py --pred predictions.jsonl --gold gold.jsonl [--json out.json]
```

Both files use the schema in `docs/schema.md`. Output: one row per difficulty
bucket plus `all` — coverage, MAE, MedAE (ms, matched words), PCO@{100,200,300}ms
(denominator = all gold words; misses count against you).

## Build the gold manifest

```bash
uv run scripts/ingest_jamendolyrics.py            # -> data/bench/jamendolyrics.jsonl
```

Requires the JamendoLyrics dataset at `data/jamendolyrics`
(`hf download jamendolyrics/jamendolyrics --repo-type dataset --local-dir data/jamendolyrics`).

Difficulty buckets in the gold manifest are `null` until assigned by a human
by ear — never machine-assigned. Bucketed and hand-corrected additions land
as separate manifests in `data/bench/`.

## Reference numbers (Phase 0 baseline, one rap track)

Demucs → Whisper medium (ASR transcript, no lyrics input) → wav2vec2 CTC:
coverage 0.51, MAE 450ms, MedAE 67ms, PCO@100 39%. Timing on matched words
is workable; word coverage is the dominant failure on rap.

## Tests

```bash
uv run pytest eval/ scripts/
```

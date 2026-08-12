# signalign — plan (rev 2, 2026-08-12)

## Pivot

Alignment *methods* are crowded (DAFx25 SOTA: 216ms MAE / 41ms MedAE on
JamendoLyrics). The empty, citable lanes are **artifacts**:

1. **signalign-bench** — the first difficulty-bucketed word-level alignment
   benchmark for singing (rap / melisma / held / buried / clean). Nothing
   like it exists; every future paper needs it.
2. **signalign-corpus** — a large, openly licensed, redistributable aligned
   singing corpus for music-gen training. DALI can't ship audio; gen-model
   teams (ACE-Step, DiffRhythm) hand-roll hacks because this doesn't exist.

The aligner tool remains as supporting infrastructure, not the product.
A fine-tuned model is an optional later accelerant, not a goal.

## Evidence base (Phase 0 findings)

- Baseline (Demucs → Whisper medium → wav2vec2 CTC) on fast rap: onsets
  ~60–100ms off where words exist, but Whisper dropped 32% of words
  (395/581). Coverage, not timing, is the first bottleneck when lyrics
  aren't fed in. True forced alignment must consume provided lyrics.

## Phases

### P1 — Benchmark v0.1 (load-bearing)
- `eval/score.py` per docs/metrics.md (MAE, MedAE, PCO@{100,200,300}ms,
  per bucket), unit-tested.
- Ingest JamendoLyrics gold (79 songs, word onsets already hand-made) into
  the schema. Segment long tracks.
- **Human:** assign difficulty buckets by ear; add hard-case tracks the
  field lacks (dense rap pellas from ccMixter, metal/buried, heavy melisma),
  hand-correct their onsets.
- Baseline zoo: score WhisperX, raw wav2vec2 (ours), MFA if feasible —
  publish per-bucket results table.
- Ship: HF dataset `signalign-bench` + results in `results/`. Citable
  immediately.

### P2 — Corpus factory
- `pipeline/`: folder → Demucs → VAD → lyrics-informed forced alignment
  (lyrics in, not ASR-only) → confidence gate → schema manifests.
- Gate thresholds calibrated against signalign-bench buckets (report
  precision of the gate per bucket — this is the quality story).
- Sources: **CC-BY / CC-BY-SA only** for redistribution (MTG-Jamendo CC
  subset, ccMixter, FMA). NC/ND tracks may appear in the benchmark
  (evaluation use) but NEVER in the corpus.
- Ship: HF dataset `signalign-corpus` v0.1 with per-track license
  provenance + dataset card.

### P3 (optional) — Quality accelerant
- Fine-tune wav2vec2 CTC on corpus keep-pile → better factory emissions →
  corpus v2; measure on bench.
- Upstream option: singing alignment model as a WhisperX "singing mode"
  PR + HF weights. Distribution without brand-building.

### P4 — Leaderboard + community
- HF Space: leaderboard over signalign-bench + submission protocol.
- Contribution guide centered on hand-correcting tracks (non-coders own
  real work).
- Tech report (arXiv) describing bench + corpus + baseline zoo.

## Guardrails (unchanged)

Human-only: bucket assignment, hand-correction, listening judgments.
Never machine-generate benchmark ground truth. Never relicense NC/ND into
the corpus. eval/score.py is the single metrics authority.

## Licensing map

| Artifact | Contents | License handling |
|---|---|---|
| signalign-bench | audio + gold onsets | per-track CC incl. NC/ND (eval use), licenses in manifest |
| signalign-corpus | audio + machine alignments | CC-BY / CC-BY-SA only, redistributable |
| code | everything in repo | Apache-2.0 |

# Dataset factory

Turns a folder of songs (plus optional lyrics) into schema-valid, confidence-
gated aligned segments.

```bash
uv run python pipeline/run.py --config my.toml
```

## Config (TOML)

```toml
[input]
audio_dir = "path/to/songs"        # wav/mp3/flac/ogg
lyrics_dir = "path/to/lyrics"      # optional; <track-stem>.txt per song
licenses_csv = "tracks.csv"        # optional; per-track license (id,license columns)
source = "mysource"                # provenance tag written to every record
license = "CC-BY-4.0"              # fallback license when no per-track entry

[output]
dir = "out/factory/mysource"

[vad]                              # defaults shown
min_gap = 0.5                      # merge VAD spans closer than this (s)
min_len = 1.0                      # drop segments shorter than this (s)
max_len = 30.0                     # split segments longer than this (s)

[gate]
min_score = 0.15                   # min mean CTC score per segment (calibrated, results/gate_calibration.md)
max_cer = 0.3                      # max CER(ASR, lyrics) per track

[asr]
enabled = true                     # ASR pass for CER check when lyrics exist
model = "medium"                   # faster-whisper size
```

## Stages (independently importable)

1. `separate.Separator` — Demucs htdemucs → vocal stem (cached)
2. `align.Aligner` — CTC forced alignment of lyrics over the whole track,
   per-word posterior scores kept. No lyrics → ASR transcript is aligned
   instead (lower trust; CER gate can't run)
3. `segment.vad_spans` + `merge_spans` — Silero-VAD, gap-merged and capped
4. `segment.slice_words` — words assigned to spans by midpoint, times
   rebased to segment start
5. `gate.route` — `keep` vs `hard` per segment; clips + stem clips written
   under the output dir; records appended to `keep.jsonl` / `hard.jsonl`

Resume: rerun the same config; tracks already present in the output
manifests are skipped.

## Trust model

- `alignment_score` = mean CTC posterior over the segment's words — how
  confident the aligner was
- `cer_vs_lyrics` = whole-track CER between ASR and provided lyrics — did
  the lyrics actually match the audio (catches wrong-lyrics files)
- Gate thresholds are calibrated against signalign-bench (see results/)

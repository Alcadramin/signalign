# signalign

**An open, actually-usable word-level aligner for *sung* vocals** — the piece open
music-generation models (ACE-Step, DiffRhythm, etc.) are missing, because speech
aligners break on singing: held notes, melisma, fast rap, buried vocals.

Narrow tool, built for the open ecosystem to build on. Not a Suno competitor.

## Status

Early. Phase 0: baseline exploration (Demucs → Whisper → wav2vec2 forced
alignment) to map exactly where speech aligners drift on singing.

## Quickstart (baseline explorer)

```bash
pip install -r requirements.txt
python scripts/explore.py --audio path/to/song.wav
```

Emits word-level timings as JSONL per [`docs/schema.md`](docs/schema.md).

## Roadmap

- [x] **Phase 0** — baseline stack end to end; map failure modes
- [ ] **Phase 1** — hand-corrected golden eval set + scoring harness (`signalign-eval`)
- [ ] **Phase 2** — dataset factory with confidence gating (`signalign-train`)
- [ ] **Phase 3** — fine-tune wav2vec2 CTC on sung vocals, beat the baseline (`signalign-w2v-sung`)
- [ ] **Phase 4** — pip package, Gradio demo Space, integrations, community

## Layout

```
scripts/    one-off exploration
pipeline/   the dataset factory (stages + CLI)
eval/       scoring harness + protocol
train/      fine-tuning code + configs
inference/  align(audio, lyrics) -> word timings
results/    eval numbers vs baseline, per difficulty bucket
docs/       schema.md, metrics.md, pipeline.md
```

## License

Code: [Apache-2.0](LICENSE). Datasets keep their source licenses — see the
dataset cards.

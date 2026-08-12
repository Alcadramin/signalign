# signalign

**The missing evaluation + data infrastructure for sung-vocal alignment.**

Two artifacts the field doesn't have:

- **signalign-bench** — the first difficulty-bucketed word-level alignment
  benchmark for singing (rap / melisma / held notes / buried vocals / clean)
- **signalign-corpus** — a large, openly licensed, *redistributable* aligned
  singing corpus for training open music-generation models

Plus the aligner pipeline that produces the corpus. Speech aligners drift on
singing; gen-model teams hand-roll alignment hacks because no shared benchmark
or open corpus exists. This fixes the infrastructure, not just the tool.

## Status

Early. Phase 0 done: baseline (Demucs → Whisper → wav2vec2 forced alignment)
runs end to end; on fast rap it drops 32% of words — see
[docs/plan.md](docs/plan.md) for the full plan and findings.

## Quickstart (baseline explorer)

```bash
uv sync
uv run scripts/explore.py --audio path/to/song.wav
```

Emits word-level timings as JSONL per [`docs/schema.md`](docs/schema.md).

## Roadmap

- [x] **Phase 0** — baseline stack end to end; map failure modes
- [ ] **Phase 1** — `signalign-bench`: bucketed benchmark + scoring harness + baseline zoo
- [ ] **Phase 2** — `signalign-corpus`: factory with license-clean sources + calibrated confidence gate
- [ ] **Phase 3** — (optional) fine-tune for factory quality; WhisperX upstream
- [ ] **Phase 4** — HF leaderboard Space, contribution paths, tech report

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

# Data schema

All alignment I/O — eval gold, pipeline output, inference output — uses this
JSONL format: one JSON object per line, one object per audio segment. No
alternate formats.

## Segment object

```json
{
  "id": "jamendo_00123_seg04",
  "audio_path": "clips/jamendo_00123_seg04.wav",
  "vocal_stem_path": "stems/jamendo_00123_seg04.wav",
  "duration": 12.34,
  "words": [
    {"text": "hello", "start": 1.23, "end": 1.45},
    {"text": "world", "start": 1.52, "end": 1.98}
  ],
  "difficulty": "melisma",
  "asr_confidence": 0.87,
  "cer_vs_lyrics": 0.04,
  "source": "jamendolyrics",
  "license": "CC-BY-SA-3.0"
}
```

## Fields

| Field | Type | Required | Meaning |
|---|---|---|---|
| `id` | string | yes | Unique segment id: `<source>_<track>_<segNN>` |
| `audio_path` | string | yes | Path to the mix clip, relative to the manifest |
| `vocal_stem_path` | string \| null | no | Path to the separated vocal stem, if any |
| `duration` | float | yes | Segment duration in seconds |
| `words` | array | yes | Word timings, ordered by `start` |
| `words[].text` | string | yes | The word as written in the lyrics |
| `words[].start` | float | yes | Word onset in seconds, relative to segment start |
| `words[].end` | float | yes | Word offset in seconds, relative to segment start |
| `words[].score` | float | no | Mean CTC posterior for the word's tokens (factory output) |
| `alignment_score` | float \| null | no | Mean of word scores over the segment |
| `language` | string \| null | no | Track language when known |
| `difficulty` | string \| null | no | Human-assigned bucket; see below. `null` until assigned |
| `asr_confidence` | float \| null | no | Mean ASR confidence over the segment, 0–1 |
| `cer_vs_lyrics` | float \| null | no | Character error rate of ASR vs reference lyrics |
| `source` | string | yes | Dataset/provenance tag (`jamendolyrics`, `local`, …) |
| `license` | string | yes | License of the underlying audio (`unknown` if unclear) |

## Difficulty buckets

Assigned **by a human, by ear** — never machine-assigned:

- `clean` — clear vocal, moderate tempo, plain delivery
- `held` — long sustained notes
- `melisma` — multiple pitches per syllable
- `rap` — fast, dense delivery
- `buried` — vocal low in the mix / heavy accompaniment bleed

## Trust levels

Same schema everywhere; only trust differs:

- **eval gold** (`signalign-eval`): `words` hand-corrected by a human, `difficulty` set
- **train** (`signalign-train`): `words` pipeline-generated, gated by confidence
- **inference output**: `words` predicted; provenance fields may be `null`

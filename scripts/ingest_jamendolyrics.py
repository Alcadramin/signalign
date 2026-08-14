import argparse
import csv
import json
from pathlib import Path

import soundfile


def track_duration(audio_path: Path, fallback: float) -> float:
    try:
        return round(soundfile.info(str(audio_path)).duration, 3)
    except Exception:
        return fallback


def load_annotations(ann_path: Path) -> list[tuple[float, float]]:
    with open(ann_path) as f:
        return [
            (float(row["word_start"]), float(row["word_end"]))
            for row in csv.DictReader(f)
        ]


def ingest_track(dataset_dir: Path, meta: dict) -> dict | None:
    stem = Path(meta["Filepath"]).stem
    lyrics_path = dataset_dir / "lyrics" / f"{stem}.txt"
    ann_path = dataset_dir / "annotations" / "words" / f"{stem}.csv"
    if not lyrics_path.exists() or not ann_path.exists():
        return None

    lyric_words = lyrics_path.read_text().split()
    timings = load_annotations(ann_path)
    if len(lyric_words) != len(timings):
        return None

    audio_path = dataset_dir / "mp3" / meta["Filepath"]
    last_end = round(timings[-1][1], 3) if timings else 0.0
    return {
        "id": stem,
        "audio_path": str(audio_path),
        "vocal_stem_path": None,
        "duration": track_duration(audio_path, fallback=last_end),
        "words": [
            {"text": text, "start": round(start, 3), "end": round(end, 3)}
            for text, (start, end) in zip(lyric_words, timings)
        ],
        "difficulty": None,
        "language": meta["Language"],
        "asr_confidence": None,
        "cer_vs_lyrics": None,
        "source": "jamendolyrics",
        "license": meta["LicenseType"],
    }


def ingest(dataset_dir: Path, out_path: Path) -> dict:
    stats = {"ingested": 0, "skipped": 0}
    with open(dataset_dir / "JamendoLyrics.csv") as f, open(out_path, "w") as out:
        for meta in csv.DictReader(f):
            record = ingest_track(dataset_dir, meta)
            if record is None:
                stats["skipped"] += 1
                print(f"skip {meta['Filepath']}: missing files or word count mismatch")
                continue
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            stats["ingested"] += 1
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert JamendoLyrics gold to schema JSONL")
    parser.add_argument("--dataset-dir", type=Path, default=Path("data/jamendolyrics"))
    parser.add_argument("--out", type=Path, default=Path("data/bench/jamendolyrics.jsonl"))
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    stats = ingest(args.dataset_dir, args.out)
    print(f"ingested {stats['ingested']}, skipped {stats['skipped']} -> {args.out}")


if __name__ == "__main__":
    main()

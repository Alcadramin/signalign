import argparse
import json
import time
from pathlib import Path

from explore import force_align, pick_device, separate_vocals


def load_done_ids(out_path: Path) -> set[str]:
    if not out_path.exists():
        return set()
    with open(out_path) as f:
        return {json.loads(line)["id"] for line in f if line.strip()}


def pending(gold_records: list[dict], done_ids: set[str]) -> list[dict]:
    return [r for r in gold_records if r["id"] not in done_ids]


def align_record(record: dict, work_dir: Path, device: str) -> dict:
    vocal_path = separate_vocals(Path(record["audio_path"]), work_dir, device)
    words = [w["text"] for w in record["words"]]
    timed_words, duration = force_align(vocal_path, words, device)
    return {
        "id": record["id"],
        "audio_path": record["audio_path"],
        "vocal_stem_path": str(vocal_path),
        "duration": round(duration, 3),
        "words": timed_words,
        "difficulty": None,
        "asr_confidence": None,
        "cer_vs_lyrics": None,
        "source": "wav2vec2-base-960h+gold-lyrics",
        "license": record["license"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run lyrics-informed baseline over a gold manifest"
    )
    parser.add_argument("--gold", type=Path, default=Path("data/bench/jamendolyrics.jsonl"))
    parser.add_argument("--out", type=Path, default=Path("out/bench/wav2vec2_base.jsonl"))
    parser.add_argument("--work-dir", type=Path, default=Path("out/bench/stems"))
    args = parser.parse_args()

    device = pick_device()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.work_dir.mkdir(parents=True, exist_ok=True)

    with open(args.gold) as f:
        gold_records = [json.loads(line) for line in f if line.strip()]
    todo = pending(gold_records, load_done_ids(args.out))
    print(f"{len(todo)} of {len(gold_records)} tracks to align ({device})", flush=True)

    for index, record in enumerate(todo, 1):
        started = time.time()
        try:
            prediction = align_record(record, args.work_dir, device)
        except Exception as error:
            print(f"[{index}/{len(todo)}] {record['id']} FAILED: {error}", flush=True)
            continue
        with open(args.out, "a") as out:
            out.write(json.dumps(prediction, ensure_ascii=False) + "\n")
        elapsed = time.time() - started
        print(f"[{index}/{len(todo)}] {record['id']} ok ({elapsed:.0f}s)", flush=True)


if __name__ == "__main__":
    main()

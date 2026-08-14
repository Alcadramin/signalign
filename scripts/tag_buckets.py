import argparse
import csv
import json
import subprocess
from pathlib import Path

from apply_buckets import VALID_BUCKETS, load_buckets

KEYMAP = {"c": "clean", "r": "rap", "m": "melisma", "h": "held", "b": "buried"}


def load_genres(dataset_csv: Path) -> dict[str, str]:
    if not dataset_csv.exists():
        return {}
    with open(dataset_csv) as f:
        return {Path(row["Filepath"]).stem: row["Genre"] for row in csv.DictReader(f)}


def play(audio_path: str, start: float, duration: float) -> None:
    subprocess.run(
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet",
         "-ss", str(start), "-t", str(duration), audio_path],
        check=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Listen and tag difficulty buckets by ear")
    parser.add_argument("--manifest", type=Path, default=Path("data/bench/jamendolyrics.jsonl"))
    parser.add_argument("--buckets", type=Path, default=Path("data/bench/buckets.csv"))
    parser.add_argument("--dataset-csv", type=Path, default=Path("data/jamendolyrics/JamendoLyrics.csv"))
    parser.add_argument("--clip-seconds", type=float, default=25.0)
    args = parser.parse_args()

    records = [
        json.loads(line)
        for line in args.manifest.read_text().splitlines()
        if line.strip()
    ]
    done = load_buckets(args.buckets) if args.buckets.exists() else {}
    genres = load_genres(args.dataset_csv)
    todo = [r for r in records if r["id"] not in done]

    if not args.buckets.exists():
        args.buckets.parent.mkdir(parents=True, exist_ok=True)
        args.buckets.write_text("id,difficulty\n")

    print(f"{len(todo)} of {len(records)} tracks to tag")
    print("keys: [c]lean [r]ap [m]elisma [h]eld [b]uried | [p]lay again [f]ull [s]kip [q]uit")

    for record in todo:
        start = max(0.0, record["duration"] * 0.25)
        genre = genres.get(record["id"], "?")
        print(f"\n--- {record['id']}  (genre hint: {genre})")
        play(record["audio_path"], start, args.clip_seconds)
        while True:
            key = input("bucket> ").strip().lower()
            if key == "p":
                play(record["audio_path"], start, args.clip_seconds)
            elif key == "f":
                play(record["audio_path"], 0.0, record["duration"])
            elif key == "s":
                break
            elif key == "q":
                print("bye — progress saved, rerun to continue")
                return
            elif key in KEYMAP:
                with open(args.buckets, "a") as f:
                    f.write(f"{record['id']},{KEYMAP[key]}\n")
                print(f"  -> {KEYMAP[key]}")
                break
            else:
                print(f"  keys: {sorted(KEYMAP)} or p/f/s/q")

    print("\nall tagged. apply with: uv run scripts/apply_buckets.py")


if __name__ == "__main__":
    main()

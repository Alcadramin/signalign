import argparse
import csv
import json
from pathlib import Path

VALID_BUCKETS = {"clean", "rap", "melisma", "held", "buried"}


def load_buckets(csv_path: Path) -> dict[str, str]:
    with open(csv_path) as f:
        return {row["id"]: row["difficulty"] for row in csv.DictReader(f)}


def apply_buckets(manifest_path: Path, buckets: dict[str, str]) -> dict:
    unknown = set(buckets.values()) - VALID_BUCKETS
    if unknown:
        raise ValueError(f"unknown buckets: {sorted(unknown)}")

    records = [
        json.loads(line)
        for line in manifest_path.read_text().splitlines()
        if line.strip()
    ]
    stats = {"tagged": 0, "untagged": 0}
    for record in records:
        if record["id"] in buckets:
            record["difficulty"] = buckets[record["id"]]
            stats["tagged"] += 1
        else:
            stats["untagged"] += 1
    manifest_path.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)
    )
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply human difficulty buckets to a gold manifest")
    parser.add_argument("--manifest", type=Path, default=Path("data/bench/jamendolyrics.jsonl"))
    parser.add_argument("--buckets", type=Path, default=Path("data/bench/buckets.csv"))
    args = parser.parse_args()

    stats = apply_buckets(args.manifest, load_buckets(args.buckets))
    print(f"tagged {stats['tagged']}, untagged {stats['untagged']}")


if __name__ == "__main__":
    main()

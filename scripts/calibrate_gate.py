import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "eval"))

from score import match_words

DEFAULT_THRESHOLDS = [round(0.05 * i, 2) for i in range(20)]


def sweep(pairs: list[tuple[float, float]], thresholds=None) -> list[dict]:
    thresholds = DEFAULT_THRESHOLDS if thresholds is None else thresholds
    rows = []
    for threshold in thresholds:
        kept = [error for score, error in pairs if score >= threshold]
        rows.append(
            {
                "threshold": threshold,
                "kept_frac": round(len(kept) / len(pairs), 4) if pairs else 0.0,
                "median_error_ms": round(statistics.median(kept), 1) if kept else None,
                "frac_under_100ms": round(
                    sum(1 for e in kept if e <= 100) / len(kept), 4
                ) if kept else None,
            }
        )
    return rows


def segment_pairs(factory_records: list[dict], gold_by_track: dict) -> dict[str, list]:
    by_bucket: dict[str, list] = {}
    by_track: dict[str, list[dict]] = {}
    for record in factory_records:
        by_track.setdefault(record["track_id"], []).append(record)

    for track_id, segments in by_track.items():
        gold = gold_by_track.get(track_id)
        if gold is None:
            continue
        segments.sort(key=lambda r: r["track_offset"])
        flat_words = []
        segment_of = []
        for seg_index, segment in enumerate(segments):
            for word in segment["words"]:
                flat_words.append(
                    {"text": word["text"], "start": word["start"] + segment["track_offset"]}
                )
                segment_of.append(seg_index)

        errors_per_segment: dict[int, list[float]] = {}
        for pred_idx, gold_idx in match_words(flat_words, gold["words"]):
            error_ms = abs(flat_words[pred_idx]["start"] - gold["words"][gold_idx]["start"]) * 1000
            errors_per_segment.setdefault(segment_of[pred_idx], []).append(error_ms)

        bucket = gold.get("difficulty") or "unbucketed"
        for seg_index, errors in errors_per_segment.items():
            pair = (segments[seg_index]["alignment_score"], statistics.median(errors))
            by_bucket.setdefault(bucket, []).append(pair)
            by_bucket.setdefault("all", []).append(pair)
    return by_bucket


def load_jsonl(path: Path) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Calibrate gate threshold against bench gold")
    parser.add_argument("--factory-dir", type=Path, default=Path("out/factory_calib"))
    parser.add_argument("--gold", type=Path, default=Path("data/bench/jamendolyrics.jsonl"))
    parser.add_argument("--json", type=Path, default=Path("results/gate_calibration.json"))
    args = parser.parse_args()

    records = []
    for pile in ("keep", "hard"):
        pile_path = args.factory_dir / f"{pile}.jsonl"
        if pile_path.exists():
            records.extend(load_jsonl(pile_path))
    gold_by_track = {r["id"]: r for r in load_jsonl(args.gold)}

    by_bucket = segment_pairs(records, gold_by_track)
    output = {bucket: sweep(pairs) for bucket, pairs in sorted(by_bucket.items())}

    for bucket, rows in output.items():
        print(f"\n== {bucket} ({len(by_bucket[bucket])} segments)")
        print(f"{'thr':>5} {'kept':>6} {'mederr':>8} {'<=100ms':>8}")
        for row in rows:
            if row["threshold"] not in (0.0, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8):
                continue
            med = f"{row['median_error_ms']:.0f}" if row["median_error_ms"] is not None else "-"
            frac = f"{row['frac_under_100ms']:.2f}" if row["frac_under_100ms"] is not None else "-"
            print(f"{row['threshold']:>5.2f} {row['kept_frac']:>6.2f} {med:>8} {frac:>8}")

    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(output, indent=2) + "\n")
    print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()

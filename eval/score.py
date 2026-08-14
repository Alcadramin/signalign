import argparse
import json
import re
import statistics
from difflib import SequenceMatcher
from pathlib import Path

PCO_THRESHOLDS_MS = (100, 200, 300)


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9']", "", text.lower())


def match_words(pred_words: list[dict], gold_words: list[dict]) -> list[tuple[int, int]]:
    pred_norm = [normalize(w["text"]) for w in pred_words]
    gold_norm = [normalize(w["text"]) for w in gold_words]
    matcher = SequenceMatcher(a=pred_norm, b=gold_norm, autojunk=False)
    pairs = []
    for block in matcher.get_matching_blocks():
        for offset in range(block.size):
            pairs.append((block.a + offset, block.b + offset))
    return pairs


def bucket_of(segment: dict, group_by: str = "difficulty") -> str:
    return segment.get(group_by) or "unbucketed"


def metrics_from(errors_ms: list[float], n_gold: int) -> dict:
    matched = len(errors_ms)
    result = {
        "n_words": n_gold,
        "coverage": matched / n_gold if n_gold else 0.0,
        "mae_ms": round(statistics.mean(errors_ms), 1) if errors_ms else None,
        "medae_ms": round(statistics.median(errors_ms), 1) if errors_ms else None,
    }
    for tau in PCO_THRESHOLDS_MS:
        correct = sum(1 for e in errors_ms if e < tau)
        result[f"pco_{tau}"] = round(correct / n_gold, 4) if n_gold else 0.0
    return result


def score_segments(
    pred_segments: list[dict], gold_segments: list[dict], group_by: str = "difficulty"
) -> dict:
    pred_by_id = {s["id"]: s for s in pred_segments}
    errors_by_bucket: dict[str, list[float]] = {}
    gold_counts: dict[str, int] = {}

    for gold_seg in gold_segments:
        bucket = bucket_of(gold_seg, group_by)
        gold_words = gold_seg["words"]
        gold_counts[bucket] = gold_counts.get(bucket, 0) + len(gold_words)
        errors_by_bucket.setdefault(bucket, [])

        pred_seg = pred_by_id.get(gold_seg["id"])
        if pred_seg is None:
            continue
        pred_words = pred_seg["words"]
        for pred_idx, gold_idx in match_words(pred_words, gold_words):
            error_ms = abs(pred_words[pred_idx]["start"] - gold_words[gold_idx]["start"]) * 1000
            errors_by_bucket[bucket].append(error_ms)

    result = {
        bucket: metrics_from(errors, gold_counts[bucket])
        for bucket, errors in errors_by_bucket.items()
    }
    all_errors = [e for errors in errors_by_bucket.values() for e in errors]
    result["all"] = metrics_from(all_errors, sum(gold_counts.values()))
    return result


def load_jsonl(path: Path) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def score_files(pred_path: Path, gold_path: Path, group_by: str = "difficulty") -> dict:
    return score_segments(load_jsonl(pred_path), load_jsonl(gold_path), group_by)


def format_table(result: dict) -> str:
    header = f"{'bucket':<12} {'words':>6} {'cov':>6} {'MAE':>8} {'MedAE':>8} {'PCO@100':>8} {'PCO@200':>8} {'PCO@300':>8}"
    lines = [header, "-" * len(header)]
    buckets = sorted(b for b in result if b != "all") + ["all"]
    for bucket in buckets:
        m = result[bucket]
        mae = f"{m['mae_ms']:.0f}" if m["mae_ms"] is not None else "-"
        medae = f"{m['medae_ms']:.0f}" if m["medae_ms"] is not None else "-"
        lines.append(
            f"{bucket:<12} {m['n_words']:>6} {m['coverage']:>6.2f} {mae:>8} {medae:>8}"
            f" {m['pco_100']:>8.2%} {m['pco_200']:>8.2%} {m['pco_300']:>8.2%}"
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Score predicted alignments against gold")
    parser.add_argument("--pred", type=Path, required=True)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--json", type=Path, default=None)
    parser.add_argument("--group-by", default="difficulty")
    args = parser.parse_args()

    result = score_files(args.pred, args.gold, args.group_by)
    print(format_table(result))
    if args.json:
        args.json.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()

import json

from apply_buckets import apply_buckets, load_buckets


def test_load_buckets_reads_csv(tmp_path):
    csv_path = tmp_path / "buckets.csv"
    csv_path.write_text("id,difficulty\na,rap\nb,clean\n")
    assert load_buckets(csv_path) == {"a": "rap", "b": "clean"}


def test_apply_buckets_updates_matching_records(tmp_path):
    manifest = tmp_path / "gold.jsonl"
    records = [
        {"id": "a", "difficulty": None},
        {"id": "b", "difficulty": None},
    ]
    manifest.write_text("".join(json.dumps(r) + "\n" for r in records))

    stats = apply_buckets(manifest, {"a": "rap"})

    updated = [json.loads(line) for line in manifest.read_text().splitlines()]
    assert stats == {"tagged": 1, "untagged": 1}
    assert updated[0]["difficulty"] == "rap"
    assert updated[1]["difficulty"] is None


def test_apply_buckets_rejects_unknown_bucket(tmp_path):
    manifest = tmp_path / "gold.jsonl"
    manifest.write_text(json.dumps({"id": "a", "difficulty": None}) + "\n")
    try:
        apply_buckets(manifest, {"a": "shouty"})
        raised = False
    except ValueError:
        raised = True
    assert raised

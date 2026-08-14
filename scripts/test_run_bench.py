import json

from run_bench import load_done_ids, pending


def test_pending_filters_done_ids():
    gold = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    assert pending(gold, {"b"}) == [{"id": "a"}, {"id": "c"}]


def test_load_done_ids_reads_existing_manifest(tmp_path):
    out = tmp_path / "preds.jsonl"
    out.write_text(json.dumps({"id": "a"}) + "\n" + json.dumps({"id": "b"}) + "\n")
    assert load_done_ids(out) == {"a", "b"}


def test_load_done_ids_empty_when_missing(tmp_path):
    assert load_done_ids(tmp_path / "nope.jsonl") == set()

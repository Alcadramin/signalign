import json

import pytest

from score import match_words, score_files, score_segments


def seg(id_, words, difficulty=None):
    return {
        "id": id_,
        "audio_path": f"{id_}.wav",
        "duration": 30.0,
        "words": words,
        "difficulty": difficulty,
        "source": "test",
        "license": "CC0",
    }


def words(*starts, text=None):
    return [
        {"text": text[i] if text else f"w{i}", "start": s, "end": s + 0.1}
        for i, s in enumerate(starts)
    ]


def test_perfect_prediction_scores_zero_error():
    gold = [seg("a", words(1.0, 2.0, 3.0))]
    pred = [seg("a", words(1.0, 2.0, 3.0))]
    result = score_segments(pred, gold)
    assert result["all"]["mae_ms"] == 0.0
    assert result["all"]["medae_ms"] == 0.0
    assert result["all"]["pco_100"] == 1.0
    assert result["all"]["coverage"] == 1.0
    assert result["all"]["n_words"] == 3


def test_constant_offset_reflected_in_metrics():
    gold = [seg("a", words(1.0, 2.0, 3.0))]
    pred = [seg("a", words(1.15, 2.15, 3.15))]
    result = score_segments(pred, gold)
    assert result["all"]["mae_ms"] == pytest.approx(150.0)
    assert result["all"]["pco_100"] == 0.0
    assert result["all"]["pco_200"] == 1.0


def test_median_robust_to_outlier():
    gold = [seg("a", words(1.0, 2.0, 3.0))]
    pred = [seg("a", words(1.0, 2.0, 3.9))]
    result = score_segments(pred, gold)
    assert result["all"]["mae_ms"] == pytest.approx(300.0)
    assert result["all"]["medae_ms"] == 0.0


def test_missing_words_hurt_coverage_and_pco():
    gold = [seg("a", words(1.0, 2.0, 3.0, 4.0, text=["a", "b", "c", "d"]))]
    pred = [seg("a", words(1.0, 2.0, text=["a", "b"]))]
    result = score_segments(pred, gold)
    assert result["all"]["coverage"] == 0.5
    assert result["all"]["pco_100"] == 0.5
    assert result["all"]["mae_ms"] == 0.0


def test_missing_segment_counts_as_zero_coverage():
    gold = [seg("a", words(1.0, 2.0))]
    result = score_segments([], gold)
    assert result["all"]["coverage"] == 0.0
    assert result["all"]["pco_100"] == 0.0
    assert result["all"]["mae_ms"] is None


def test_buckets_reported_separately():
    gold = [
        seg("a", words(1.0), difficulty="rap"),
        seg("b", words(1.0), difficulty="melisma"),
    ]
    pred = [
        seg("a", words(1.05)),
        seg("b", words(1.25)),
    ]
    result = score_segments(pred, gold)
    assert result["rap"]["mae_ms"] == pytest.approx(50.0)
    assert result["melisma"]["mae_ms"] == pytest.approx(250.0)
    assert result["all"]["n_words"] == 2


def test_null_difficulty_grouped_as_unbucketed():
    gold = [seg("a", words(1.0))]
    pred = [seg("a", words(1.0))]
    result = score_segments(pred, gold)
    assert "unbucketed" in result


def test_match_words_ignores_case_and_punctuation():
    gold = [{"text": "Hello,", "start": 1.0, "end": 1.1}, {"text": "world!", "start": 2.0, "end": 2.1}]
    pred = [{"text": "hello", "start": 1.0, "end": 1.1}, {"text": "world", "start": 2.0, "end": 2.1}]
    pairs = match_words(pred, gold)
    assert pairs == [(0, 0), (1, 1)]


def test_match_words_skips_inserted_asr_words():
    gold = [{"text": "one", "start": 1.0, "end": 1.1}, {"text": "two", "start": 2.0, "end": 2.1}]
    pred = [
        {"text": "one", "start": 1.0, "end": 1.1},
        {"text": "uh", "start": 1.5, "end": 1.6},
        {"text": "two", "start": 2.0, "end": 2.1},
    ]
    pairs = match_words(pred, gold)
    assert pairs == [(0, 0), (2, 1)]


def test_score_files_reads_jsonl(tmp_path):
    gold_path = tmp_path / "gold.jsonl"
    pred_path = tmp_path / "pred.jsonl"
    gold_path.write_text(json.dumps(seg("a", words(1.0, 2.0))) + "\n")
    pred_path.write_text(json.dumps(seg("a", words(1.0, 2.0))) + "\n")
    result = score_files(pred_path, gold_path)
    assert result["all"]["pco_100"] == 1.0

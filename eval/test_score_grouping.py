from score import score_segments
from test_score import seg, words


def test_group_by_language():
    gold = [
        {**seg("a", words(1.0)), "language": "English"},
        {**seg("b", words(1.0)), "language": "French"},
    ]
    pred = [seg("a", words(1.05)), seg("b", words(1.25))]
    result = score_segments(pred, gold, group_by="language")
    assert result["English"]["mae_ms"] == 50.0
    assert result["French"]["mae_ms"] == 250.0


def test_group_by_missing_key_falls_back_to_unbucketed():
    gold = [seg("a", words(1.0))]
    pred = [seg("a", words(1.0))]
    result = score_segments(pred, gold, group_by="language")
    assert "unbucketed" in result

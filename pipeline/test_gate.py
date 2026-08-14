from gate import cer, route


def test_cer_identical_is_zero():
    assert cer("hello world", "hello world") == 0.0


def test_cer_counts_edits_over_reference_length():
    assert cer("abcd", "abed") == 0.25


def test_cer_empty_reference():
    assert cer("anything", "") == 1.0


def test_cer_normalizes_case_and_whitespace():
    assert cer("Hello  World", "hello world") == 0.0


def test_route_keeps_high_score_low_cer():
    segment = {"alignment_score": 0.8, "cer_vs_lyrics": 0.05}
    assert route(segment, min_score=0.5, max_cer=0.3) == "keep"


def test_route_hard_on_low_score():
    segment = {"alignment_score": 0.3, "cer_vs_lyrics": 0.05}
    assert route(segment, min_score=0.5, max_cer=0.3) == "hard"


def test_route_hard_on_high_cer():
    segment = {"alignment_score": 0.8, "cer_vs_lyrics": 0.6}
    assert route(segment, min_score=0.5, max_cer=0.3) == "hard"


def test_route_missing_cer_gates_on_score_alone():
    segment = {"alignment_score": 0.8, "cer_vs_lyrics": None}
    assert route(segment, min_score=0.5, max_cer=0.3) == "keep"

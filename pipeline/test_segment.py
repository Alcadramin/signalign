from segment import merge_spans, slice_words


def test_merge_spans_joins_small_gaps():
    spans = [(0.0, 2.0), (2.2, 4.0)]
    assert merge_spans(spans, min_gap=0.5, min_len=0.5, max_len=30.0) == [(0.0, 4.0)]


def test_merge_spans_keeps_large_gaps_separate():
    spans = [(0.0, 2.0), (5.0, 7.0)]
    assert merge_spans(spans, min_gap=0.5, min_len=0.5, max_len=30.0) == [(0.0, 2.0), (5.0, 7.0)]


def test_merge_spans_drops_short_segments():
    spans = [(0.0, 0.2), (5.0, 7.0)]
    assert merge_spans(spans, min_gap=0.5, min_len=0.5, max_len=30.0) == [(5.0, 7.0)]


def test_merge_spans_splits_overlong_segments():
    spans = [(0.0, 50.0)]
    result = merge_spans(spans, min_gap=0.5, min_len=0.5, max_len=30.0)
    assert result == [(0.0, 25.0), (25.0, 50.0)]
    assert all(end - start <= 30.0 for start, end in result)


def test_slice_words_assigns_by_midpoint_and_rebases():
    words = [
        {"text": "a", "start": 1.0, "end": 1.4},
        {"text": "b", "start": 5.0, "end": 5.4},
    ]
    segments = slice_words(words, [(0.0, 2.0), (4.5, 6.0)])
    assert len(segments) == 2
    assert segments[0]["span"] == (0.0, 2.0)
    assert segments[0]["words"] == [{"text": "a", "start": 1.0, "end": 1.4}]
    assert segments[1]["words"] == [{"text": "b", "start": 0.5, "end": 0.9}]


def test_slice_words_drops_empty_segments():
    words = [{"text": "a", "start": 1.0, "end": 1.4}]
    segments = slice_words(words, [(0.0, 2.0), (10.0, 12.0)])
    assert len(segments) == 1


def test_slice_words_word_outside_all_spans_lands_nowhere():
    words = [{"text": "a", "start": 8.0, "end": 8.4}]
    assert slice_words(words, [(0.0, 2.0)]) == []

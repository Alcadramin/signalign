from collections import namedtuple

from align import build_targets, group_spans

Span = namedtuple("Span", ["token", "start", "end", "score"])

LABELS = ("-", "|", "A", "B", "C")
DICTIONARY = {c: i for i, c in enumerate(LABELS)}


def test_build_targets_filters_unalignable_words():
    kept, targets = build_targets(["ab!", "??", "ca"], DICTIONARY)
    assert kept == ["ab!", "ca"]
    assert targets == [
        DICTIONARY["A"], DICTIONARY["B"],
        DICTIONARY["|"],
        DICTIONARY["C"], DICTIONARY["A"],
    ]


def test_group_spans_words_with_times_and_scores():
    spans = [
        Span(DICTIONARY["A"], 10, 12, 0.9),
        Span(DICTIONARY["B"], 13, 15, 0.7),
        Span(DICTIONARY["|"], 16, 16, 1.0),
        Span(DICTIONARY["C"], 20, 22, 0.5),
        Span(DICTIONARY["A"], 23, 24, 0.3),
    ]
    words = group_spans(spans, ["ab", "ca"], DICTIONARY["|"], seconds_per_frame=0.02)
    assert words == [
        {"text": "ab", "start": 0.2, "end": 0.3, "score": 0.8},
        {"text": "ca", "start": 0.4, "end": 0.48, "score": 0.4},
    ]


def test_group_spans_skips_words_with_no_spans():
    spans = [Span(DICTIONARY["A"], 10, 12, 0.9), Span(DICTIONARY["|"], 13, 13, 1.0)]
    words = group_spans(spans, ["a", "b"], DICTIONARY["|"], seconds_per_frame=0.02)
    assert [w["text"] for w in words] == ["a"]

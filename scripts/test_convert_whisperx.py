import json

from convert_whisperx import convert_file


def test_convert_flattens_segments_to_schema_words(tmp_path):
    wx = {
        "segments": [
            {"words": [
                {"word": "Live", "start": 16.03, "end": 16.23, "score": 0.777},
                {"word": "in", "start": 16.27, "end": 16.33, "score": 0.634},
            ]},
            {"words": [
                {"word": "time", "start": 17.0, "end": 17.4, "score": 0.9},
            ]},
        ]
    }
    path = tmp_path / "Track_A.json"
    path.write_text(json.dumps(wx))

    record = convert_file(path)

    assert record["id"] == "Track_A"
    assert record["source"] == "whisperx-medium"
    assert record["words"] == [
        {"text": "Live", "start": 16.03, "end": 16.23},
        {"text": "in", "start": 16.27, "end": 16.33},
        {"text": "time", "start": 17.0, "end": 17.4},
    ]


def test_convert_skips_untimed_words(tmp_path):
    wx = {"segments": [{"words": [
        {"word": "hmm"},
        {"word": "yes", "start": 1.0, "end": 1.2, "score": 0.5},
    ]}]}
    path = tmp_path / "Track_B.json"
    path.write_text(json.dumps(wx))
    assert [w["text"] for w in convert_file(path)["words"]] == ["yes"]

import json

from ingest_jamendolyrics import ingest


def make_dataset(root, tracks):
    (root / "lyrics").mkdir()
    (root / "annotations" / "words").mkdir(parents=True)
    (root / "mp3").mkdir()
    rows = ["URL,Filepath,Artist,Title,Genre,LicenseType,Language,LyricOverlap,Polyphonic,NonLexical"]
    for name, lyric_words, starts in tracks:
        rows.append(f"http://x/{name},{name}.mp3,Artist,{name},Pop,CC BY-SA,English,false,false,false")
        (root / "lyrics" / f"{name}.txt").write_text(" ".join(lyric_words) + "\n")
        ann = ["word_start,word_end,line_end"] + [
            f"{s},{s + 0.2},nan" for s in starts
        ]
        (root / "annotations" / "words" / f"{name}.csv").write_text("\n".join(ann) + "\n")
    (root / "JamendoLyrics.csv").write_text("\n".join(rows) + "\n")


def test_ingest_produces_schema_records(tmp_path):
    make_dataset(tmp_path, [("Song_A", ["hello", "world"], [1.5, 2.5])])
    out = tmp_path / "gold.jsonl"
    stats = ingest(tmp_path, out)

    records = [json.loads(line) for line in out.read_text().splitlines()]
    assert stats == {"ingested": 1, "skipped": 0}
    assert len(records) == 1
    rec = records[0]
    assert rec["id"] == "Song_A"
    assert rec["source"] == "jamendolyrics"
    assert rec["license"] == "CC BY-SA"
    assert rec["difficulty"] is None
    assert rec["language"] == "English"
    assert rec["words"] == [
        {"text": "hello", "start": 1.5, "end": 1.7},
        {"text": "world", "start": 2.5, "end": 2.7},
    ]
    assert rec["duration"] == 2.7
    assert rec["audio_path"].endswith("mp3/Song_A.mp3")


def test_ingest_skips_word_count_mismatch(tmp_path):
    make_dataset(tmp_path, [("Bad_Song", ["one", "two", "three"], [1.0])])
    out = tmp_path / "gold.jsonl"
    stats = ingest(tmp_path, out)
    assert stats == {"ingested": 0, "skipped": 1}
    assert out.read_text() == ""

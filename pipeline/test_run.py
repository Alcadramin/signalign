from pathlib import Path

from run import build_record, find_lyrics, load_config


def test_load_config_applies_defaults(tmp_path):
    cfg_path = tmp_path / "cfg.toml"
    cfg_path.write_text(
        '[input]\naudio_dir = "songs"\nsource = "test"\nlicense = "CC-BY-4.0"\n'
        '[output]\ndir = "out/test"\n'
    )
    cfg = load_config(cfg_path)
    assert cfg["input"]["audio_dir"] == "songs"
    assert cfg["vad"]["max_len"] == 30.0
    assert cfg["gate"]["min_score"] == 0.5
    assert cfg["gate"]["max_cer"] == 0.3


def test_load_config_overrides_defaults(tmp_path):
    cfg_path = tmp_path / "cfg.toml"
    cfg_path.write_text(
        '[input]\naudio_dir = "songs"\nsource = "s"\nlicense = "l"\n'
        '[output]\ndir = "o"\n'
        '[gate]\nmin_score = 0.7\n'
    )
    assert load_config(cfg_path)["gate"]["min_score"] == 0.7


def test_find_lyrics_reads_matching_txt(tmp_path):
    (tmp_path / "song.txt").write_text("hello world\n")
    assert find_lyrics(Path("x/song.mp3"), tmp_path) == ["hello", "world"]


def test_find_lyrics_none_when_missing(tmp_path):
    assert find_lyrics(Path("x/song.mp3"), tmp_path) is None


def test_build_record_produces_schema_segment():
    seg = {
        "span": (10.0, 22.5),
        "words": [{"text": "hi", "start": 1.0, "end": 1.3, "score": 0.8}],
    }
    record = build_record(
        track_id="song",
        index=4,
        segment=seg,
        clip_path=Path("clips/song_004.wav"),
        stem_path=Path("stems/song_004.wav"),
        source="test",
        license_="CC-BY-4.0",
        cer=0.1,
    )
    assert record["id"] == "song_seg004"
    assert record["duration"] == 12.5
    assert record["alignment_score"] == 0.8
    assert record["cer_vs_lyrics"] == 0.1
    assert record["words"][0]["score"] == 0.8
    assert record["difficulty"] is None
    assert record["audio_path"] == "clips/song_004.wav"
    assert record["vocal_stem_path"] == "stems/song_004.wav"

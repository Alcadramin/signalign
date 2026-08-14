from explore import load_lyrics_words


def test_load_lyrics_words_splits_lines_and_whitespace(tmp_path):
    lyrics = tmp_path / "lyrics.txt"
    lyrics.write_text("hello  world\n\nsecond line\n")
    assert load_lyrics_words(lyrics) == ["hello", "world", "second", "line"]


def test_load_lyrics_words_preserves_punctuation_and_case(tmp_path):
    lyrics = tmp_path / "lyrics.txt"
    lyrics.write_text("Hello, world!\n")
    assert load_lyrics_words(lyrics) == ["Hello,", "world!"]

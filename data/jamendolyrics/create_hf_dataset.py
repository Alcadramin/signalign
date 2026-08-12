"""Create a Hugging Face dataset from the JamendoLyrics dataset in its original layout."""

# %%
import glob
import shutil
from pathlib import Path

import datasets

# %%
LANGUAGE_MAP = {"English": "en", "Spanish": "es", "German": "de", "French": "fr"}

# %%
metadata = datasets.load_dataset(
    "csv",
    data_files={"test": "JamendoLyrics.csv"},
    split="test",
)

# %%
features = datasets.Features(
    {
        "name": datasets.Value("string"),
        "file_name": datasets.Value("string"),
        "url": datasets.Value("string"),
        "artist": datasets.Value("string"),
        "title": datasets.Value("string"),
        "genre": datasets.Value("string"),
        "license_type": datasets.Value("string"),
        "language": datasets.Value("string"),
        "lyric_overlap": datasets.Value("bool"),
        "polyphonic": datasets.Value("bool"),
        "non_lexical": datasets.Value("bool"),
        "text": datasets.Value("string"),
        "words": [
            {
                "start": datasets.Value("float32"),
                "end": datasets.Value("float32"),
                "text": datasets.Value("string"),
                "line_end": datasets.Value("bool"),
            }
        ],
        "lines": [
            {
                "start": datasets.Value("float32"),
                "end": datasets.Value("float32"),
                "text": datasets.Value("string"),
            }
        ],
    }
)

features_lines_in = datasets.Features(
    {
        "start_time": datasets.Value(dtype="float32", id=None),
        "end_time": datasets.Value(dtype="float32", id=None),
        "lyrics_line": datasets.Value(dtype="string", id=None),
    }
)
features_words_in = datasets.Features(
    {
        "word_start": datasets.Value(dtype="float32", id=None),
        "word_end": datasets.Value(dtype="float32", id=None),
        "line_end": datasets.Value(dtype="float32", id=None),
    }
)

# %%
data = {
    "name": [x.removesuffix(".mp3") for x in metadata["Filepath"]],
    "url": metadata["URL"],
    "artist": metadata["Artist"],
    "title": metadata["Title"],
    "genre": metadata["Genre"],
    "license_type": metadata["LicenseType"],
    "language": [LANGUAGE_MAP[x] for x in metadata["Language"]],
    "lyric_overlap": metadata["LyricOverlap"],
    "polyphonic": metadata["Polyphonic"],
    "non_lexical": metadata["NonLexical"],
    "text": [],
    "lines": [],
    "words": [],
}
data["file_name"] = [
    Path("subsets") / lg / "mp3" / f"{n}.mp3"
    for lg, n in zip(data["language"], data["name"])
]

for name in data["name"]:
    data["text"].append((Path("lyrics") / (name + ".txt")).read_text())
    lines = datasets.load_dataset(
        "csv",
        features=features_lines_in,
        data_files={
            "test": str(Path("annotations") / "lines" / glob.escape(name + ".csv"))
        },
        split="test",
    )
    data["lines"].append(
        [
            {
                "start": li["start_time"],
                "end": li["end_time"],
                "text": li["lyrics_line"],
            }
            for li in lines
        ]
    )
    words = datasets.load_dataset(
        "csv",
        features=features_words_in,
        data_files={
            "test": str(Path("annotations") / "words" / glob.escape(name + ".csv"))
        },
        split="test",
    )
    words_text = (Path("lyrics") / (name + ".words.txt")).read_text().splitlines()
    assert len(words) == len(words_text)
    assert all(w["line_end"] in [None, w["word_end"]] for w in words)
    data["words"].append(
        [
            {
                "start": w["word_start"],
                "end": w["word_end"],
                "text": text,
                "line_end": w["line_end"] is not None,
            }
            for w, text in zip(words, words_text)
        ]
    )

# %%
dataset = datasets.Dataset.from_dict(data, features=features)

# %%
dataset

# %%
# Divide the MP3 files by language. Hugging Face requires each subset and its metadadta to be in
# a separate directory. However, for backwards compatibility, we also want to keep the top-level
# "mp3" directory and replace the MP3 files with symlinks into the subsets.

# Back up the directory with the original MP3 files
if not Path("mp3_orig").exists():
    for path in Path("mp3").glob("*.mp3"):
        if path.is_symlink():
            target = path.resolve()
            path.unlink()
            target.rename(path)
    Path("mp3").rename("mp3_orig")
elif Path("mp3").exists():
    shutil.rmtree("mp3")
Path("mp3").mkdir(exist_ok=True)

subsets_dir = Path("subsets")
if subsets_dir.exists():
    shutil.rmtree(subsets_dir)
subsets_dir.mkdir()

# Create language subsets and:
# - hard link the files from mp3_orig to subsets
# - add symlinks from mp3 into subsets
for language in ["en", "es", "de", "fr"]:
    subset_dir = subsets_dir / language
    subset_dir.mkdir()
    subset = dataset.select(
        [i for i in range(len(dataset)) if dataset["language"][i] == language]
    )
    subset_file_names = subset["file_name"]
    subset = subset.remove_columns("file_name").add_column(
        "file_name", [str(Path(p).relative_to(subset_dir)) for p in subset_file_names]
    )
    subset.to_json(subset_dir / "metadata.jsonl")
    (subset_dir / "mp3").mkdir()
    for name in subset["name"]:
        (subset_dir / "mp3" / f"{name}.mp3").hardlink_to(
            Path("mp3_orig") / f"{name}.mp3"
        )
        (Path("mp3") / f"{name}.mp3").symlink_to(
            Path("..") / subset_dir / "mp3" / f"{name}.mp3"
        )

# Create the top-level data file for the "all" config
dataset.to_json("metadata.jsonl")

# %%

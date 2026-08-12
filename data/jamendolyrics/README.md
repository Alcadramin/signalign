---
multilinguality:
- multilingual
language:
- en
- fr
- de
- es
tags:
- music
- lyrics
- evaluation
- benchmark
- alignment
- ala
configs:
- config_name: all
  default: true
  data_files:
  - split: test
    path:
    - metadata.jsonl
    - subsets/*/mp3/*.mp3
- config_name: en
  data_files:
  - split: test
    path:
    - subsets/en/metadata.jsonl
    - subsets/en/mp3/*.mp3
- config_name: es
  data_files:
  - split: test
    path:
    - subsets/es/metadata.jsonl
    - subsets/es/mp3/*.mp3
- config_name: de
  data_files:
  - split: test
    path:
    - subsets/de/metadata.jsonl
    - subsets/de/mp3/*.mp3
- config_name: fr
  data_files:
  - split: test
    path:
    - subsets/fr/metadata.jsonl
    - subsets/fr/mp3/*.mp3
pretty_name: JamendoLyrics MultiLang dataset for lyrics research
---

# JamendoLyrics MultiLang dataset for lyrics research

## Dataset description

* **Paper (ICASSP 2023):** https://arxiv.org/abs/2306.07744
* **Paper (ICASSP 2019):** https://arxiv.org/abs/1902.06797
* **Related datasets:** https://huggingface.co/jamendolyrics

A dataset containing 79 songs with different genres and languages along with lyrics that 
are time-aligned on a word-by-word level (with start and end times) to the music.

> [!note]
> **Note:** The dataset is primarily intended as an **automatic lyrics alignment** (**ALA**) benchmark.
> For **lyrics transcription**, please see the [Jam-ALT](https://huggingface.co/datasets/jamendolyrics/jam-alt/)
> dataset, which contains a revised version of the lyrics, better suited as a reference for the transcription task.
> See also the [community readme](https://huggingface.co/jamendolyrics) for information about related datasets.

The dataset was introduced in the [ICASSP 2023](https://ieeexplore.ieee.org/document/10096725) paper (full citation [below](#citation)): \
📄 [**Similarity-based Audio-Lyrics Alignment of Multiple Languages**](https://arxiv.org/abs/2306.07744) \
👥 Simon Durand, Daniel Stoller, Sebastian Ewert (Spotify)

## Usage

The dataset can be loaded using 🤗 Datasets:
```python
from datasets import load_dataset
dataset = load_dataset("jamendolyrics/jamendolyrics", split="test")
```

A subset is defined for each language (`en`, `fr`, `de`, `es`);
for example, use `load_dataset("jamendolyrics/jamendolyrics", "es", split="test")` to load only the Spanish songs.

The dataset contains one record per song, with the audio in the `audio` column.
The the text and timing of each line and word can be found in the `lines` and `words` columns, respectively;
`text` contains the full lyrics of the song. Other metadata columns such as `language` are included;
see [below](#metadata-csv) for more information.

To control how the audio is decoded, cast the `audio` column using `dataset.cast_column("audio", datasets.Audio(...))`.
Useful arguments to `datasets.Audio()` are:
- `sampling_rate` and `mono=True` to control the sampling rate and number of channels.
- `decode=False` to skip decoding the audio and just get the raw MP3 files.

See [this blog post](https://huggingface.co/blog/audio-datasets) for a guide on audio datasets on Hugging Face.

The dataset can also be downloaded without installing 🤗 Datasets by
[cloning the Git repository](https://huggingface.co/datasets/jamendolyrics/jamendolyrics?clone=true) (with [Git LFS](https://git-lfs.com/) enabled).
To get the annotations and metadata, use either [`metadata.jsonl`](#the-🤗-dataset-metadatajsonl), or the CSV and text files described below.

## Metadata CSV

All songs are listed in `JamendoLyrics.csv` together with their metadata.
To load annotations you are interested in, you can iterate over this CSV and use the `Filepath` 
column to build file paths to files containing the data for each song (audio file, lyrics 
annotations). Among the metadata, "LyricOverlap" refers to whether or not the lyrics in the song overlap,
“Polyphonic” refers to whether or not there are multiple singers singing the same lyrics, but with different melodies,
and "NonLexical" refers to whether or not there is non-lexical singing (eg: scatting).

## Lyrics files

In the `lyrics` subfolder, we provide the lyrics to each song as `SONG_NAME.txt` (normalized, e.
g. special characters and characters not supported in `vocab/international.characters` are removed)

Furthermore, `SONG_NAME.words.txt` contains all the words, separated by 
lines, ignoring the paragraph structure of the original lyrics. This is used for the word-level timestamp annotations.

## Time-aligned lyrics annotations

We have aligned the lyrics on a word-by-word and line-by-line basis to the music.

Word-by-word start and end timestamps are stored in the "annotations/words" subfolder, and they 
also indicate whether the word represents the end of a line as well (it will have the word end 
timestamp set instead of NaN).

A line-by-line version of the lyrics is stored in the subfolder
"annotations/lines" as CSV files, denoting the start and end time of each lyrical line in the audio.
These contain one row per line in the form of `(start_time, end_time, lyrics_line)` and can be
used to train or evaluate models only on a line-by-line level.

### Modifying word-by-word timestamps

In case the word timestamps are modified, one needs to run `generate_lines.py` to 
update the line-level timestamp files in "annotations/lines" accordingly. 
You will need Python 3.10 with packages installed as listed in `requirements.txt`.

This is because the line-level annotation in "annotations/lines" is auto-generated based on the manual
word-by-word annotations: The start timestamp for each line is set to be the start timestamp of the 
word after an end-of-line word.

In case you find errors in the timestamp annotations, we encourage you to submit a pull request 
to this repository so we can correct the errors.

## The 🤗 dataset (`metadata.jsonl`)

This dataset has been ported from the [original GitHub repo](https://github.com/f90/jamendolyrics)
and adapted for Hugging Face Hub.

The Hugging Face version of the dataset is stored as `metadata.jsonl` files: one for the entire dataset
and one for each lanugage subset. The `file_name` field contains the audio file paths relative to the
`metadata.jsonl` file. These JSONL files were generated from the original CSV and text files using the
[`create_hf_dataset.py`](./create_hf_dataset.py) script, and need to be re-generated if any modifications
are made to the original files.

## Acknowledgements

We want to acknowledge our 2022 Research intern, [Emir Demirel](https://emirdemirel.github.io/), 
and Torr Yatco for their help in assembling this dataset.

## Original JamendoLyrics dataset

This dataset is an extended version of the original (English-only) JamendoLyrics dataset presented in the paper \
[End-to-end Lyrics Alignment for Polyphonic Music Using an Audio-to-Character Recognition Model](https://arxiv.org/abs/1902.06797)

It originally contained only 20 English songs and is now deprecated as annotations are slightly improved, 
so we discourage its use in the future.
You can find it archived [here](https://github.com/f90/jamendolyrics/releases/tag/original).

## Citation

```bibtex
@inproceedings{durand-2023-contrastive,
  author={Durand, Simon and Stoller, Daniel and Ewert, Sebastian},
  booktitle={2023 IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP)}, 
  title={Contrastive Learning-Based Audio to Lyrics Alignment for Multiple Languages}, 
  year={2023},
  pages={1-5},
  address={Rhodes Island, Greece},
  doi={10.1109/ICASSP49357.2023.10096725}
}
```
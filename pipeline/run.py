import argparse
import json
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from gate import cer as compute_cer
from gate import route

DEFAULTS = {
    "vad": {"min_gap": 0.5, "min_len": 1.0, "max_len": 30.0},
    "gate": {"min_score": 0.5, "max_cer": 0.3},
    "asr": {"enabled": True, "model": "medium"},
}


def load_config(cfg_path: Path) -> dict:
    with open(cfg_path, "rb") as f:
        cfg = tomllib.load(f)
    for section, defaults in DEFAULTS.items():
        cfg.setdefault(section, {})
        for key, value in defaults.items():
            cfg[section].setdefault(key, value)
    return cfg


def find_lyrics(audio_path: Path, lyrics_dir: Path | None) -> list[str] | None:
    if lyrics_dir is None:
        return None
    lyrics_path = Path(lyrics_dir) / f"{audio_path.stem}.txt"
    if not lyrics_path.exists():
        return None
    return lyrics_path.read_text().split()


def build_record(
    track_id: str,
    index: int,
    segment: dict,
    clip_path: Path,
    stem_path: Path,
    source: str,
    license_: str,
    cer: float | None,
) -> dict:
    words = segment["words"]
    span_start, span_end = segment["span"]
    scores = [w["score"] for w in words if "score" in w]
    return {
        "id": f"{track_id}_seg{index:03d}",
        "track_id": track_id,
        "track_offset": round(span_start, 3),
        "audio_path": str(clip_path),
        "vocal_stem_path": str(stem_path),
        "duration": round(span_end - span_start, 3),
        "words": words,
        "difficulty": None,
        "alignment_score": round(sum(scores) / len(scores), 4) if scores else None,
        "asr_confidence": None,
        "cer_vs_lyrics": cer,
        "source": source,
        "license": license_,
    }


def write_clip(source_path: Path, span: tuple[float, float], out_path: Path) -> None:
    import soundfile

    info = soundfile.info(str(source_path))
    start_frame = int(span[0] * info.samplerate)
    end_frame = int(span[1] * info.samplerate)
    audio, sample_rate = soundfile.read(
        str(source_path), start=start_frame, stop=end_frame, always_2d=True
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    soundfile.write(str(out_path), audio, sample_rate)


def transcribe_track(vocal_path: Path, model_size: str) -> str:
    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(vocal_path), vad_filter=True)
    return " ".join(s.text.strip() for s in segments)


def process_track(audio_path: Path, cfg: dict, workers: dict, out_dir: Path) -> dict:
    from segment import merge_spans, slice_words, vad_spans

    stem_path = workers["separator"].separate(audio_path, out_dir / "track_stems")
    lyric_words = find_lyrics(audio_path, cfg["input"].get("lyrics_dir"))

    track_cer = None
    if lyric_words is not None and cfg["asr"]["enabled"]:
        asr_text = transcribe_track(stem_path, cfg["asr"]["model"])
        track_cer = round(compute_cer(asr_text, " ".join(lyric_words)), 4)

    if lyric_words is None:
        asr_text = transcribe_track(stem_path, cfg["asr"]["model"])
        lyric_words = asr_text.split()

    timed_words, _ = workers["aligner"].align(stem_path, lyric_words)

    spans = merge_spans(
        vad_spans(str(stem_path)),
        min_gap=cfg["vad"]["min_gap"],
        min_len=cfg["vad"]["min_len"],
        max_len=cfg["vad"]["max_len"],
    )
    segments = slice_words(timed_words, spans)

    counts = {"keep": 0, "hard": 0}
    for index, seg in enumerate(segments):
        clip_path = out_dir / "clips" / f"{audio_path.stem}_seg{index:03d}.wav"
        stem_clip_path = out_dir / "stems" / f"{audio_path.stem}_seg{index:03d}.wav"
        write_clip(audio_path, seg["span"], clip_path)
        write_clip(stem_path, seg["span"], stem_clip_path)
        record = build_record(
            track_id=audio_path.stem,
            index=index,
            segment=seg,
            clip_path=clip_path.relative_to(out_dir),
            stem_path=stem_clip_path.relative_to(out_dir),
            source=cfg["input"]["source"],
            license_=cfg["input"]["license"],
            cer=track_cer,
        )
        pile = route(record, cfg["gate"]["min_score"], cfg["gate"]["max_cer"])
        counts[pile] += 1
        with open(out_dir / f"{pile}.jsonl", "a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Dataset factory: folder of songs -> gated aligned segments")
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()

    cfg = load_config(args.config)
    out_dir = Path(cfg["output"]["dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    from align import Aligner
    from separate import Separator

    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    workers = {"separator": Separator(device=device), "aligner": Aligner(device=device)}

    audio_dir = Path(cfg["input"]["audio_dir"])
    done_ids = set()
    for pile in ("keep", "hard"):
        manifest = out_dir / f"{pile}.jsonl"
        if manifest.exists():
            done_ids |= {
                json.loads(line)["id"].rsplit("_seg", 1)[0]
                for line in manifest.read_text().splitlines() if line.strip()
            }

    tracks = sorted(
        p for p in audio_dir.iterdir()
        if p.suffix.lower() in {".wav", ".mp3", ".flac", ".ogg"}
    )
    todo = [t for t in tracks if t.stem not in done_ids]
    print(f"{len(todo)} of {len(tracks)} tracks to process ({device})", flush=True)

    for i, track in enumerate(todo, 1):
        try:
            counts = process_track(track, cfg, workers, out_dir)
        except Exception as error:
            print(f"[{i}/{len(todo)}] {track.stem} FAILED: {error}", flush=True)
            continue
        print(f"[{i}/{len(todo)}] {track.stem}: keep={counts['keep']} hard={counts['hard']}", flush=True)


if __name__ == "__main__":
    main()

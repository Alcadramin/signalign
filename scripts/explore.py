import argparse
import json
import math
import re
import unicodedata
from pathlib import Path

import soundfile
import torch
import torchaudio
from demucs.api import Separator, save_audio
from faster_whisper import WhisperModel


def pick_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


def separate_vocals(audio_path: Path, out_dir: Path, device: str) -> Path:
    vocal_path = out_dir / f"{audio_path.stem}_vocals.wav"
    if vocal_path.exists():
        return vocal_path
    separator = Separator(model="htdemucs", device=device)
    _, stems = separator.separate_audio_file(str(audio_path))
    save_audio(stems["vocals"], str(vocal_path), samplerate=separator.samplerate)
    return vocal_path


def transcribe(vocal_path: Path, device: str, model_size: str) -> tuple[list[str], float]:
    compute_type = "float16" if device == "cuda" else "int8"
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    segments, _ = model.transcribe(str(vocal_path), vad_filter=True)
    words: list[str] = []
    logprobs: list[float] = []
    for segment in segments:
        words.extend(segment.text.split())
        logprobs.append(segment.avg_logprob)
    confidence = math.exp(sum(logprobs) / len(logprobs)) if logprobs else 0.0
    return words, confidence


def load_lyrics_words(lyrics_path: Path) -> list[str]:
    return lyrics_path.read_text().split()


def normalize_word(word: str) -> str:
    decomposed = unicodedata.normalize("NFKD", word)
    ascii_only = decomposed.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^A-Z']", "", ascii_only.upper())


def force_align(
    vocal_path: Path, words: list[str], device: str
) -> tuple[list[dict], float]:
    bundle = torchaudio.pipelines.WAV2VEC2_ASR_BASE_960H
    model = bundle.get_model().to(device)
    labels = bundle.get_labels()
    dictionary = {c: i for i, c in enumerate(labels)}
    separator_id = dictionary["|"]

    audio, sample_rate = soundfile.read(str(vocal_path), dtype="float32", always_2d=True)
    mono = torch.from_numpy(audio.T).mean(0, keepdim=True)
    if sample_rate != bundle.sample_rate:
        mono = torchaudio.functional.resample(mono, sample_rate, bundle.sample_rate)

    with torch.inference_mode():
        emissions, _ = model(mono.to(device))
    log_probs = torch.log_softmax(emissions, dim=-1).cpu()

    aligned = [(w, normalize_word(w)) for w in words]
    aligned = [(orig, norm) for orig, norm in aligned if norm]
    if not aligned:
        raise ValueError("no alignable words in transcript")

    target_ids: list[int] = []
    for index, (_, norm) in enumerate(aligned):
        if index > 0:
            target_ids.append(separator_id)
        target_ids.extend(dictionary[c] for c in norm)
    targets = torch.tensor([target_ids], dtype=torch.int32)

    alignments, scores = torchaudio.functional.forced_align(log_probs, targets, blank=0)
    token_spans = torchaudio.functional.merge_tokens(alignments[0], scores[0], blank=0)

    seconds_per_frame = mono.size(1) / log_probs.size(1) / bundle.sample_rate
    duration = mono.size(1) / bundle.sample_rate

    word_spans: list[list] = [[]]
    for span in token_spans:
        if span.token == separator_id:
            word_spans.append([])
        else:
            word_spans[-1].append(span)

    timed_words = []
    for (orig, _), spans in zip(aligned, word_spans):
        if not spans:
            continue
        timed_words.append(
            {
                "text": orig,
                "start": round(spans[0].start * seconds_per_frame, 3),
                "end": round(spans[-1].end * seconds_per_frame, 3),
            }
        )
    return timed_words, duration


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Baseline sung-vocal aligner: Demucs -> Whisper -> wav2vec2 forced alignment"
    )
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--lyrics", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--whisper-model", default="medium")
    parser.add_argument("--work-dir", type=Path, default=Path("out"))
    args = parser.parse_args()

    device = pick_device()
    args.work_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out or args.work_dir / f"{args.audio.stem}.jsonl"

    print(f"[1/3] separating vocals (demucs htdemucs, {device})")
    vocal_path = separate_vocals(args.audio, args.work_dir, device)

    if args.lyrics:
        print("[2/3] using provided lyrics (no ASR)")
        words, confidence = load_lyrics_words(args.lyrics), None
        if not words:
            raise SystemExit("lyrics file is empty")
        print(f"      {len(words)} words")
    else:
        print(f"[2/3] transcribing (faster-whisper {args.whisper_model})")
        words, confidence = transcribe(vocal_path, device, args.whisper_model)
        if not words:
            raise SystemExit("whisper produced no transcript; is there a vocal?")
        print(f"      {len(words)} words, asr_confidence={confidence:.2f}")

    print("[3/3] forced alignment (wav2vec2 CTC)")
    timed_words, duration = force_align(vocal_path, words, device)

    record = {
        "id": args.audio.stem,
        "audio_path": str(args.audio),
        "vocal_stem_path": str(vocal_path),
        "duration": round(duration, 3),
        "words": timed_words,
        "difficulty": None,
        "asr_confidence": round(confidence, 3) if confidence is not None else None,
        "cer_vs_lyrics": None,
        "source": "local",
        "license": "unknown",
    }
    with open(out_path, "w") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"wrote {out_path} ({len(timed_words)} aligned words)")


if __name__ == "__main__":
    main()

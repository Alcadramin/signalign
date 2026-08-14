import argparse
import json
from pathlib import Path


def convert_file(json_path: Path) -> dict:
    data = json.loads(json_path.read_text())
    words = [
        {"text": w["word"].strip(), "start": w["start"], "end": w["end"]}
        for segment in data["segments"]
        for w in segment.get("words", [])
        if "start" in w
    ]
    return {
        "id": json_path.stem,
        "audio_path": None,
        "vocal_stem_path": None,
        "duration": round(words[-1]["end"], 3) if words else 0.0,
        "words": words,
        "difficulty": None,
        "asr_confidence": None,
        "cer_vs_lyrics": None,
        "source": "whisperx-medium",
        "license": "unknown",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert WhisperX JSON outputs to schema JSONL")
    parser.add_argument("--in-dir", type=Path, default=Path("out/whisperx"))
    parser.add_argument("--out", type=Path, default=Path("out/bench/whisperx_medium.jsonl"))
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as out:
        for json_path in sorted(args.in_dir.glob("*.json")):
            record = convert_file(json_path)
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(f"{record['id']}: {len(record['words'])} words")


if __name__ == "__main__":
    main()

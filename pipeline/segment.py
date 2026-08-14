def merge_spans(
    spans: list[tuple[float, float]], min_gap: float, min_len: float, max_len: float
) -> list[tuple[float, float]]:
    merged: list[list[float]] = []
    for start, end in sorted(spans):
        if merged and start - merged[-1][1] < min_gap:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])

    result: list[tuple[float, float]] = []
    for start, end in merged:
        length = end - start
        if length < min_len:
            continue
        if length <= max_len:
            result.append((start, end))
            continue
        pieces = int(length // max_len) + 1
        piece_len = length / pieces
        for i in range(pieces):
            result.append((start + i * piece_len, start + (i + 1) * piece_len))
    return result


def slice_words(
    words: list[dict], spans: list[tuple[float, float]]
) -> list[dict]:
    segments = []
    for span_start, span_end in spans:
        inside = [
            w for w in words
            if span_start <= (w["start"] + w["end"]) / 2 < span_end
        ]
        if not inside:
            continue
        segments.append(
            {
                "span": (span_start, span_end),
                "words": [
                    {
                        "text": w["text"],
                        "start": round(w["start"] - span_start, 3),
                        "end": round(w["end"] - span_start, 3),
                        **({"score": w["score"]} if "score" in w else {}),
                    }
                    for w in inside
                ],
            }
        )
    return segments


def vad_spans(vocal_path: str, sample_rate: int = 16000) -> list[tuple[float, float]]:
    import torch
    from silero_vad import get_speech_timestamps, load_silero_vad, read_audio

    model = load_silero_vad()
    audio = read_audio(vocal_path, sampling_rate=sample_rate)
    timestamps = get_speech_timestamps(audio, model, sampling_rate=sample_rate)
    return [(t["start"] / sample_rate, t["end"] / sample_rate) for t in timestamps]

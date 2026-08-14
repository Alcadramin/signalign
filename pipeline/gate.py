import re


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def cer(hypothesis: str, reference: str) -> float:
    hyp, ref = _normalize(hypothesis), _normalize(reference)
    if not ref:
        return 0.0 if not hyp else 1.0
    previous = list(range(len(hyp) + 1))
    for i, ref_char in enumerate(ref, 1):
        current = [i]
        for j, hyp_char in enumerate(hyp, 1):
            cost = 0 if ref_char == hyp_char else 1
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost))
        previous = current
    return min(1.0, previous[-1] / len(ref))


def route(segment: dict, min_score: float, max_cer: float) -> str:
    if segment["alignment_score"] < min_score:
        return "hard"
    segment_cer = segment.get("cer_vs_lyrics")
    if segment_cer is not None and segment_cer > max_cer:
        return "hard"
    return "keep"

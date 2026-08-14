import re
import unicodedata
from pathlib import Path


def normalize_word(word: str) -> str:
    decomposed = unicodedata.normalize("NFKD", word)
    ascii_only = decomposed.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^A-Z']", "", ascii_only.upper())


def build_targets(words: list[str], dictionary: dict[str, int]) -> tuple[list[str], list[int]]:
    separator_id = dictionary["|"]
    kept: list[str] = []
    targets: list[int] = []
    for word in words:
        norm = normalize_word(word)
        tokens = [dictionary[c] for c in norm if c in dictionary]
        if not tokens:
            continue
        if kept:
            targets.append(separator_id)
        targets.extend(tokens)
        kept.append(word)
    return kept, targets


def group_spans(
    token_spans, words: list[str], separator_id: int, seconds_per_frame: float
) -> list[dict]:
    per_word: list[list] = [[]]
    for span in token_spans:
        if span.token == separator_id:
            per_word.append([])
        else:
            per_word[-1].append(span)

    result = []
    for word, spans in zip(words, per_word):
        if not spans:
            continue
        result.append(
            {
                "text": word,
                "start": round(spans[0].start * seconds_per_frame, 3),
                "end": round(spans[-1].end * seconds_per_frame, 3),
                "score": round(sum(s.score for s in spans) / len(spans), 4),
            }
        )
    return result


class Aligner:
    def __init__(self, device: str = "cpu"):
        import torch
        import torchaudio

        self._torch = torch
        self._torchaudio = torchaudio
        self._bundle = torchaudio.pipelines.WAV2VEC2_ASR_BASE_960H
        self._model = self._bundle.get_model().to(device)
        self._labels = self._bundle.get_labels()
        self._dictionary = {c: i for i, c in enumerate(self._labels)}
        self._device = device

    @property
    def sample_rate(self) -> int:
        return self._bundle.sample_rate

    def align(self, vocal_path: Path, words: list[str]) -> tuple[list[dict], float]:
        import soundfile

        torch = self._torch
        audio, sample_rate = soundfile.read(str(vocal_path), dtype="float32", always_2d=True)
        mono = torch.from_numpy(audio.T).mean(0, keepdim=True)
        if sample_rate != self.sample_rate:
            mono = self._torchaudio.functional.resample(mono, sample_rate, self.sample_rate)

        with torch.inference_mode():
            emissions, _ = self._model(mono.to(self._device))
        log_probs = torch.log_softmax(emissions, dim=-1).cpu()

        kept, targets = build_targets(words, self._dictionary)
        if not kept:
            raise ValueError("no alignable words")
        target_tensor = torch.tensor([targets], dtype=torch.int32)

        alignments, scores = self._torchaudio.functional.forced_align(
            log_probs, target_tensor, blank=0
        )
        token_spans = self._torchaudio.functional.merge_tokens(
            alignments[0], scores[0].exp(), blank=0
        )

        seconds_per_frame = mono.size(1) / log_probs.size(1) / self.sample_rate
        duration = mono.size(1) / self.sample_rate
        return group_spans(token_spans, kept, self._dictionary["|"], seconds_per_frame), duration

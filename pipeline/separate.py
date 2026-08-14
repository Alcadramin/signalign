from pathlib import Path


class Separator:
    def __init__(self, device: str = "cpu", model: str = "htdemucs"):
        from demucs.api import Separator as DemucsSeparator

        self._separator = DemucsSeparator(model=model, device=device)

    def separate(self, audio_path: Path, out_dir: Path) -> Path:
        from demucs.api import save_audio

        vocal_path = out_dir / f"{audio_path.stem}_vocals.wav"
        if vocal_path.exists():
            return vocal_path
        out_dir.mkdir(parents=True, exist_ok=True)
        _, stems = self._separator.separate_audio_file(str(audio_path))
        save_audio(stems["vocals"], str(vocal_path), samplerate=self._separator.samplerate)
        return vocal_path

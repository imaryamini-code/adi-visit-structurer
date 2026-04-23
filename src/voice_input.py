"""
src/voice_input.py
Audio transcription using faster-whisper.
Optimized for Italian clinical dictation.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from faster_whisper import WhisperModel

# Model size: "base" (fast) or "small" (more accurate)
_MODEL_SIZE = "base"
_model: Optional[WhisperModel] = None


def _get_model() -> WhisperModel:
    """Lazy-load the Whisper model (loaded once, reused across requests)."""
    global _model
    if _model is None:
        _model = WhisperModel(_MODEL_SIZE, device="cpu", compute_type="int8")
    return _model


def transcribe_audio(audio_path: str, model_size: str = _MODEL_SIZE) -> str:
    """
    Transcribe an audio file using faster-whisper.

    Args:
        audio_path: Path to audio file (.wav, .webm, .mp3, .m4a).
        model_size: Whisper model size ("base" or "small").

    Returns:
        Transcribed text string.

    Raises:
        FileNotFoundError: If the audio file does not exist.
        RuntimeError: If transcription fails.
    """
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    try:
        model = _get_model()
        segments, info = model.transcribe(
            str(path),
            language="it",
            initial_prompt=(
                "Trascrizione di una visita medica domiciliare ADI. "
                "Include parametri vitali come pressione, frequenza cardiaca, "
                "saturazione e temperatura corporea."
            ),
            beam_size=5,
            vad_filter=True,
        )

        text = " ".join(seg.text.strip() for seg in segments).strip()

        if not text:
            return "Nessun parlato rilevato."

        return text

    except Exception as e:
        raise RuntimeError(f"Transcription failed: {e}") from e

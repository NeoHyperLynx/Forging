"""
Generates cloned-voice dialogue lines using Coqui XTTS v2, running locally --
no external API, no per-call cost. Needs the `TTS` package and its model
weights (downloaded once, on first run).

pip install TTS
"""
import os
from pathlib import Path

from config import OUTPUT_DIR, VOICE_REFERENCES

# XTTS v2 is gated under the Coqui Public Model License -- first load prompts
# for interactive terms acceptance, which hangs forever in a script/notebook.
# Setting this before import auto-accepts it (see idiap/coqui-ai-TTS #78).
os.environ.setdefault("COQUI_TOS_AGREED", "1")

_tts_model = None


def _get_model():
    global _tts_model
    if _tts_model is None:
        from TTS.api import TTS  # imported lazily -- slow to load; pip package is coqui-tts

        _tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    return _tts_model


def generate_line(text: str, speaker: str, out_name: str, language: str = "en") -> str:
    ref = VOICE_REFERENCES.get(speaker)
    if not ref or not Path(ref).exists():
        raise FileNotFoundError(
            f"No voice reference for '{speaker}'. Record a 5-15s clean sample "
            f"and set it in config.py / VOICE_REFERENCES (or the matching env var)."
        )
    model = _get_model()
    out_path = Path(OUTPUT_DIR) / "voice" / out_name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    model.tts_to_file(text=text, speaker_wav=ref, language=language, file_path=str(out_path))
    return str(out_path)

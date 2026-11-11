import tempfile, os
import edge_tts
from ..config import settings

_whisper = None
VOICES = {"en": "en-IN-NeerjaNeural", "hi": "hi-IN-SwaraNeural", "mr": "mr-IN-AarohiNeural"}

def transcribe(audio: bytes, suffix=".webm") -> dict:
    global _whisper
    if _whisper is None:
        from faster_whisper import WhisperModel
        _whisper = WhisperModel(settings.whisper_model, compute_type="int8")
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(audio); path = f.name
    try:
        segs, info = _whisper.transcribe(path)
        return {"text": " ".join(s.text.strip() for s in segs), "language": info.language}
    finally:
        os.unlink(path)

async def synthesize(text: str, lang: str, rate: str = "+0%") -> bytes:
    if lang not in VOICES:
        raise ValueError("TTS currently supports en, hi, mr.")
    out = b""
    async for ch in edge_tts.Communicate(text[:4000], VOICES[lang], rate=rate).stream():
        if ch["type"] == "audio":
            out += ch["data"]
    return out

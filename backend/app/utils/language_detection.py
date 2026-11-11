from langdetect import detect, LangDetectException

def detect_language(text: str) -> str:
    try:
        return detect(text[:3000])
    except LangDetectException:
        return "unknown"

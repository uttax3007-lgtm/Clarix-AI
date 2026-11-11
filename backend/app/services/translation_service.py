from .ai_service import complete, SYSTEM

LANGS = {"en": "English", "hi": "Hindi", "mr": "Marathi", "gu": "Gujarati", "bn": "Bengali",
         "ta": "Tamil", "te": "Telugu", "kn": "Kannada", "ml": "Malayalam", "pa": "Punjabi"}

async def translate(text: str, target: str) -> str:
    """LLM-backed translation. Replace this function with an IndicTrans2 backend without touching callers."""
    q = (f"Translate into {LANGS[target]}. Keep legal, financial and official terms in original form followed by a "
         f"short bracketed explanation. Keep numbers and dates exact.\n<text>\n{text}\n</text>")
    return (await complete([{"role": "system", "content": SYSTEM}, {"role": "user", "content": q}]))[0]

import io, re
import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageOps, ImageFilter
from docx import Document

OCR_LANGS = "eng+hin+mar"  # requires tesseract-ocr-hin and tesseract-ocr-mar packs

def _ocr_image(img: Image.Image) -> tuple[str, float]:
    img = ImageOps.autocontrast(ImageOps.grayscale(img)).filter(ImageFilter.MedianFilter(3))
    if max(img.size) < 1500:
        img = img.resize((img.width * 2, img.height * 2))
    try:  # rotation correction
        osd = pytesseract.image_to_osd(img, output_type=pytesseract.Output.DICT)
        if osd.get("rotate"):
            img = img.rotate(-osd["rotate"], expand=True)
    except pytesseract.TesseractError:
        pass
    data = pytesseract.image_to_data(img, lang=OCR_LANGS, output_type=pytesseract.Output.DICT)
    words = [(w, float(c)) for w, c in zip(data["text"], data["conf"]) if w.strip() and float(c) >= 0]
    conf = sum(c for _, c in words) / len(words) if words else 0.0
    return " ".join(w for w, _ in words), round(conf, 1)

def clean(text: str) -> str:
    return re.sub(r"[ \t]+", " ", re.sub(r"\n{3,}", "\n\n", text)).strip()

def extract(path: str, ftype: str) -> list[dict]:
    """Return [{page, text, ocr, confidence}]. Raises ValueError for corrupt/empty files."""
    pages = []
    try:
        if ftype == "pdf":
            with fitz.open(path) as pdf:
                for i, page in enumerate(pdf, 1):
                    text = page.get_text().strip()
                    if len(text) >= 20:
                        pages.append({"page": i, "text": clean(text), "ocr": False, "confidence": None})
                    else:  # scanned / image-only page -> OCR
                        pix = page.get_pixmap(dpi=200)
                        t, c = _ocr_image(Image.open(io.BytesIO(pix.tobytes("png"))))
                        pages.append({"page": i, "text": clean(t), "ocr": True, "confidence": c})
        elif ftype == "docx":
            d = Document(path)
            parts = [("## " if p.style.name.startswith("Heading") else "") + p.text for p in d.paragraphs if p.text.strip()]
            for t in d.tables:
                parts += [" | ".join(c.text.strip() for c in r.cells) for r in t.rows]
            pages.append({"page": 1, "text": clean("\n".join(parts)), "ocr": False, "confidence": None})
        else:
            t, c = _ocr_image(Image.open(path))
            pages.append({"page": 1, "text": clean(t), "ocr": True, "confidence": c})
    except Exception as e:
        raise ValueError(f"Could not read document ({type(e).__name__}).")
    if not any(p["text"] for p in pages):
        raise ValueError("No readable text found in the document.")
    return pages

def chunk(pages: list[dict], size: int = 900, overlap: int = 150) -> list[dict]:
    out = []
    for p in pages:
        t, s = p["text"], 0
        while s < len(t):
            out.append({"page": p["page"], "text": t[s:s + size]})
            s += size - overlap
    return out

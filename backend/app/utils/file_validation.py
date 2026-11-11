from fastapi import HTTPException
ALLOWED = {"pdf": (b"%PDF",), "docx": (b"PK\x03\x04",), "png": (b"\x89PNG",),
           "jpg": (b"\xff\xd8\xff",), "jpeg": (b"\xff\xd8\xff",)}

def validate_upload(filename: str, data: bytes, max_mb: int) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED:
        raise HTTPException(415, "Unsupported file type. Use PDF, DOCX, PNG, JPG or JPEG.")
    if len(data) == 0:
        raise HTTPException(400, "File is empty.")
    if len(data) > max_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {max_mb} MB limit.")
    if not any(data.startswith(sig) for sig in ALLOWED[ext]):
        raise HTTPException(400, "File content does not match its extension.")
    return ext

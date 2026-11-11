import pytest
from fastapi import HTTPException
from app.utils.file_validation import validate_upload
from app.services.document_service import chunk

def test_accepts_pdf(): assert validate_upload("a.pdf", b"%PDF-1.7 x", 1) == "pdf"
def test_rejects_exe():
    with pytest.raises(HTTPException) as e: validate_upload("a.exe", b"MZ", 1)
    assert e.value.status_code == 415
def test_rejects_spoofed_extension():
    with pytest.raises(HTTPException): validate_upload("a.pdf", b"MZ....", 1)
def test_rejects_oversize():
    with pytest.raises(HTTPException) as e: validate_upload("a.png", b"\x89PNG" + b"0" * 2_000_000, 1)
    assert e.value.status_code == 413
def test_chunk_keeps_page_numbers():
    cs = chunk([{"page": 3, "text": "x" * 2000}])
    assert cs and all(c["page"] == 3 for c in cs)

import os, uuid, logging
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from ..config import settings
from ..database import db
from ..middleware.authentication import current_user
from ..services import document_service as docs, rag_service, ai_service, translation_service
from ..utils.file_validation import validate_upload
from ..utils.language_detection import detect_language

router = APIRouter(prefix="/documents", tags=["documents"])
limiter = Limiter(key_func=get_remote_address)
log = logging.getLogger("clarix")

def _oid(v: str) -> ObjectId:
    try: return ObjectId(v)
    except InvalidId: raise HTTPException(404, "Document not found")

async def owned(doc_id: str, user: dict) -> dict:
    """Ownership check used by EVERY document operation."""
    d = await db.documents.find_one({"_id": _oid(doc_id), "user_id": user["_id"]})
    if not d: raise HTTPException(404, "Document not found")  # 404, not 403: don't leak existence
    return d

def _public(d: dict) -> dict:
    return {"id": str(d["_id"]), "title": d["original_filename"], "file_type": d["file_type"],
            "status": d["processing_status"], "error": d.get("error"), "language": d.get("detected_language"),
            "created_at": d["created_at"]}

async def run_pipeline(doc_id: ObjectId):
    async def status(s, **kw): await db.documents.update_one({"_id": doc_id}, {"$set": {"processing_status": s, **kw}})
    try:
        d = await db.documents.find_one({"_id": doc_id})
        await status("extracting")
        pages = docs.extract(os.path.join(settings.storage_dir, "files", d["storage_key"]), d["file_type"])
        text = "\n\n".join(p["text"] for p in pages)
        await status("indexing", extracted_text=text, pages=pages, detected_language=detect_language(text))
        rag_service.build_index(str(doc_id), docs.chunk(pages))
        await status("summarizing")
        summary, usage = await ai_service.summarize(pages)
        await db.document_summaries.update_one({"document_id": doc_id},
            {"$set": {**summary.model_dump(), "document_id": doc_id, "usage": usage}}, upsert=True)
        await status("ready", error=None)
    except (ValueError, ai_service.AIUnavailable) as e:
        await status("failed", error=str(e))
    except Exception as e:
        log.error("pipeline failed: %s", type(e).__name__)
        await status("failed", error="Processing failed unexpectedly.")

@router.post("/upload", status_code=201)
@limiter.limit("20/hour")
async def upload(request: Request, bg: BackgroundTasks, file: UploadFile = File(...), user=Depends(current_user)):
    data = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    ext = validate_upload(file.filename or "", data, settings.max_upload_mb)
    key = f"{uuid.uuid4().hex}.{ext}"  # random key; original name never touches the filesystem
    os.makedirs(os.path.join(settings.storage_dir, "files"), exist_ok=True)
    with open(os.path.join(settings.storage_dir, "files", key), "wb") as f: f.write(data)
    doc = {"user_id": user["_id"], "original_filename": os.path.basename(file.filename)[:200], "file_type": ext,
           "storage_key": key, "processing_status": "queued", "created_at": datetime.now(timezone.utc)}
    doc["_id"] = (await db.documents.insert_one(doc)).inserted_id
    bg.add_task(run_pipeline, doc["_id"])
    return _public(doc)

@router.get("")
async def list_docs(q: str = "", status: str = "", sort: str = "-created_at",
                    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100), user=Depends(current_user)):
    f: dict = {"user_id": user["_id"]}
    if q: f["original_filename"] = {"$regex": q[:60].replace("\\", ""), "$options": "i"}
    if status: f["processing_status"] = status
    field = sort.lstrip("-") if sort.lstrip("-") in ("created_at", "original_filename") else "created_at"
    cur = db.documents.find(f, {"extracted_text": 0, "pages": 0}).sort(field, -1 if sort.startswith("-") else 1).skip((page - 1) * size).limit(size)
    return {"items": [_public(d) async for d in cur], "total": await db.documents.count_documents(f), "page": page}

@router.get("/{doc_id}")
async def get_doc(doc_id: str, user=Depends(current_user)): return _public(await owned(doc_id, user))

class Rename(BaseModel): title: str = Field(min_length=1, max_length=200)

@router.patch("/{doc_id}")
async def rename(doc_id: str, body: Rename, user=Depends(current_user)):
    d = await owned(doc_id, user)
    await db.documents.update_one({"_id": d["_id"]}, {"$set": {"original_filename": body.title.strip()}})
    return {"ok": True}

@router.delete("/{doc_id}", status_code=204)
async def delete(doc_id: str, user=Depends(current_user)):
    d = await owned(doc_id, user)
    for p in (os.path.join(settings.storage_dir, "files", d["storage_key"]),):
        if os.path.exists(p): os.remove(p)
    for col in (db.documents, db.document_summaries, db.conversations):
        await col.delete_many({"_id": d["_id"]} if col is db.documents else {"document_id": d["_id"]})

@router.get("/{doc_id}/file")
async def download(doc_id: str, user=Depends(current_user)):
    d = await owned(doc_id, user)
    return FileResponse(os.path.join(settings.storage_dir, "files", d["storage_key"]), filename=d["original_filename"])

@router.post("/{doc_id}/process", status_code=202)
async def reprocess(doc_id: str, bg: BackgroundTasks, user=Depends(current_user)):
    d = await owned(doc_id, user)
    await db.documents.update_one({"_id": d["_id"]}, {"$set": {"processing_status": "queued"}})
    bg.add_task(run_pipeline, d["_id"]); return {"status": "queued"}

async def _summary(d: dict) -> dict:
    if d["processing_status"] != "ready": raise HTTPException(409, f"Document is {d['processing_status']}.")
    s = await db.document_summaries.find_one({"document_id": d["_id"]}, {"_id": 0, "document_id": 0, "usage": 0})
    if not s: raise HTTPException(404, "No summary available")
    return s

@router.get("/{doc_id}/summary")
async def summary(doc_id: str, level: int = Query(2, ge=1, le=3), language: str = "en", user=Depends(current_user)):
    s = await _summary(await owned(doc_id, user))
    try:
        explanation = await ai_service.explain(s, level, translation_service.LANGS.get(language, "English"))
    except ai_service.AIUnavailable as e: raise HTTPException(503, str(e))
    return {**s, "explanation": explanation, "level": level, "language": language}

@router.get("/{doc_id}/dates")
async def dates(doc_id: str, user=Depends(current_user)): return {"items": (await _summary(await owned(doc_id, user)))["important_dates"]}
@router.get("/{doc_id}/eligibility")
async def eligibility(doc_id: str, user=Depends(current_user)): return {"items": (await _summary(await owned(doc_id, user)))["eligibility"]}
@router.get("/{doc_id}/actions")
async def actions(doc_id: str, user=Depends(current_user)): return {"items": (await _summary(await owned(doc_id, user)))["action_items"]}

class TranslateIn(BaseModel):
    target: str = Field(pattern="^(en|hi|mr|gu|bn|ta|te|kn|ml|pa)$")
    text: str | None = Field(default=None, max_length=8000)

@router.post("/{doc_id}/translate")
@limiter.limit("30/hour")
async def translate(request: Request, doc_id: str, body: TranslateIn, user=Depends(current_user)):
    d = await owned(doc_id, user)
    text = body.text or (await _summary(d))["simple_summary"]
    try: return {"original": text, "translated": await translation_service.translate(text, body.target)}
    except ai_service.AIUnavailable as e: raise HTTPException(503, str(e))

class ChatIn(BaseModel):
    question: str = Field(min_length=2, max_length=1000)
    language: str = "en"

async def answer_question(d: dict, question: str, language: str) -> dict:
    if d["processing_status"] != "ready": raise HTTPException(409, f"Document is {d['processing_status']}.")
    hits = rag_service.retrieve(str(d["_id"]), question)
    try: reply = await ai_service.answer(question, hits, translation_service.LANGS.get(language, "English"))
    except ai_service.AIUnavailable as e: raise HTTPException(503, str(e))
    sources = [{"page": h["page"], "excerpt": h["text"][:240]} for h in hits[:3]]
    now = datetime.now(timezone.utc)
    await db.conversations.update_one({"document_id": d["_id"], "user_id": d["user_id"]},
        {"$push": {"messages": {"$each": [{"role": "user", "content": question, "at": now},
                                           {"role": "assistant", "content": reply, "at": now}]}},
         "$setOnInsert": {"created_at": now}}, upsert=True)
    return {"answer": reply, "sources": sources}

@router.post("/{doc_id}/chat")
@limiter.limit("60/hour")
async def chat(request: Request, doc_id: str, body: ChatIn, user=Depends(current_user)):
    return await answer_question(await owned(doc_id, user), body.question, body.language)

@router.get("/{doc_id}/chat")
async def history(doc_id: str, user=Depends(current_user)):
    d = await owned(doc_id, user)
    c = await db.conversations.find_one({"document_id": d["_id"], "user_id": user["_id"]})
    return {"messages": [{"role": m["role"], "content": m["content"]} for m in (c or {}).get("messages", [])]}

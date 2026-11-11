from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool
from ..middleware.authentication import current_user
from ..services import speech_service
from .documents import owned, answer_question

router = APIRouter(prefix="/voice", tags=["voice"])

@router.post("/transcribe")
async def transcribe(audio: UploadFile = File(...), document_id: str = Form(""), language: str = Form("en"),
                     user=Depends(current_user)):
    data = await audio.read(10 * 1024 * 1024 + 1)
    if not data or len(data) > 10 * 1024 * 1024: raise HTTPException(413, "Audio must be 1 byte–10 MB.")
    t = await run_in_threadpool(speech_service.transcribe, data)
    out = {"transcript": t["text"], "detected_language": t["language"]}
    if document_id and t["text"].strip():  # same grounding + ownership rules as typed questions
        out.update(await answer_question(await owned(document_id, user), t["text"], language))
    return out

class SynthIn(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    language: str = Field(pattern="^(en|hi|mr)$")
    rate: str = Field(default="+0%", pattern=r"^[+-]\d{1,2}%$")

@router.post("/synthesize")
async def synthesize(body: SynthIn, user=Depends(current_user)):
    return Response(await speech_service.synthesize(body.text, body.language, body.rate), media_type="audio/mpeg")

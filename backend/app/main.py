from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from .config import settings
from .database import init_indexes
from .api import documents, voice
from .middleware.error_handler import unhandled

@asynccontextmanager
async def lifespan(app):
    await init_indexes(); yield

app = FastAPI(title="CLARIX AI API", version="1.0.0", lifespan=lifespan)
app.state.limiter = documents.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(Exception, unhandled)
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
                   allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["Authorization", "Content-Type"])

@app.exception_handler(HTTPException)
async def http_err(_: Request, e: HTTPException):
    return JSONResponse({"error": {"code": e.status_code, "message": e.detail}}, status_code=e.status_code)

@app.exception_handler(RequestValidationError)
async def val_err(_: Request, e: RequestValidationError):
    return JSONResponse({"error": {"code": 422, "message": "Invalid input."}}, status_code=422)

app.include_router(documents.router, prefix="/api/v1")
app.include_router(voice.router, prefix="/api/v1")

@app.get("/api/v1/health")
async def health(): return {"status": "ok", "ai_configured": bool(settings.openrouter_api_key)}

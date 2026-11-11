import logging
from fastapi import Request
from fastapi.responses import JSONResponse
log = logging.getLogger("clarix")

async def unhandled(request: Request, exc: Exception):
    log.error("Unhandled error on %s: %s", request.url.path, type(exc).__name__)  # never log document content
    return JSONResponse({"error": {"code": "internal_error", "message": "Something went wrong."}}, status_code=500)

import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Header, HTTPException
from datetime import datetime, timezone
from ..config import settings
from ..database import db

if not firebase_admin._apps:
    cred = credentials.Certificate(settings.firebase_credentials_path) if settings.firebase_credentials_path else None
    firebase_admin.initialize_app(cred)

async def current_user(authorization: str = Header(default="")) -> dict:
    """Verify the Firebase ID token. The user id is NEVER taken from client input."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    try:
        decoded = auth.verify_id_token(authorization[7:])
    except Exception:
        raise HTTPException(401, "Invalid or expired token")
    return await db.users.find_one_and_update(
        {"firebase_uid": decoded["uid"]},
        {"$setOnInsert": {"firebase_uid": decoded["uid"], "full_name": decoded.get("name", ""),
                          "email": decoded.get("email", ""), "preferred_language": "en",
                          "created_at": datetime.now(timezone.utc)}},
        upsert=True, return_document=True)

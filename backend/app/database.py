from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

client = AsyncIOMotorClient(settings.mongodb_uri)
db = client[settings.mongodb_db]

async def init_indexes():
    await db.users.create_index("firebase_uid", unique=True)
    await db.documents.create_index([("user_id", 1), ("created_at", -1)])
    await db.document_summaries.create_index("document_id", unique=True)
    await db.conversations.create_index([("user_id", 1), ("document_id", 1)])

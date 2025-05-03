import json
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
COLLECTION_NAME = "valid_accounts"
DB_NAME = "bulk_validator"

async def import_accounts(json_path):
    with open(json_path) as f:
        accounts = json.load(f)
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    await collection.delete_many({})  # Optional: clear existing
    if accounts:
        await collection.insert_many(accounts)
    print(f"Imported {len(accounts)} accounts to MongoDB collection '{COLLECTION_NAME}'")

if __name__ == "__main__":
    import sys
    json_path = sys.argv[1] if len(sys.argv) > 1 else "app/valid_accounts.json"
    asyncio.run(import_accounts(json_path))

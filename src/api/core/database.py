from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from .config import get_settings

settings = get_settings()
client = AsyncIOMotorClient(settings.mongodb_url)
database = client[settings.database_name]

async def get_collection(collection_name: str) -> AsyncIOMotorCollection:
    return database[collection_name]

async def init_db():
    # Create indexes for stories collection
    stories_collection = database["stories"]
    await stories_collection.create_index("epic_id")
    await stories_collection.create_index("status")
    await stories_collection.create_index("priority")
    await stories_collection.create_index("tags")
    
    # Create vector search index for embeddings
    try:
        await stories_collection.create_index([("embedding", "vectorSearch")], 
                                           vectorSearchOptions={"kind": "knnBeta", "dimensions": 1536})
    except Exception as e:
        print(f"Note: Vector search index creation failed (this is expected if using MongoDB < 7.0): {e}")

async def close_db_connections():
    client.close()

from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from langchain_openai import OpenAIEmbeddings

from src.api.models.epics import Epic, UserStory
from src.config import OPENAI_API_KEY

class EpicService:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection
        self.embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
    
    async def create_epic(self, epic: Epic) -> Epic:
        epic_dict = epic.model_dump(exclude_none=True)
        epic_dict["created_at"] = datetime.utcnow()
        epic_dict["updated_at"] = epic_dict["created_at"]
        
        # Generate embedding for epic content
        epic_text = f"{epic.title} {epic.description}"
        if epic.acceptance_criteria:
            epic_text += " " + " ".join(epic.acceptance_criteria)
        embedding = await self.embeddings.aembed_query(epic_text)
        epic_dict["embedding"] = embedding
        
        result = await self.collection.insert_one(epic_dict)
        epic_dict["id"] = str(result.inserted_id)
        return Epic(**epic_dict)
    
    async def get_epic(self, epic_id: str) -> Optional[Epic]:
        if not ObjectId.is_valid(epic_id):
            return None
        epic_dict = await self.collection.find_one({"_id": ObjectId(epic_id)})
        if epic_dict:
            epic_dict["id"] = str(epic_dict.pop("_id"))
            return Epic(**epic_dict)
        return None
    
    async def update_epic(self, epic_id: str, epic_update: Epic) -> Optional[Epic]:
        if not ObjectId.is_valid(epic_id):
            return None
            
        epic_dict = epic_update.model_dump(exclude_none=True)
        epic_dict["updated_at"] = datetime.utcnow()
        
        # Generate new embedding if content changed
        epic_text = f"{epic_update.title} {epic_update.description}"
        if epic_update.acceptance_criteria:
            epic_text += " " + " ".join(epic_update.acceptance_criteria)
        embedding = await self.embeddings.aembed_query(epic_text)
        epic_dict["embedding"] = embedding

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(epic_id)},
            {"$set": epic_dict},
            return_document=True
        )
        
        if result:
            result["id"] = str(result.pop("_id"))
            return Epic(**result)
        return None
    
    async def delete_epic(self, epic_id: str) -> bool:
        if not ObjectId.is_valid(epic_id):
            return False
        result = await self.collection.delete_one({"_id": ObjectId(epic_id)})
        return result.deleted_count > 0
    
    async def list_epics(
        self, 
        skip: int = 0, 
        limit: int = 10,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Epic]:
        query = {}
        if status:
            query["status"] = status
        if priority:
            query["priority"] = priority
        if tags:
            query["tags"] = {"$all": tags}

        cursor = self.collection.find(query).skip(skip).limit(limit)
        epics = []
        async for epic in cursor:
            epic["id"] = str(epic.pop("_id"))
            epics.append(Epic(**epic))
        return epics
    
    async def search_similar_epics(
        self, 
        query: str, 
        limit: int = 5
    ) -> List[Epic]:
        query_embedding = await self.embeddings.aembed_query(query)
        
        pipeline = [
            {
                "$search": {
                    "knnBeta": {
                        "vector": query_embedding,
                        "path": "embedding",
                        "k": limit
                    }
                }
            },
            {"$limit": limit}
        ]
        
        epics = []
        async for epic in self.collection.aggregate(pipeline):
            epic["id"] = str(epic.pop("_id"))
            epics.append(Epic(**epic))
        return epics

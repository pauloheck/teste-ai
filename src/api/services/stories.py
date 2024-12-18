from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from langchain_openai import OpenAIEmbeddings

from ..models.stories import UserStory
from src.config import OPENAI_API_KEY

class StoryService:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection
        self.embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)

    async def create_story(self, story: UserStory) -> UserStory:
        story_dict = story.model_dump(exclude_none=True)
        story_dict["created_at"] = datetime.utcnow()
        story_dict["updated_at"] = story_dict["created_at"]
        
        # Generate embedding for story content
        story_text = f"{story.role} {story.action} {story.benefit}"
        if story.acceptance_criteria:
            story_text += " " + " ".join(story.acceptance_criteria)
        embedding = await self.embeddings.aembed_query(story_text)
        story_dict["embedding"] = embedding
        
        result = await self.collection.insert_one(story_dict)
        story_dict["id"] = str(result.inserted_id)
        return UserStory(**story_dict)

    async def get_story(self, story_id: str) -> Optional[UserStory]:
        if not ObjectId.is_valid(story_id):
            return None
        story_dict = await self.collection.find_one({"_id": ObjectId(story_id)})
        if story_dict:
            story_dict["id"] = str(story_dict.pop("_id"))
            return UserStory(**story_dict)
        return None

    async def update_story(self, story_id: str, story_update: UserStory) -> Optional[UserStory]:
        if not ObjectId.is_valid(story_id):
            return None
            
        story_dict = story_update.model_dump(exclude_none=True)
        story_dict["updated_at"] = datetime.utcnow()
        
        # Generate new embedding if content changed
        story_text = f"{story_update.role} {story_update.action} {story_update.benefit}"
        if story_update.acceptance_criteria:
            story_text += " " + " ".join(story_update.acceptance_criteria)
        embedding = await self.embeddings.aembed_query(story_text)
        story_dict["embedding"] = embedding

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(story_id)},
            {"$set": story_dict},
            return_document=True
        )
        
        if result:
            result["id"] = str(result.pop("_id"))
            return UserStory(**result)
        return None

    async def list_stories(
        self, 
        skip: int = 0, 
        limit: int = 10,
        epic_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[UserStory]:
        query = {}
        if epic_id:
            query["epic_id"] = epic_id
        if status:
            query["status"] = status
        if priority:
            query["priority"] = priority
        if tags:
            query["tags"] = {"$all": tags}

        cursor = self.collection.find(query).skip(skip).limit(limit)
        stories = []
        async for story in cursor:
            story["id"] = str(story.pop("_id"))
            stories.append(UserStory(**story))
        return stories

    async def delete_story(self, story_id: str) -> bool:
        if not ObjectId.is_valid(story_id):
            return False
        result = await self.collection.delete_one({"_id": ObjectId(story_id)})
        return result.deleted_count > 0

    async def search_similar_stories(
        self, 
        query: str, 
        limit: int = 5,
        epic_id: Optional[str] = None
    ) -> List[UserStory]:
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
            }
        ]
        
        if epic_id:
            pipeline.append({"$match": {"epic_id": epic_id}})
            
        pipeline.append({"$limit": limit})
        
        stories = []
        async for story in self.collection.aggregate(pipeline):
            story["id"] = str(story.pop("_id"))
            stories.append(UserStory(**story))
        return stories

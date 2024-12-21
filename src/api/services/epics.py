from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from src.models.epic import Epic, UserStory

class EpicService:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection
        
    async def create_epic(self, epic: Epic) -> str:
        epic_dict = epic.model_dump(exclude_none=True)
        epic_dict["created_at"] = datetime.utcnow()
        epic_dict["updated_at"] = epic_dict["created_at"]
        
        result = await self.collection.insert_one(epic_dict)
        return str(result.inserted_id)
    
    async def get_epic(self, epic_id: str) -> Optional[Epic]:
        if not ObjectId.is_valid(epic_id):
            return None
            
        epic_dict = await self.collection.find_one({"_id": ObjectId(epic_id)})
        if epic_dict:
            epic_dict["id"] = str(epic_dict.pop("_id"))
            return Epic(**epic_dict)
        return None
    
    async def update_epic(self, epic_id: str, epic_update: Epic) -> bool:
        if not ObjectId.is_valid(epic_id):
            return False
            
        epic_dict = epic_update.model_dump(exclude_none=True)
        epic_dict["updated_at"] = datetime.utcnow()
        
        result = await self.collection.update_one(
            {"_id": ObjectId(epic_id)},
            {"$set": epic_dict}
        )
        return result.modified_count > 0
    
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
        tags: Optional[List[str]] = None,
        sort_by: str = "created_at",
        sort_order: int = -1
    ) -> List[Epic]:
        # Construir o filtro
        filter_dict = {}
        if status:
            filter_dict["status"] = status
        if tags:
            filter_dict["tags"] = {"$all": tags}
            
        # Executar a consulta
        cursor = self.collection.find(filter_dict)
        
        # Aplicar ordenação
        cursor = cursor.sort(sort_by, sort_order)
        
        # Aplicar paginação
        cursor = cursor.skip(skip).limit(limit)
        
        # Converter resultados
        epics = []
        async for epic_dict in cursor:
            epic_dict["id"] = str(epic_dict.pop("_id"))
            epics.append(Epic(**epic_dict))
            
        return epics
    
    async def search_similar_epics(
        self,
        text: str,
        limit: int = 5,
        threshold: float = 0.5
    ) -> List[Epic]:
        # TODO: Implementar busca semântica usando embeddings
        return []

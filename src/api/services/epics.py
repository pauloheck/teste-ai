from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from src.api.models.epics import Epic, UserStory

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
    
    async def update_epic(self, epic_id: str, epic_update: Epic) -> Optional[Epic]:
        if not ObjectId.is_valid(epic_id):
            return None
            
        epic_dict = epic_update.model_dump(exclude_none=True)
        epic_dict["updated_at"] = datetime.utcnow()
        
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
        tags: Optional[List[str]] = None,
        sort_by: str = "created_at",
        sort_order: int = -1
    ) -> Dict[str, Any]:
        # Construir query de filtro
        filter_query = {}
        if status:
            filter_query["status"] = status
        if tags:
            filter_query["tags"] = {"$all": tags}
            
        # Contar total de documentos
        total = await self.collection.count_documents(filter_query)
        
        # Executar query com sort e paginação
        cursor = self.collection.find(filter_query)
        cursor = cursor.sort(sort_by, sort_order).skip(skip).limit(limit)
        
        # Processar resultados
        epics = []
        async for epic in cursor:
            epic["id"] = str(epic.pop("_id"))
            epics.append(Epic(**epic))
            
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "data": epics
        }
        
    async def search_similar(
        self,
        text: str,
        limit: int = 5,
        threshold: float = 0.5
    ) -> List[Epic]:
        # Por enquanto, faz uma busca simples por texto
        # TODO: Implementar busca por embeddings
        cursor = self.collection.find({
            "$or": [
                {"title": {"$regex": text, "$options": "i"}},
                {"description": {"$regex": text, "$options": "i"}},
                {"tags": {"$in": text.split()}}
            ]
        }).limit(limit)
        
        epics = []
        async for epic in cursor:
            epic["id"] = str(epic.pop("_id"))
            epics.append(Epic(**epic))
        return epics

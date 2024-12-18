import logging
from datetime import datetime
from typing import List, Optional, Dict
from bson import ObjectId
from pymongo import MongoClient, ASCENDING
from langchain_openai import OpenAIEmbeddings

from src.models.epic import Epic, UserStory, ExternalReference, EpicSource
from src.config import MONGODB_URI

logger = logging.getLogger(__name__)

class EpicService:
    def __init__(self):
        self.client = MongoClient(MONGODB_URI)
        self.db = self.client.getai
        self.epic_collection = self.db.epics
        self.embeddings = OpenAIEmbeddings()
        
        # Ensure indexes
        self._ensure_indexes()
        
    def _ensure_indexes(self):
        """Ensure all required indexes exist"""
        indexes = [
            ("title", ASCENDING),
            ("status", ASCENDING),
            ("created_at", ASCENDING),
            ("tags", ASCENDING),
            ("external_references.source", ASCENDING),
            ("external_references.external_id", ASCENDING),
        ]
        
        for field, direction in indexes:
            self.epic_collection.create_index([(field, direction)])
            
        # Criar índice para busca por similaridade
        self.epic_collection.create_index([("embedding", "2dsphere")])

    def _to_dict(self, epic: Epic) -> Dict:
        """Convert Epic object to dictionary for MongoDB"""
        epic_dict = {
            "title": epic.title,
            "description": epic.description,
            "objectives": epic.objectives,
            "user_stories": [
                {
                    "role": story.role,
                    "action": story.action,
                    "benefit": story.benefit,
                    "external_references": [
                        {
                            "source": ref.source.value,
                            "external_id": ref.external_id,
                            "url": ref.url,
                            "status": ref.status,
                            "last_sync": ref.last_sync
                        }
                        for ref in (story.external_references or [])
                    ]
                }
                for story in epic.user_stories
            ],
            "acceptance_criteria": epic.acceptance_criteria,
            "success_metrics": epic.success_metrics,
            "external_references": [
                {
                    "source": ref.source.value,
                    "external_id": ref.external_id,
                    "url": ref.url,
                    "status": ref.status,
                    "last_sync": ref.last_sync
                }
                for ref in (epic.external_references or [])
            ] if epic.external_references else [],
            "embedding": epic.embedding,
            "tags": epic.tags,
            "created_at": epic.created_at,
            "updated_at": epic.updated_at,
            "status": epic.status
        }
        return epic_dict

    def _from_dict(self, epic_dict: Dict) -> Epic:
        """Convert dictionary from MongoDB to Epic object"""
        # Convert user stories
        user_stories = []
        for story_dict in epic_dict["user_stories"]:
            external_refs = []
            if "external_references" in story_dict:
                for ref in story_dict["external_references"]:
                    external_refs.append(ExternalReference(
                        source=EpicSource(ref["source"]),
                        external_id=ref["external_id"],
                        url=ref["url"],
                        status=ref["status"],
                        last_sync=ref["last_sync"]
                    ))
            
            story = UserStory(
                role=story_dict["role"],
                action=story_dict["action"],
                benefit=story_dict["benefit"],
                external_references=external_refs if external_refs else None
            )
            user_stories.append(story)
        
        # Convert external references
        external_refs = []
        if epic_dict.get("external_references"):
            for ref in epic_dict["external_references"]:
                external_refs.append(ExternalReference(
                    source=EpicSource(ref["source"]),
                    external_id=ref["external_id"],
                    url=ref["url"],
                    status=ref["status"],
                    last_sync=ref["last_sync"]
                ))
        
        return Epic(
            title=epic_dict["title"],
            description=epic_dict["description"],
            objectives=epic_dict["objectives"],
            user_stories=user_stories,
            acceptance_criteria=epic_dict["acceptance_criteria"],
            success_metrics=epic_dict["success_metrics"],
            external_references=external_refs if external_refs else None,
            embedding=epic_dict.get("embedding"),
            tags=epic_dict.get("tags", []),
            created_at=epic_dict["created_at"],
            updated_at=epic_dict["updated_at"],
            status=epic_dict["status"]
        )

    async def create_epic(self, epic: Epic) -> str:
        """Create a new epic"""
        try:
            logger.info(f"[EPIC] Iniciando criação de épico: {epic.title}")
            
            # Generate embedding
            logger.info("[EPIC] Gerando embedding para o épico")
            text = epic.to_embedding_text()
            epic.embedding = await self.embeddings.aembed_query(text)
            logger.info(f"[EPIC] Embedding gerado com {len(epic.embedding)} dimensões")
            
            # Convert to dict and insert
            epic_dict = self._to_dict(epic)
            result = self.epic_collection.insert_one(epic_dict)
            
            logger.info(f"[EPIC] Épico criado com sucesso. ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"[EPIC] Erro ao criar épico: {str(e)}")
            raise

    async def get_epic(self, epic_id: str) -> Optional[Epic]:
        """Get epic by ID"""
        try:
            logger.info(f"[EPIC] Buscando épico por ID: {epic_id}")
            epic_dict = self.epic_collection.find_one({"_id": ObjectId(epic_id)})
            if epic_dict:
                logger.info(f"[EPIC] Épico encontrado: {epic_dict.get('title')}")
                return self._from_dict(epic_dict)
            logger.warning(f"[EPIC] Épico não encontrado: {epic_id}")
            return None
        except Exception as e:
            logger.error(f"[EPIC] Erro ao buscar épico {epic_id}: {str(e)}")
            raise

    async def update_epic(self, epic_id: str, epic: Epic) -> bool:
        """Update an existing epic"""
        try:
            logger.info(f"[EPIC] Iniciando atualização do épico {epic_id}")
            
            # Generate new embedding if content changed
            logger.info("[EPIC] Gerando novo embedding")
            text = epic.to_embedding_text()
            epic.embedding = await self.embeddings.aembed_query(text)
            epic.updated_at = datetime.utcnow()
            
            # Convert to dict and update
            epic_dict = self._to_dict(epic)
            result = self.epic_collection.update_one(
                {"_id": ObjectId(epic_id)},
                {"$set": epic_dict}
            )
            
            if result.modified_count > 0:
                logger.info(f"[EPIC] Épico {epic_id} atualizado com sucesso")
            else:
                logger.warning(f"[EPIC] Nenhuma modificação feita no épico {epic_id}")
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"[EPIC] Erro ao atualizar épico {epic_id}: {str(e)}")
            raise

    async def delete_epic(self, epic_id: str) -> bool:
        """Delete an epic"""
        try:
            logger.info(f"[EPIC] Iniciando remoção do épico {epic_id}")
            result = self.epic_collection.delete_one({"_id": ObjectId(epic_id)})
            
            if result.deleted_count > 0:
                logger.info(f"[EPIC] Épico {epic_id} removido com sucesso")
            else:
                logger.warning(f"[EPIC] Épico {epic_id} não encontrado para remoção")
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"[EPIC] Erro ao remover épico {epic_id}: {str(e)}")
            raise

    async def list_epics(
        self,
        skip: int = 0,
        limit: int = 10,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Epic]:
        """List epics with optional filters"""
        try:
            logger.info(f"[EPIC] Listando épicos. Skip: {skip}, Limit: {limit}, Status: {status}, Tags: {tags}")
            
            # Build query
            query = {}
            if status:
                query["status"] = status
            if tags:
                query["tags"] = {"$all": tags}
            
            # Execute query
            logger.info(f"[EPIC] Executando query com filtros: {query}")
            cursor = self.epic_collection.find(query).skip(skip).limit(limit)
            epics = [self._from_dict(epic_dict) for epic_dict in cursor]
            
            logger.info(f"[EPIC] {len(epics)} épicos encontrados")
            return epics
            
        except Exception as e:
            logger.error(f"[EPIC] Erro ao listar épicos: {str(e)}")
            raise

    async def search_similar_epics(
        self,
        text: str,
        limit: int = 5,
        min_similarity: float = 0.7
    ) -> List[Epic]:
        """Search for similar epics using embedding similarity"""
        try:
            logger.info(f"[EPIC] Iniciando busca por épicos similares. Texto: '{text[:50]}...'")
            
            # Generate embedding for search text
            logger.info("[EPIC] Gerando embedding para busca")
            query_embedding = await self.embeddings.aembed_query(text)
            
            # Search using vector similarity
            pipeline = [
                {
                    "$vectorSearch": {
                        "queryVector": query_embedding,
                        "path": "embedding",
                        "numCandidates": limit * 2,
                        "limit": limit,
                        "minScore": min_similarity
                    }
                }
            ]
            
            logger.info(f"[EPIC] Executando busca vetorial. Min Score: {min_similarity}")
            results = list(self.epic_collection.aggregate(pipeline))
            epics = [self._from_dict(epic_dict) for epic_dict in results]
            
            logger.info(f"[EPIC] {len(epics)} épicos similares encontrados")
            return epics
            
        except Exception as e:
            logger.error(f"[EPIC] Erro na busca por épicos similares: {str(e)}")
            raise

    async def link_external_reference(
        self,
        epic_id: str,
        source: EpicSource,
        external_id: str,
        url: str,
        status: str
    ) -> bool:
        """Link an epic to an external system"""
        try:
            ref = ExternalReference(
                source=source,
                external_id=external_id,
                url=url,
                status=status,
                last_sync=datetime.utcnow()
            )
            
            result = self.epic_collection.update_one(
                {"_id": ObjectId(epic_id)},
                {
                    "$push": {"external_references": self._to_dict(ref)},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            logger.info(f"[EPIC] Linked epic {epic_id} to {source.value} {external_id}")
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"[EPIC] Erro ao linkar épico {epic_id} to external reference: {str(e)}")
            raise

    async def update_external_reference(
        self,
        epic_id: str,
        source: EpicSource,
        external_id: str,
        status: str
    ) -> bool:
        """Update status of an external reference"""
        try:
            result = self.epic_collection.update_one(
                {
                    "_id": ObjectId(epic_id),
                    "external_references.source": source.value,
                    "external_references.external_id": external_id
                },
                {
                    "$set": {
                        "external_references.$.status": status,
                        "external_references.$.last_sync": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"[EPIC] Updated external reference status for epic {epic_id}")
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"[EPIC] Erro ao atualizar external reference for epic {epic_id}: {str(e)}")
            raise

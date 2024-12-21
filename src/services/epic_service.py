import logging
from datetime import datetime
from typing import List, Optional, Dict
from bson import ObjectId
from pymongo import ASCENDING
from motor import motor_asyncio
from src.config import MONGODB_URI, MONGODB_DB_NAME
from src.utils.azure_client import get_azure_chat_model, get_azure_embeddings
import asyncio

from src.models.epic import Epic, UserStory, ExternalReference, EpicSource

logger = logging.getLogger(__name__)

class EpicService:
    def __init__(self):
        """Initialize Epic Service with MongoDB connection."""
        try:
            # Initialize async services
            self.embeddings = None
            self.llm = None
            
            # Initialize MongoDB connection
            self.client = motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
            self.db = self.client[MONGODB_DB_NAME]
            self.epic_collection = self.db["epics"]
            
            logger.info("Successfully initialized EpicService")
            
        except Exception as e:
            logger.error(f"Failed to initialize EpicService: {str(e)}")
            raise
            
    async def initialize(self):
        """Initialize async services and ensure indexes."""
        try:
            # Initialize AI services
            self.embeddings = await get_azure_embeddings()
            self.llm = await get_azure_chat_model()
            
            # Ensure indexes exist
            await self._ensure_indexes()
            
            logger.info("Successfully initialized async services and indexes")
            
        except Exception as e:
            logger.error(f"Failed to initialize async services: {str(e)}")
            raise
            
    async def _ensure_indexes(self):
        """Ensure all required indexes exist"""
        try:
            # Get existing indexes
            existing_indexes = await self.epic_collection.list_indexes().to_list(None)
            existing_index_names = {idx.get('name') for idx in existing_indexes}
            
            # Define standard indexes
            standard_indexes = {
                "status_1": ("status", 1),
                "priority_1": ("priority", 1),
                "tags_1": ("tags", 1),
                "created_at_1": ("created_at", 1)
            }
            
            # Create standard indexes if they don't exist
            for idx_name, (field, direction) in standard_indexes.items():
                if idx_name not in existing_index_names:
                    try:
                        await self.epic_collection.create_index([(field, direction)])
                        logger.info(f"Created index {idx_name}")
                    except Exception as e:
                        logger.warning(f"Error creating index {idx_name}: {str(e)}")
            
            # Handle vector index
            vector_index_name = "embedding_2dsphere"
            try:
                # Only create if it doesn't exist
                if vector_index_name not in existing_index_names:
                    await self.epic_collection.create_index(
                        [("embedding", "2dsphere")],
                        name=vector_index_name,
                        sparse=True,
                        background=True
                    )
                    logger.info(f"Created vector index {vector_index_name}")
                else:
                    logger.info(f"Vector index {vector_index_name} already exists")
            except Exception as e:
                logger.warning(f"Error handling vector index: {str(e)}")
            
            logger.info("Successfully ensured all indexes")
            
        except Exception as e:
            logger.error(f"Error ensuring indexes: {str(e)}")
            # Don't raise the error to allow the service to continue
            
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
            result = await self.epic_collection.insert_one(epic_dict)
            
            logger.info(f"[EPIC] Épico criado com sucesso. ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"[EPIC] Erro ao criar épico: {str(e)}")
            raise

    async def get_epic(self, epic_id: str) -> Optional[Epic]:
        """Get epic by ID"""
        try:
            logger.info(f"[EPIC] Buscando épico por ID: {epic_id}")
            epic_dict = await self.epic_collection.find_one({"_id": ObjectId(epic_id)})
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
            result = await self.epic_collection.update_one(
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
            result = await self.epic_collection.delete_one({"_id": ObjectId(epic_id)})
            
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
            epics = [self._from_dict(epic_dict) async for epic_dict in cursor]
            
            logger.info(f"[EPIC] {len(epics)} épicos encontrados")
            return epics
            
        except Exception as e:
            logger.error(f"[EPIC] Erro ao listar épicos: {str(e)}")
            raise

    async def search_similar_epics(
        self,
        text: str,
        limit: int = 5,
        min_similarity: float = 0.7,
        num_candidates: int = 100
    ) -> List[Epic]:
        """Search for similar epics using vector similarity search.
        
        Args:
            text: Query text to search for
            limit: Maximum number of results to return
            min_similarity: Minimum similarity score (0-1) for results
            num_candidates: Number of candidates to consider (should be > limit)
        
        Returns:
            List of similar epics sorted by relevance
        """
        try:
            logger.info(f"[EPIC] Iniciando busca por épicos similares. Texto: '{text[:50]}...'")
            
            # Generate embedding for search text
            logger.info("[EPIC] Gerando embedding para busca")
            query_embedding = await self.embeddings.aembed_query(text)
            
            # Perform vector search
            pipeline = [
                {
                    "$geoNear": {
                        "near": {"type": "Point", "coordinates": query_embedding},
                        "distanceField": "distance",
                        "key": "embedding",  # Specify the field explicitly
                        "spherical": True,
                        "maxDistance": 1 - min_similarity,
                        "limit": num_candidates
                    }
                },
                {
                    "$addFields": {
                        "similarity_score": {
                            "$subtract": [1, "$distance"]
                        }
                    }
                },
                {
                    "$match": {
                        "similarity_score": {
                            "$gte": min_similarity
                        }
                    }
                },
                {
                    "$sort": {
                        "similarity_score": -1
                    }
                },
                {
                    "$limit": limit
                }
            ]
            
            logger.info(f"[EPIC] Executando busca vetorial. Min Score: {min_similarity}")
            results = await self.epic_collection.aggregate(pipeline).to_list(None)
            
            # Convert results to Epic objects
            epics = []
            for result in results:
                epic = self._from_dict(result)
                epic.metadata = {"similarity_score": result.get("similarity_score", 0)}
                epics.append(epic)
            
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
            
            result = await self.epic_collection.update_one(
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
            result = await self.epic_collection.update_one(
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

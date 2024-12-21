"""
Configurações e utilitários de banco de dados
"""
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from src.config.settings import get_settings

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect(cls):
        """Conecta ao MongoDB e inicializa índices"""
        if cls.client is None:
            settings = get_settings()
            cls.client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                maxPoolSize=10,
                minPoolSize=1
            )
            cls.db = cls.client[settings.MONGODB_DB_NAME]
            
            # Inicializa índices
            await cls._init_indexes()
    
    @classmethod
    async def _init_indexes(cls):
        """Inicializa os índices necessários"""
        if cls.db is None:
            return
            
        # Índices para coleção de stories
        stories = cls.db["stories"]
        await stories.create_index("epic_id")
        await stories.create_index("status")
        await stories.create_index("priority")
        await stories.create_index("tags")
        
        # Índices para coleção de documentos
        documents = cls.db["documents"]
        await documents.create_index("status")
        await documents.create_index("created_at")
        await documents.create_index("updated_at")
    
    @classmethod
    async def disconnect(cls):
        """Desconecta do MongoDB"""
        if cls.client is not None:
            cls.client.close()
            cls.client = None
            cls.db = None
    
    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """Retorna a instância do banco de dados"""
        if cls.db is None:
            raise RuntimeError("Database not initialized. Call connect() first.")
        return cls.db

    @classmethod
    async def get_collection(cls, collection_name: str) -> AsyncIOMotorCollection:
        """Retorna uma coleção do MongoDB"""
        if cls.db is None:
            await cls.connect()
        return cls.db[collection_name]
    
# Funções utilitárias para obter coleções específicas
async def get_epic_collection() -> AsyncIOMotorCollection:
    """Retorna a coleção de épicos"""
    db = MongoDB.get_database()
    return db["epics"]

async def get_document_collection() -> AsyncIOMotorCollection:
    """Retorna a coleção de documentos"""
    db = MongoDB.get_database()
    return db["documents"]

from typing import List, Dict, Optional
import numpy as np
from langchain.embeddings import OpenAIEmbeddings
import logging
from pymongo import MongoClient
from datetime import datetime

logger = logging.getLogger(__name__)

class EmbeddingsManager:
    """Gerencia a criação e armazenamento de embeddings."""
    
    def __init__(
        self,
        mongodb_uri: str,
        database_name: str = "getai",
        collection_name: str = "embeddings",
        embedding_model: str = "text-embedding-ada-002"
    ):
        """
        Inicializa o gerenciador de embeddings.
        
        Args:
            mongodb_uri: URI do MongoDB
            database_name: Nome do banco de dados
            collection_name: Nome da coleção
            embedding_model: Modelo de embedding da OpenAI
        """
        self.client = MongoClient(mongodb_uri)
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        
        # Criar índices
        self.collection.create_index([("embedding", "2dsphere")])
        self.collection.create_index("file_path")
        self.collection.create_index("chunk_id")

    def create_embedding(self, text: str) -> List[float]:
        """
        Cria embedding para um texto.
        
        Args:
            text: Texto para criar embedding
            
        Returns:
            Lista de floats representando o embedding
        """
        try:
            embedding = self.embeddings.embed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"Erro ao criar embedding: {str(e)}")
            raise

    def store_embeddings(self, chunks: List[Dict]) -> List[str]:
        """
        Armazena embeddings e chunks no MongoDB.
        
        Args:
            chunks: Lista de chunks processados
            
        Returns:
            Lista de IDs dos documentos armazenados
        """
        try:
            stored_ids = []
            for chunk in chunks:
                embedding = self.create_embedding(chunk['content'])
                
                doc = {
                    'content': chunk['content'],
                    'embedding': embedding,
                    'metadata': chunk['metadata'],
                    'created_at': datetime.utcnow()
                }
                
                result = self.collection.insert_one(doc)
                stored_ids.append(str(result.inserted_id))
            
            logger.info(f"Armazenados {len(stored_ids)} embeddings")
            return stored_ids
            
        except Exception as e:
            logger.error(f"Erro ao armazenar embeddings: {str(e)}")
            raise

    def search_similar(
        self,
        query: str,
        max_results: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict]:
        """
        Busca chunks similares usando embeddings.
        
        Args:
            query: Texto da consulta
            max_results: Número máximo de resultados
            similarity_threshold: Limite mínimo de similaridade
            
        Returns:
            Lista de chunks similares com scores
        """
        try:
            query_embedding = self.create_embedding(query)
            
            # Busca por similaridade usando produto escalar
            pipeline = [
                {
                    "$addFields": {
                        "similarity": {
                            "$reduce": {
                                "input": {"$range": [0, {"$size": "$embedding"}]},
                                "initialValue": 0,
                                "in": {
                                    "$add": [
                                        "$$value",
                                        {"$multiply": [
                                            {"$arrayElemAt": ["$embedding", "$$this"]},
                                            {"$arrayElemAt": [query_embedding, "$$this"]}
                                        ]}
                                    ]
                                }
                            }
                        }
                    }
                },
                {"$match": {"similarity": {"$gt": similarity_threshold}}},
                {"$sort": {"similarity": -1}},
                {"$limit": max_results},
                {
                    "$project": {
                        "_id": 0,
                        "content": 1,
                        "metadata": 1,
                        "similarity": 1
                    }
                }
            ]
            
            results = list(self.collection.aggregate(pipeline))
            logger.info(f"Encontrados {len(results)} resultados similares")
            return results
            
        except Exception as e:
            logger.error(f"Erro na busca por similaridade: {str(e)}")
            raise

    def get_document_stats(self) -> Dict:
        """
        Retorna estatísticas sobre os documentos armazenados.
        
        Returns:
            Dicionário com estatísticas
        """
        try:
            stats = {
                'total_chunks': self.collection.count_documents({}),
                'unique_files': len(self.collection.distinct('metadata.file_path')),
                'file_types': self.collection.distinct('metadata.file_type')
            }
            return stats
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {str(e)}")
            raise

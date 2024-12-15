from typing import List, Optional
import numpy as np
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pymongo import MongoClient
import os

from src.config import (
    MONGODB_URI,
    MONGODB_DB_NAME,
    MONGODB_COLLECTION_NAME,
    VECTOR_INDEX_NAME,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    validate_config
)

class RAGAgent:
    def __init__(self):
        # Valida as configurações
        validate_config()
            
        # Inicializa conexão com MongoDB
        self.client = MongoClient(MONGODB_URI)
        self.db = self.client[MONGODB_DB_NAME]
        self.collection = self.db[MONGODB_COLLECTION_NAME]
        
        # Configurações do RAG
        self.embeddings = OpenAIEmbeddings(openai_api_key=os.environ.get('OPENAI_API_KEY'))
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
        )
        
    def add_documents(self, texts: List[str], metadatas: Optional[List[dict]] = None) -> None:
        """
        Adiciona documentos ao vector store para posterior recuperação.
        
        Args:
            texts: Lista de textos para adicionar
            metadatas: Lista opcional de metadados para cada texto
        """
        # Prepara os documentos
        documents = [Document(page_content=text) for text in texts]
        if metadatas:
            for doc, metadata in zip(documents, metadatas):
                doc.metadata = metadata
                
        # Divide em chunks
        chunks = self.text_splitter.split_documents(documents)
        
        # Gera embeddings e insere no MongoDB
        for chunk in chunks:
            # Gera embedding
            embedding = self.embeddings.embed_query(chunk.page_content)
            
            # Prepara documento para inserção
            doc = {
                "text": chunk.page_content,
                "metadata": chunk.metadata,
                "embedding": embedding
            }
            
            # Insere no MongoDB
            self.collection.insert_one(doc)
            
    def search(self, query: str, k: int = 3) -> List[Document]:
        """
        Busca os documentos mais relevantes para uma query.
        
        Args:
            query: Texto da busca
            k: Número de documentos para retornar
            
        Returns:
            Lista de documentos mais relevantes
        """
        # Gera embedding da query
        query_embedding = self.embeddings.embed_query(query)
        
        # Busca documentos similares usando o operador $vectorSearch
        pipeline = [
            {
                "$vectorSearch": {
                    "index": VECTOR_INDEX_NAME,
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": k * 10,  # Busca mais candidatos para melhor precisão
                    "limit": k
                }
            },
            {
                "$project": {
                    "text": 1,
                    "metadata": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]
        
        results = list(self.collection.aggregate(pipeline))
        
        # Converte resultados para Documents
        documents = []
        for result in results:
            doc = Document(
                page_content=result["text"],
                metadata={
                    **result.get("metadata", {}),
                    "score": result.get("score", 0)
                }
            )
            documents.append(doc)
            
        return documents
    
    def clear(self) -> None:
        """Limpa todos os documentos do vector store."""
        self.collection.delete_many({})
        
    def __del__(self):
        """Fecha a conexão com o MongoDB quando o objeto é destruído."""
        if hasattr(self, 'client'):
            self.client.close()

from typing import List, Dict, Optional, Union
import os
from datetime import datetime
import logging
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from .document_processor import DocumentProcessor
from .embeddings_manager import EmbeddingsManager

logger = logging.getLogger(__name__)

class RAGEngine:
    """Motor principal do sistema RAG."""
    
    def __init__(
        self,
        mongodb_uri: str,
        openai_api_key: Optional[str] = None,
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 500
    ):
        """
        Inicializa o motor RAG.
        
        Args:
            mongodb_uri: URI do MongoDB
            openai_api_key: Chave da API OpenAI
            model_name: Nome do modelo LLM
            temperature: Temperatura para geração
            max_tokens: Máximo de tokens na resposta
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key não encontrada")

        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        self.document_processor = DocumentProcessor()
        self.embeddings_manager = EmbeddingsManager(mongodb_uri)
        
        # Template para geração de respostas
        self.response_template = ChatPromptTemplate.from_messages([
            ("system", """Você é um assistente especializado em responder perguntas com base em documentos.
             Use as informações fornecidas para dar respostas precisas e relevantes.
             Se não tiver certeza ou se a informação não estiver nos documentos, seja honesto sobre isso.
             
             Contexto dos documentos:
             {context}"""),
            ("human", "{question}")
        ])

    def index_file(self, file_path: str) -> List[str]:
        """
        Indexa um arquivo no sistema RAG.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Lista de IDs dos chunks indexados
        """
        try:
            chunks = self.document_processor.process_file(file_path)
            chunk_ids = self.embeddings_manager.store_embeddings(chunks)
            logger.info(f"Arquivo indexado com sucesso: {file_path}")
            return chunk_ids
        except Exception as e:
            logger.error(f"Erro ao indexar arquivo: {str(e)}")
            raise

    def index_directory(
        self,
        directory_path: str,
        recursive: bool = True
    ) -> Dict[str, List[str]]:
        """
        Indexa um diretório no sistema RAG.
        
        Args:
            directory_path: Caminho do diretório
            recursive: Se deve processar subdiretórios
            
        Returns:
            Dicionário com caminhos dos arquivos e IDs dos chunks
        """
        try:
            chunks = self.document_processor.process_directory(
                directory_path,
                recursive=recursive
            )
            chunk_ids = self.embeddings_manager.store_embeddings(chunks)
            
            # Organiza os IDs por arquivo
            file_chunks = {}
            for chunk, chunk_id in zip(chunks, chunk_ids):
                file_path = chunk['metadata']['file_path']
                if file_path not in file_chunks:
                    file_chunks[file_path] = []
                file_chunks[file_path].append(chunk_id)
            
            logger.info(f"Diretório indexado com sucesso: {directory_path}")
            return file_chunks
        except Exception as e:
            logger.error(f"Erro ao indexar diretório: {str(e)}")
            raise

    async def query(
        self,
        question: str,
        max_results: int = 5,
        similarity_threshold: float = 0.7
    ) -> Dict:
        """
        Realiza uma consulta no sistema RAG.
        
        Args:
            question: Pergunta do usuário
            max_results: Número máximo de resultados
            similarity_threshold: Limite mínimo de similaridade
            
        Returns:
            Dicionário com resposta e fontes
        """
        try:
            # Busca documentos similares
            similar_docs = self.embeddings_manager.search_similar(
                question,
                max_results=max_results,
                similarity_threshold=similarity_threshold
            )
            
            if not similar_docs:
                return {
                    "answer": "Desculpe, não encontrei informações relevantes para responder sua pergunta.",
                    "sources": []
                }
            
            # Prepara o contexto
            context = "\n\n".join([
                f"Documento {i+1}:\n{doc['content']}"
                for i, doc in enumerate(similar_docs)
            ])
            
            # Gera resposta
            response = await self.llm.agenerate([
                self.response_template.format_messages(
                    context=context,
                    question=question
                )
            ])
            
            answer = response.generations[0][0].text
            
            # Prepara as fontes
            sources = [
                {
                    "file_name": doc["metadata"]["file_name"],
                    "file_path": doc["metadata"]["file_path"],
                    "chunk_id": doc["metadata"]["chunk_id"],
                    "similarity": doc["similarity"]
                }
                for doc in similar_docs
            ]
            
            return {
                "answer": answer,
                "sources": sources
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar consulta: {str(e)}")
            raise

    def get_system_stats(self) -> Dict:
        """
        Retorna estatísticas do sistema RAG.
        
        Returns:
            Dicionário com estatísticas
        """
        try:
            stats = self.embeddings_manager.get_document_stats()
            stats.update({
                "chunk_size": self.document_processor.chunk_size,
                "chunk_overlap": self.document_processor.chunk_overlap,
                "supported_formats": list(self.document_processor.SUPPORTED_EXTENSIONS.keys())
            })
            return stats
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {str(e)}")
            raise

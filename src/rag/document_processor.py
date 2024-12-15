from typing import List, Dict, Optional
import os
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import (
    TextLoader,
    PDFMinerLoader,
    UnstructuredMarkdownLoader,
    CSVLoader,
    UnstructuredExcelLoader,
)
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Processa documentos para indexação no sistema RAG."""
    
    SUPPORTED_EXTENSIONS = {
        '.txt': TextLoader,
        '.pdf': PDFMinerLoader,
        '.md': UnstructuredMarkdownLoader,
        '.csv': CSVLoader,
        '.xlsx': UnstructuredExcelLoader,
        '.xls': UnstructuredExcelLoader
    }

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        encoding: str = 'utf-8'
    ):
        """
        Inicializa o processador de documentos.
        
        Args:
            chunk_size: Tamanho dos chunks de texto
            chunk_overlap: Sobreposição entre chunks
            encoding: Codificação dos arquivos de texto
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = encoding
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )

    def process_file(self, file_path: str) -> List[Dict]:
        """
        Processa um arquivo e retorna seus chunks.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Lista de chunks processados com metadados
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

            extension = file_path.suffix.lower()
            if extension not in self.SUPPORTED_EXTENSIONS:
                raise ValueError(f"Extensão não suportada: {extension}")

            loader_class = self.SUPPORTED_EXTENSIONS[extension]
            loader = loader_class(str(file_path))
            documents = loader.load()
            
            chunks = self.text_splitter.split_documents(documents)
            
            processed_chunks = []
            for i, chunk in enumerate(chunks):
                processed_chunks.append({
                    'content': chunk.page_content,
                    'metadata': {
                        **chunk.metadata,
                        'chunk_id': i,
                        'file_name': file_path.name,
                        'file_path': str(file_path),
                        'file_type': extension
                    }
                })
            
            logger.info(f"Arquivo processado com sucesso: {file_path}")
            return processed_chunks

        except Exception as e:
            logger.error(f"Erro ao processar arquivo {file_path}: {str(e)}")
            raise

    def process_directory(
        self,
        directory_path: str,
        recursive: bool = True
    ) -> List[Dict]:
        """
        Processa todos os arquivos suportados em um diretório.
        
        Args:
            directory_path: Caminho do diretório
            recursive: Se deve processar subdiretórios
            
        Returns:
            Lista de todos os chunks processados
        """
        try:
            directory_path = Path(directory_path)
            if not directory_path.exists():
                raise NotADirectoryError(f"Diretório não encontrado: {directory_path}")

            all_chunks = []
            pattern = '**/*' if recursive else '*'
            
            for ext in self.SUPPORTED_EXTENSIONS.keys():
                for file_path in directory_path.glob(f'{pattern}{ext}'):
                    chunks = self.process_file(str(file_path))
                    all_chunks.extend(chunks)
            
            logger.info(f"Diretório processado com sucesso: {directory_path}")
            return all_chunks

        except Exception as e:
            logger.error(f"Erro ao processar diretório {directory_path}: {str(e)}")
            raise

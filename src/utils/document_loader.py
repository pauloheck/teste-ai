import os
from typing import List, Tuple
from pathlib import Path

def load_documents(directory: str) -> List[Tuple[str, dict]]:
    """
    Carrega todos os documentos de texto de um diretório.
    
    Args:
        directory: Caminho para o diretório contendo os documentos
        
    Returns:
        Lista de tuplas (conteúdo, metadata)
    """
    documents = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(('.txt', '.md', '.py')):  # Adicione mais extensões conforme necessário
                file_path = Path(root) / file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        metadata = {
                            'source': str(file_path),
                            'filename': file,
                            'extension': file_path.suffix
                        }
                        documents.append((content, metadata))
                except Exception as e:
                    print(f"Erro ao ler arquivo {file_path}: {e}")
    
    return documents

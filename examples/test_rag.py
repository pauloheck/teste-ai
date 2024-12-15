import asyncio
import os
from dotenv import load_dotenv
from src.rag import RAGEngine

# Carregar variáveis de ambiente
load_dotenv()

# Configurar MongoDB e OpenAI
MONGODB_URI = os.getenv("MONGODB_URI")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

async def main():
    # Inicializar o motor RAG
    rag = RAGEngine(
        mongodb_uri=MONGODB_URI,
        openai_api_key=OPENAI_API_KEY
    )
    
    # Diretório com documentos de teste
    docs_dir = "./data/documents"
    
    try:
        # Indexar documentos
        print("\n1. Indexando documentos...")
        file_chunks = rag.index_directory(docs_dir)
        print(f"Documentos indexados: {len(file_chunks)} arquivos")
        
        # Obter estatísticas
        print("\n2. Estatísticas do sistema:")
        stats = rag.get_system_stats()
        print(f"Total de chunks: {stats['total_chunks']}")
        print(f"Arquivos únicos: {stats['unique_files']}")
        print(f"Tipos de arquivo: {stats['file_types']}")
        
        # Realizar algumas consultas
        queries = [
            "Qual é o prazo para reembolso de produtos físicos?",
            "Como solicito um reembolso?",
            "Quanto tempo leva para processar um reembolso?"
        ]
        
        print("\n3. Testando consultas:")
        for query in queries:
            print(f"\nPergunta: {query}")
            response = await rag.query(query)
            print(f"Resposta: {response['answer']}")
            print("\nFontes:")
            for source in response['sources']:
                print(f"- {source['file_name']} (similaridade: {source['similarity']:.2f})")
    
    except Exception as e:
        print(f"Erro: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())

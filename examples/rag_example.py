from src.agents.rag_agent import RAGAgent
from src.utils.document_loader import load_documents

def main():
    # Inicializa o agente RAG
    rag = RAGAgent()
    
    # Carrega documentos de exemplo
    docs_dir = "./data/documents"  # Ajuste o caminho conforme necessário
    documents = load_documents(docs_dir)
    
    if not documents:
        print("Nenhum documento encontrado para indexar!")
        return
        
    # Adiciona documentos ao RAG
    texts = [doc[0] for doc in documents]
    metadatas = [doc[1] for doc in documents]
    rag.add_documents(texts, metadatas)
    
    # Exemplo de busca
    while True:
        query = input("\nDigite sua pergunta (ou 'sair' para encerrar): ")
        if query.lower() == 'sair':
            break
            
        # Busca documentos relevantes
        results = rag.search(query)
        
        print("\nDocumentos mais relevantes encontrados:")
        for i, doc in enumerate(results, 1):
            print(f"\n--- Documento {i} ---")
            print(f"Fonte: {doc.metadata.get('source', 'Desconhecida')}")
            print(f"Conteúdo: {doc.page_content[:200]}...")

if __name__ == "__main__":
    main()

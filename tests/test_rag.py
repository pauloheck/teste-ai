from src.agents.rag_agent import RAGAgent

def main():
    # Criar instância do RAG
    rag = RAGAgent()

    # Dados de teste
    test_documents = [
        'Os épicos são usados para organizar grandes iniciativas de projeto em partes gerenciáveis.',
        'User stories são descrições curtas de funcionalidades do ponto de vista do usuário.',
        'Critérios de aceitação definem quando uma user story está completa.'
    ]

    # Adicionar documentos
    print('Adicionando documentos ao RAG...')
    rag.add_documents(test_documents)

    # Realizar uma busca
    query = 'Como user stories se relacionam com épicos?'
    print('\nRealizando busca para:', query)
    results = rag.search(query, k=2)

    # Mostrar resultados
    print('\nResultados encontrados:')
    for i, doc in enumerate(results, 1):
        print(f'\n{i}. Texto: {doc.text}')
        print(f'   Score: {doc.metadata.get("score", "N/A")}')

if __name__ == "__main__":
    main()

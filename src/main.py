import os
from fastapi import FastAPI
from src.agents.rag_agent import RAGAgent
from src.agents.epic_generator import EpicGenerator
from src.utils.document_loader import load_documents
from src.api.routers import epics

app = FastAPI(title="GetAI API")

# Register routers
app.include_router(epics.router, prefix="/api/epics", tags=["epics"])

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_main_menu():
    clear_screen()
    print("=== GetAI - Sistema Inteligente de Gestão de Projetos ===")
    print("1. Sistema RAG - Consulta de Documentos")
    print("2. Gerador de Épicos")
    print("3. Configurações")
    print("4. Sair")
    print("="*50)

def print_rag_menu():
    clear_screen()
    print("=== Sistema RAG (Retrieval-Augmented Generation) ===")
    print("1. Carregar e Indexar Documentos")
    print("2. Fazer Perguntas sobre os Documentos")
    print("3. Visualizar Documentos Carregados")
    print("4. Voltar ao Menu Principal")
    print("="*50)

def print_epic_menu():
    clear_screen()
    print("=== Gerador de Épicos ===")
    print("1. Gerar Novo Épico")
    print("2. Listar Épicos Existentes")
    print("3. Exportar Épicos")
    print("4. Voltar ao Menu Principal")
    print("="*50)

def print_config_menu():
    clear_screen()
    print("=== Configurações do Sistema ===")
    print("1. Configurar API Keys")
    print("2. Gerenciar Diretórios")
    print("3. Configurar Modelos de IA")
    print("4. Voltar ao Menu Principal")
    print("="*50)

def load_and_index_documents(rag):
    clear_screen()
    print("=== Carregando e Indexando Documentos ===")
    docs_dir = "./data/documents"
    
    if not os.path.exists(docs_dir):
        print(f"\nDiretório {docs_dir} não encontrado!")
        input("\nPressione Enter para continuar...")
        return False
        
    documents = load_documents(docs_dir)
    
    if not documents:
        print("\nNenhum documento encontrado para indexar!")
        input("\nPressione Enter para continuar...")
        return False
        
    texts = [doc[0] for doc in documents]
    metadatas = [doc[1] for doc in documents]
    rag.add_documents(texts, metadatas)
    
    print(f"\nForam carregados {len(documents)} documentos com sucesso!")
    input("\nPressione Enter para continuar...")
    return True

def ask_questions(rag):
    while True:
        clear_screen()
        print("=== Fazer Perguntas sobre os Documentos ===")
        print("\nDigite 'voltar' para retornar ao menu")
        
        query = input("\nSua pergunta: ")
        if query.lower() == 'voltar':
            break
            
        results = rag.search(query)
        
        print("\nDocumentos mais relevantes encontrados:")
        for i, doc in enumerate(results, 1):
            print(f"\nDocumento {i}:")
            print(f"Conteúdo: {doc.page_content[:200]}...")
            print(f"Fonte: {doc.metadata.get('source', 'Não especificada')}")
            print(f"Score: {doc.metadata.get('score', 0):.2f}")
        
        input("\nPressione Enter para continuar...")

def view_documents():
    clear_screen()
    print("=== Documentos Disponíveis ===")
    docs_dir = "./data/documents"
    
    if not os.path.exists(docs_dir):
        print(f"\nDiretório {docs_dir} não encontrado!")
        input("\nPressione Enter para continuar...")
        return
        
    files = os.listdir(docs_dir)
    if not files:
        print("\nNenhum documento encontrado no diretório!")
    else:
        print(f"\nDocumentos em {docs_dir}:")
        for i, file in enumerate(files, 1):
            print(f"{i}. {file}")
    
    input("\nPressione Enter para continuar...")

def generate_epic():
    clear_screen()
    print("=== Gerar Novo Épico ===")
    print("\nDescreva sua ideia para o épico:")
    idea = input("> ")
    
    try:
        generator = EpicGenerator()
        print("\nGerando épico...")
        epic = generator.generate(idea)
        
        print("\nÉpico gerado com sucesso!")
        print("=========================\n")
        print(epic.to_markdown())
        
    except Exception as e:
        print(f"\nErro ao gerar o épico: {str(e)}")
    
    input("\nPressione Enter para continuar...")

def handle_rag_menu():
    rag = RAGAgent()
    documents_loaded = False
    
    while True:
        print_rag_menu()
        choice = input("\nEscolha uma opção (1-4): ")
        
        if choice == '1':
            documents_loaded = load_and_index_documents(rag)
        elif choice == '2':
            if not documents_loaded:
                print("\nPor favor, carregue os documentos primeiro (opção 1)!")
                input("\nPressione Enter para continuar...")
                continue
            ask_questions(rag)
        elif choice == '3':
            view_documents()
        elif choice == '4':
            break
        else:
            print("\nOpção inválida!")
            input("\nPressione Enter para continuar...")

def handle_epic_menu():
    while True:
        print_epic_menu()
        choice = input("\nEscolha uma opção (1-4): ")
        
        if choice == '1':
            generate_epic()
        elif choice in ['2', '3']:
            print("\nFuncionalidade em desenvolvimento...")
            input("\nPressione Enter para continuar...")
        elif choice == '4':
            break
        else:
            print("\nOpção inválida!")
            input("\nPressione Enter para continuar...")

def handle_config_menu():
    while True:
        print_config_menu()
        choice = input("\nEscolha uma opção (1-4): ")
        
        if choice in ['1', '2', '3']:
            print("\nFuncionalidade em desenvolvimento...")
            input("\nPressione Enter para continuar...")
        elif choice == '4':
            break
        else:
            print("\nOpção inválida!")
            input("\nPressione Enter para continuar...")

def check_api_key():
    if not os.getenv("OPENAI_API_KEY"):
        print("Erro: OPENAI_API_KEY não encontrada nas variáveis de ambiente")
        print("Por favor, configure a chave da API no arquivo .env")
        return False
    return True

def main():
    """Sistema principal do GetAI."""
    if not check_api_key():
        return

    while True:
        print_main_menu()
        choice = input("\nEscolha uma opção (1-4): ")
        
        if choice == '1':
            handle_rag_menu()
        elif choice == '2':
            handle_epic_menu()
        elif choice == '3':
            handle_config_menu()
        elif choice == '4':
            print("\nObrigado por usar o GetAI!")
            break
        else:
            print("\nOpção inválida!")
            input("\nPressione Enter para continuar...")

if __name__ == "__main__":
    main()

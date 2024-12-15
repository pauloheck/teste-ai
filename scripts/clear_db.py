from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

# Pega a URI do MongoDB
mongodb_uri = os.getenv("MONGODB_URI")
print(f"Conectando ao MongoDB em: {mongodb_uri}")

try:
    # Conecta ao MongoDB
    client = MongoClient(mongodb_uri)
    
    # Verifica a conexão
    client.admin.command('ping')
    print("Conexão com MongoDB estabelecida com sucesso!")
    
    # Seleciona o banco de dados
    db = client.getai
    print("\nBanco de dados selecionado:", db.name)
    
    # Lista todas as collections
    collections = db.list_collection_names()
    print("\nCollections encontradas:", collections)
    
    # Limpa cada collection
    total_deleted = 0
    for collection in collections:
        count_before = db[collection].count_documents({})
        result = db[collection].delete_many({})
        count_after = db[collection].count_documents({})
        
        print(f"\nCollection {collection}:")
        print(f"- Documentos antes: {count_before}")
        print(f"- Documentos deletados: {result.deleted_count}")
        print(f"- Documentos depois: {count_after}")
        
        total_deleted += result.deleted_count
    
    print(f"\nTotal de documentos deletados: {total_deleted}")
    print("Operação concluída!")

except Exception as e:
    print(f"\nErro: {str(e)}")
    
finally:
    client.close()
    print("\nConexão fechada.")

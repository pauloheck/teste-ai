import os
from pathlib import Path
from dotenv import load_dotenv
import subprocess

def get_openai_api_key():
    """Obtém a chave API do OpenAI de forma segura."""
    try:
        # Tenta obter do ambiente primeiro
        api_key = os.environ.get('OPENAI_API_KEY')
        if api_key:
            return api_key

        # Se não encontrou, tenta via subprocess
        result = subprocess.run(['cmd', '/c', 'set', 'OPENAI_API_KEY'], capture_output=True, text=True)
        if result.stdout:
            api_key = result.stdout.strip().split('=')[1]
            # Define a variável de ambiente
            os.environ['OPENAI_API_KEY'] = api_key
            return api_key
    except Exception as e:
        print(f"Erro ao obter OPENAI_API_KEY: {e}")
    return None

# Configura a chave API do OpenAI
OPENAI_API_KEY = get_openai_api_key()
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY não encontrada. Por favor, configure a variável de ambiente.")

# Carrega outras variáveis do arquivo .env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Confirma o valor final da OPENAI_API_KEY
print(f"Valor final da OPENAI_API_KEY: {OPENAI_API_KEY[:10] if OPENAI_API_KEY else None}...")

# MongoDB Atlas
MONGODB_URI = os.environ.get('MONGODB_URI') or os.getenv('MONGODB_URI')
MONGODB_DB_NAME = os.environ.get('MONGODB_DB_NAME') or os.getenv('MONGODB_DB_NAME', 'rag_db')
MONGODB_COLLECTION_NAME = os.environ.get('MONGODB_COLLECTION_NAME') or os.getenv('MONGODB_COLLECTION_NAME', 'documents')

# Document Processing
CHUNK_SIZE = int(os.environ.get('CHUNK_SIZE') or os.getenv('CHUNK_SIZE', '1000'))
CHUNK_OVERLAP = int(os.environ.get('CHUNK_OVERLAP') or os.getenv('CHUNK_OVERLAP', '200'))

# Vector Search
VECTOR_INDEX_NAME = os.environ.get('VECTOR_INDEX_NAME') or os.getenv('VECTOR_INDEX_NAME', 'default')
EMBEDDING_DIMENSION =  1536

def validate_config():
    """Valida as configurações necessárias."""
    missing_vars = []
    
    if not OPENAI_API_KEY:
        missing_vars.append('OPENAI_API_KEY')
    if not MONGODB_URI:
        missing_vars.append('MONGODB_URI')
        
    if missing_vars:
        raise ValueError(
            f"Variáveis de ambiente necessárias não encontradas: {', '.join(missing_vars)}\n"
            "Por favor, copie o arquivo .env.example para .env e configure as variáveis necessárias."
        )

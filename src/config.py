"""
Main configuration file
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# MongoDB Atlas
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'ada')
MONGODB_COLLECTION_NAME = os.getenv('MONGODB_COLLECTION_NAME', 'documents')

# Document Processing
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '1000'))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '200'))

# Vector Search
VECTOR_INDEX_NAME = os.getenv('VECTOR_INDEX_NAME', 'default')
EMBEDDING_DIMENSION = 1536

# OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Azure OpenAI
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_MODEL = os.getenv('CHAT_MODEL_NAME', 'gpt-4')
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME = os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2023-05-15')

# Model Configuration
TEMPERATURE = float(os.getenv('TEMPERATURE', '0.7'))
MAX_TOKENS = int(os.getenv('MAX_TOKENS', '1000'))

def validate_config():
    """Valida as configurações necessárias."""
    missing_vars = []
    
    required_vars = {
        ('MONGODB_URI', MONGODB_URI),
        ('OPENAI_API_KEY', OPENAI_API_KEY),
        ('AZURE_OPENAI_API_KEY', AZURE_OPENAI_API_KEY),
        ('AZURE_OPENAI_ENDPOINT', AZURE_OPENAI_ENDPOINT),
        ('AZURE_OPENAI_DEPLOYMENT_NAME', AZURE_OPENAI_DEPLOYMENT_NAME),
        ('AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME', AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME),
    }
    
    for var_name, var_value in required_vars:
        if not var_value:
            missing_vars.append(var_name)
            
    if missing_vars:
        raise ValueError(
            f"Variáveis de ambiente necessárias não encontradas: {', '.join(missing_vars)}\n"
            "Por favor, copie o arquivo .env.example para .env e configure as variáveis necessárias."
        )

# Validate configuration on import
validate_config()

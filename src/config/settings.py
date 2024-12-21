"""
Configurações globais da aplicação
"""
from pydantic_settings import BaseSettings
from pydantic import validator
from functools import lru_cache

class Settings(BaseSettings):
    # Azure OpenAI
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_VERSION: str = "2023-05-15"
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-4"
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME: str = "text-embedding-ada-002"
    CHAT_MODEL_NAME: str = "gpt-4"
    EMBEDDING_MODEL_NAME: str = "text-embedding-ada-002"
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 4000

    # MongoDB
    MONGODB_URI: str
    MONGODB_DB_NAME: str
    MONGODB_COLLECTION_NAME: str

    # Vector Search
    VECTOR_SEARCH_TOP_K: int = 5
    VECTOR_SEARCH_SCORE_THRESHOLD: float = 0.7
    VECTOR_STORE_DIR: str = "data/vector_store"
    VECTOR_STORE_COLLECTION: str = "documents"

    # Aplicação
    APP_NAME: str = "ADA Dev"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Sistema Inteligente para Geração de Projetos"
    DEBUG: bool = False

    # Document Processing
    UPLOAD_DIR: str = "data/uploads"
    PROCESSED_DIR: str = "data/processed"
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB em bytes
    ALLOWED_EXTENSIONS: str = ".txt,.pdf,.md,.csv,.xlsx,.xls"
    
    @validator("MAX_UPLOAD_SIZE", pre=True)
    def validate_max_upload_size(cls, v):
        if isinstance(v, str):
            # Remove comentários e espaços
            v = v.split('#')[0].strip()
        try:
            return int(v)
        except (ValueError, TypeError):
            raise ValueError("MAX_UPLOAD_SIZE deve ser um número inteiro válido")

    class Config:
        env_file = ".env"
        case_sensitive = True
        env_nested_delimiter = "__"
        extra = "allow"

# Cria uma única instância das configurações
settings = Settings()

# Função para casos onde precisamos recarregar as configurações
@lru_cache()
def get_settings() -> Settings:
    """Retorna as configurações da aplicação"""
    return Settings()

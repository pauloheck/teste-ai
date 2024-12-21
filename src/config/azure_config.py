"""
Azure OpenAI Configuration
"""
from pydantic_settings import BaseSettings
from pydantic import Field

class AzureOpenAISettings(BaseSettings):
    """Azure OpenAI settings"""
    azure_openai_api_key: str = Field(..., env='AZURE_OPENAI_API_KEY')
    azure_openai_endpoint: str = Field(..., env='AZURE_OPENAI_ENDPOINT')
    azure_openai_deployment_name: str = Field(..., env='AZURE_OPENAI_DEPLOYMENT_NAME')
    azure_openai_api_version: str = Field('2023-05-15', env='AZURE_OPENAI_API_VERSION')
    azure_openai_embedding_deployment_name: str = Field(..., env='AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME')
    
    # Model configurations
    chat_model_name: str = Field('gpt-4', env='CHAT_MODEL_NAME')
    embedding_model_name: str = Field('text-embedding-ada-002', env='EMBEDDING_MODEL_NAME')
    temperature: float = Field(0.7, env='TEMPERATURE')
    max_tokens: int = Field(4000, env='MAX_TOKENS')

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignora campos extras

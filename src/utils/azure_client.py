"""
Azure OpenAI Client Utilities
"""
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from src.config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_MODEL,
    AZURE_OPENAI_DEPLOYMENT_NAME,
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME,
    AZURE_OPENAI_API_VERSION,
    TEMPERATURE,
    MAX_TOKENS
)
from src.aspects.azure_tracking import track_azure_call

@track_azure_call(operation="chat_completion", model="gpt-4")
async def get_azure_chat_model():
    """Get Azure OpenAI chat model"""
    return AzureChatOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        model=AZURE_OPENAI_MODEL,
        deployment_name=AZURE_OPENAI_DEPLOYMENT_NAME,
        api_version=AZURE_OPENAI_API_VERSION,
        temperature=float(TEMPERATURE),
        max_tokens=int(MAX_TOKENS),
    )

@track_azure_call(operation="embeddings", model="text-embedding-ada-002")
async def get_azure_embeddings():
    """Get Azure OpenAI embeddings model"""
    return AzureOpenAIEmbeddings(
        azure_deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME,
        openai_api_version=AZURE_OPENAI_API_VERSION,
        openai_api_key=AZURE_OPENAI_API_KEY,
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )

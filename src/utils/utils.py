"""
Utility functions for secure connections and configurations
"""
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from src.config.azure_config import AzureOpenAISettings
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

def get_mongodb_client(uri: str) -> MongoClient:
    """Get a secure MongoDB client"""
    return MongoClient(
        uri,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000
    )

def get_async_mongodb_client(uri: str) -> AsyncIOMotorClient:
    """Get a secure async MongoDB client"""
    return AsyncIOMotorClient(
        uri,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000
    )

def get_azure_chat_model() -> AzureChatOpenAI:
    """Get Azure OpenAI chat model with secure settings"""
    settings = AzureOpenAISettings()
    return AzureChatOpenAI(
        openai_api_key=settings.azure_openai_api_key,
        azure_endpoint=settings.azure_openai_endpoint,
        deployment_name=settings.azure_openai_deployment_name,
        openai_api_version=settings.azure_openai_api_version,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
    )

def get_azure_embeddings() -> AzureOpenAIEmbeddings:
    """Get Azure OpenAI embeddings model with secure settings"""
    settings = AzureOpenAISettings()
    return AzureOpenAIEmbeddings(
        azure_endpoint=settings.azure_openai_endpoint,
        azure_deployment=settings.azure_openai_embedding_deployment_name,
        openai_api_key=settings.azure_openai_api_key,
        openai_api_version=settings.azure_openai_api_version,
    )

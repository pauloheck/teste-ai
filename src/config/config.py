"""
Main configuration file
"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Main application settings"""
    # MongoDB
    mongodb_uri: str
    
    # Application
    debug: bool = False
    api_prefix: str = "/api"
    
    class Config:
        env_file = ".env"

settings = Settings()

# Export commonly used settings
MONGODB_URI = settings.mongodb_uri
DEBUG = settings.debug
API_PREFIX = settings.api_prefix

"""
Configuration settings for data acquisition engine.
"""
import os
from typing import Dict, Any
from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/dd_intelligence"
    redis_url: str = "redis://localhost:6379/0"
    
    # External APIs
    insee_api_key: str = ""
    openai_api_key: str = ""
    bloomberg_api_key: str = ""
    
    # Rate limiting
    default_rate_limit: int = 100  # requests per minute
    
    # Security
    secret_key: str = "your-secret-key-here"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()

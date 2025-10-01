"""
Configuration management for the SaaS LLM application.
Handles environment variables and application settings.
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database Configuration
    mongodb_url: str = Field(default="mongodb://localhost:27017", env="MONGODB_URL")
    mongodb_database: str = Field(default="saas_llm", env="MONGODB_DATABASE")
    chroma_db_path: str = Field(default="./chroma_db", env="CHROMA_DB_PATH")
    
    # LLM Configuration
    llm_api_url: str = Field(default="http://localhost:11434", env="LLM_API_URL")
    llm_model: str = Field(default="llama2", env="LLM_MODEL")
    
    # JWT Authentication
    jwt_secret_key: str = Field(default="dev-secret-key", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"], 
        env="API_CORS_ORIGINS"
    )
    
    # File Upload
    max_file_size_mb: int = Field(default=50, env="MAX_FILE_SIZE_MB")
    allowed_file_types: List[str] = Field(
        default=["application/pdf"], 
        env="ALLOWED_FILE_TYPES"
    )
    upload_dir: str = Field(default="./uploads", env="UPLOAD_DIR")
    
    # Embeddings
    embedding_model: str = Field(default="all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    chunk_size: int = Field(default=500, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=50, env="CHUNK_OVERLAP")
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields from environment
    
    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"
    
    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


# Global settings instance
settings = Settings()

# Create necessary directories
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs("chroma_db", exist_ok=True)

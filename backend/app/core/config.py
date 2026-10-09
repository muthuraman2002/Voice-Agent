import sys
import os
from pydantic_settings import BaseSettings
from typing import List

# Ensure project root is in Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/voice_agent"
    MONGODB_URL: str = "mongodb://localhost:27017/voice_agent"

    # JWT
    JWT_SECRET: str = "your-super-secret-jwt-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"
    OLLAMA_TEMPERATURE: float = 0.7
    OLLAMA_MAX_TOKENS: int = 2048

    # vLLM
    VLLM_BASE_URL: str = "http://localhost:8000"
    VLLM_MODEL: str = "qwen2.5:7b"

    # STT
    STT_MODEL: str = "base"
    STT_LANGUAGE: str = "en"
    STT_DEVICE: str = "cpu"

    # TTS
    TTS_MODEL: str = "en_US-lessac-medium"
    TTS_SPEED: float = 1.0

    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""
    QDRANT_COLLECTION: str = "documents"

    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    API_WORKERS: int = 1

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_FILE_TYPES: List[str] = ["pdf", "md", "txt", "docx"]

    # RAG
    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 50
    RAG_TOP_K: int = 5

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

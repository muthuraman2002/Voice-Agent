import sys
import os

# Add project root to Python path for AI module imports
# This must be done before any other imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api import voice, chat, documents
import logging

# Verify path is set
logging.info(f"Project root: {project_root}")
logging.info(f"sys.path[0]: {sys.path[0]}")
logging.info(f"ai directory exists: {os.path.exists(os.path.join(project_root, 'ai'))}")

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Voice Agent API")
    yield
    logger.info("Shutting down Voice Agent API")


# Create FastAPI app
app = FastAPI(
    title="AI Voice Agent API",
    description="Production-oriented AI Voice Agent Platform",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(voice.router, prefix="/api/voice", tags=["voice"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])


@app.get("/")
async def root():
    return {
        "message": "AI Voice Agent API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "voice-agent-api"
    }

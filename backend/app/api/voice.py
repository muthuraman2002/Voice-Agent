import sys
import os

# Ensure project root is in Python path BEFORE any other imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print(f"[voice.py] Project root: {project_root}")
print(f"[voice.py] sys.path[0]: {sys.path[0]}")
print(f"[voice.py] Can import ai: ", end="")
try:
    import ai
    print("YES")
except ImportError as e:
    print(f"NO - {e}")

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session
from app.core.auth import (
    User, consume_voice_request, get_current_user, get_db, require_plan,
    get_current_user_or_guest_dep, consume_guest_request
)
from app.services.voice_service import VoiceService
from app.core.config import settings

router = APIRouter()

# Lazy initialization of voice service (to avoid import issues at module load)
_voice_service = None


class TextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10_000)
    session_id: Optional[str] = Field(default=None, max_length=100)

def get_voice_service():
    """Get or create voice service instance"""
    global _voice_service
    if _voice_service is None:
        print(f"[get_voice_service] Creating VoiceService instance")
        print(f"[get_voice_service] OLLAMA_BASE_URL from settings: {settings.OLLAMA_BASE_URL}")
        print(f"[get_voice_service] OLLAMA_MODEL from settings: {settings.OLLAMA_MODEL}")
        _voice_service = VoiceService(
            stt_model=settings.STT_MODEL,
            stt_language=settings.STT_LANGUAGE,
            stt_device=settings.STT_DEVICE,
            ollama_base_url=settings.OLLAMA_BASE_URL,
            ollama_model=settings.OLLAMA_MODEL,
            ollama_timeout=settings.OLLAMA_TIMEOUT_SECONDS,
            tts_model=settings.TTS_MODEL
        )
    return _voice_service


@router.post("/process")
async def process_voice(
    audio: UploadFile = File(...),
    session_id: Optional[str] = Form(default=None),
    user_or_guest: tuple = Depends(get_current_user_or_guest_dep),
    database: Session = Depends(get_db),
):
    """
    Process voice audio: STT → LLM → TTS
    Supports both authenticated users and guest sessions.

    Args:
        audio: Audio file (WAV, WebM, etc.)
        session_id: Optional session ID for conversation context
        user_or_guest: Either User or GuestSession tuple
        database: Database session

    Returns:
        JSON with transcript, response, and audio URL
    """
    entity, is_guest = user_or_guest

    print(f"[API] Processing voice request", audio)
    try:
        # Get voice service (lazy initialization)
        voice_service = get_voice_service()

        # Read audio data
        audio_data = await audio.read()

        # Validate audio data
        if not audio_data:
            raise ValueError("No audio data received")
        if len(audio_data) < 100:
            raise ValueError("Audio data too small (possibly empty or corrupted)")

        print(f"[API] Received audio: {len(audio_data)} bytes, content-type: {audio.content_type}")

        # Consume request based on user type
        if is_guest:
            consume_guest_request(entity, database)
        else:
            consume_voice_request(entity, database)

        # Process through the pipeline
        result = await voice_service.process_audio(audio_data, session_id)
        print(result)
        return {
            "transcript": result["transcript"],
            "query": result["transcript"],
            "input_type": "voice",
            "session_id": result["session_id"],
            "response": result["response"],
            "audio_url": result.get("audio_url"),
            "latency_ms": result.get("latency_ms"),
            "timings": result.get("timings", {}),
            "guest": is_guest
        }
    except ValueError as e:
        print(f"[API] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        print(f"[API] LLM dependency error: {e}")
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        print(f"[API] Processing error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    print(f"[API] Processing voice request", audio)
    """
    Process voice audio: STT → LLM → TTS

    Args:
        audio: Audio file (WAV, WebM, etc.)

    Returns:
        JSON with transcript, response, and audio URL
    """
    try:
        # Get voice service (lazy initialization)
        voice_service = get_voice_service()

        # Read audio data
        audio_data = await audio.read()

        # Validate audio data
        if not audio_data:
            raise ValueError("No audio data received")
        if len(audio_data) < 100:
            raise ValueError("Audio data too small (possibly empty or corrupted)")

        print(f"[API] Received audio: {len(audio_data)} bytes, content-type: {audio.content_type}")

        # Process through the pipeline
        consume_voice_request(user, database)
        result = await voice_service.process_audio(audio_data, session_id)
        print(result)
        return {
            "transcript": result["transcript"],
            "query": result["transcript"],
            "input_type": "voice",
            "session_id": result["session_id"],
            "response": result["response"],
            "audio_url": result.get("audio_url"),
            "latency_ms": result.get("latency_ms"),
            "timings": result.get("timings", {})
        }
    except ValueError as e:
        print(f"[API] Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        # The LLM provider raises RuntimeError for an unreachable/misconfigured
        # Ollama instance. This is an upstream dependency failure, not a server
        # bug in the voice API.
        print(f"[API] LLM dependency error: {e}")
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        print(f"[API] Processing error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.post("/text")
async def process_text(
    request: TextRequest,
    user_or_guest: tuple = Depends(get_current_user_or_guest_dep),
    database: Session = Depends(get_db),
):
    """Process typed input through the same LLM/TTS pipeline as voice input. Supports both users and guests."""
    entity, is_guest = user_or_guest
    try:
        if is_guest:
            consume_guest_request(entity, database)
        else:
            consume_voice_request(entity, database)

        result = await get_voice_service().process_text(
            request.text, request.session_id
        )
        return {
            "transcript": result["transcript"],
            "query": result["transcript"],
            "input_type": "text",
            "session_id": result["session_id"],
            "response": result["response"],
            "audio_url": result.get("audio_url"),
            "latency_ms": result.get("latency_ms"),
            "timings": result.get("timings", {}),
            "guest": is_guest
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        print(f"[API] Text processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}") from e


@router.post("/session")
async def create_voice_session():
    """
    Create a new voice session for WebSocket streaming

    Returns:
        Session ID for WebSocket connection
    """
    voice_service = get_voice_service()
    session_id = voice_service.create_session()
    return {
        "session_id": session_id,
        "ws_url": f"ws://localhost:8000/api/voice/stream?session_id={session_id}"
    }


@router.get("/session/{session_id}")
async def get_voice_session(session_id: str):
    """Return the completed turns in a voice conversation session."""
    session = get_voice_service().get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"session_id": session_id, "turns": session["turns"]}

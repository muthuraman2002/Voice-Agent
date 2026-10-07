from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import io
import tempfile
import os
from app.services.voice_service import VoiceService
from app.core.config import settings

router = APIRouter()

# Initialize voice service
voice_service = VoiceService(
    stt_model=settings.STT_MODEL,
    stt_language=settings.STT_LANGUAGE,
    stt_device=settings.STT_DEVICE,
    ollama_base_url=settings.OLLAMA_BASE_URL,
    ollama_model=settings.OLLAMA_MODEL,
    tts_model=settings.TTS_MODEL
)


@router.post("/process")
async def process_voice(audio: UploadFile = File(...)):
    """
    Process voice audio: STT → LLM → TTS

    Args:
        audio: Audio file (WAV, WebM, etc.)

    Returns:
        JSON with transcript, response, and audio URL
    """
    try:
        # Read audio data
        audio_data = await audio.read()

        # Process through the pipeline
        result = await voice_service.process_audio(audio_data)

        return {
            "transcript": result["transcript"],
            "response": result["response"],
            "audio_url": result.get("audio_url"),
            "latency_ms": result.get("latency_ms")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session")
async def create_voice_session():
    """
    Create a new voice session for WebSocket streaming

    Returns:
        Session ID for WebSocket connection
    """
    session_id = voice_service.create_session()
    return {
        "session_id": session_id,
        "ws_url": f"ws://localhost:8000/api/voice/stream?session_id={session_id}"
    }

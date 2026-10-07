import time
import uuid
from typing import Dict, Any, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from ai.stt.providers.whisper import WhisperProvider
from ai.llm.providers.ollama import OllamaProvider
from ai.tts.providers.piper import PiperProvider
from ai.agent.graph.simple_agent import SimpleAgent


class VoiceService:
    """Service for orchestrating voice processing pipeline"""

    def __init__(
        self,
        stt_model: str = "base",
        stt_language: str = "en",
        stt_device: str = "cpu",
        ollama_base_url: str = "http://localhost:11434",
        ollama_model: str = "qwen2.5:7b",
        tts_model: str = "en_US-lessac-medium"
    ):
        """
        Initialize voice service with all providers

        Args:
            stt_model: Whisper model size
            stt_language: Language for STT
            stt_device: Device for STT
            ollama_base_url: Ollama API URL
            ollama_model: LLM model name
            tts_model: Piper TTS model
        """
        # Initialize STT provider
        self.stt_provider = WhisperProvider(
            model_size=stt_model,
            device=stt_device
        )

        # Initialize LLM provider
        self.llm_provider = OllamaProvider(
            base_url=ollama_base_url,
            model=ollama_model
        )

        # Initialize TTS provider
        try:
            self.tts_provider = PiperProvider(model=tts_model)
        except FileNotFoundError:
            print(f"Warning: Piper TTS model '{tts_model}' not found. TTS will be disabled.")
            self.tts_provider = None

        # Initialize agent
        self.agent = SimpleAgent(llm_provider=self.llm_provider)

        # Session management
        self.sessions: Dict[str, Dict[str, Any]] = {}

    async def process_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Process audio through the full pipeline: STT → LLM → TTS

        Args:
            audio_data: Raw audio bytes

        Returns:
            Dictionary with transcript, response, and audio
        """
        start_time = time.time()
        timings = {}

        try:
            # Step 1: Speech-to-Text
            stt_start = time.time()
            transcription = await self.stt_provider.transcribe(audio_data)
            timings["stt_latency_ms"] = (time.time() - stt_start) * 1000

            transcript = transcription.text

            if not transcript:
                return {
                    "transcript": "",
                    "response": "I couldn't hear anything. Please try again.",
                    "latency_ms": (time.time() - start_time) * 1000
                }

            # Step 2: Process with Agent (LLM)
            llm_start = time.time()
            agent_response = await self.agent.process(transcript)
            timings["llm_latency_ms"] = (time.time() - llm_start) * 1000

            response_text = agent_response.action.content

            # Step 3: Text-to-Speech
            audio_url = None
            if self.tts_provider:
                tts_start = time.time()
                try:
                    tts_result = await self.tts_provider.synthesize(response_text)
                    timings["tts_latency_ms"] = (time.time() - tts_start) * 1000

                    # Save audio to temp file and return URL
                    audio_url = await self._save_audio(tts_result.audio_data)
                except Exception as e:
                    print(f"TTS failed: {e}")
                    timings["tts_latency_ms"] = None

            # Calculate total latency
            timings["total_latency_ms"] = (time.time() - start_time) * 1000

            return {
                "transcript": transcript,
                "response": response_text,
                "audio_url": audio_url,
                "latency_ms": timings["total_latency_ms"],
                "timings": timings
            }
        except Exception as e:
            print(f"Error processing audio: {e}")
            raise

    async def _save_audio(self, audio_data: bytes) -> str:
        """
        Save audio data to temporary file

        Args:
            audio_data: Audio bytes

        Returns:
            URL to access the audio
        """
        import tempfile
        import aiofiles

        # Create temp file
        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False,
            dir="static/audio"
        ) as f:
            temp_path = f.name

        # Ensure static directory exists
        os.makedirs("static/audio", exist_ok=True)

        # Write audio data
        async with aiofiles.open(temp_path, 'wb') as f:
            await f.write(audio_data)

        # Return URL (in production, this would be a proper storage URL)
        filename = os.path.basename(temp_path)
        return f"/static/audio/{filename}"

    def create_session(self) -> str:
        """
        Create a new voice session for WebSocket streaming

        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "created_at": time.time(),
            "messages": []
        }
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        return self.sessions.get(session_id)

    def delete_session(self, session_id: str):
        """Delete session"""
        if session_id in self.sessions:
            del self.sessions[session_id]

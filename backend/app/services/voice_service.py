import time
import uuid
from typing import Dict, Any, Optional
import sys
import os

# Add project root to path for imports (must be done at module level)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Print for debugging
print(f"[VoiceService] Project root: {project_root}")
print(f"[VoiceService] AI dir exists: {os.path.exists(os.path.join(project_root, 'ai'))}")
print(f"[VoiceService] sys.path[0]: {sys.path[0] if sys.path else 'empty'}")
print(f"[VoiceService] Full sys.path: {sys.path[:5]}...")

# Try to import ai to verify it works
try:
    import ai
    print(f"[VoiceService] Successfully imported 'ai' module: {ai}")
except ImportError as e:
    print(f"[VoiceService] ERROR importing 'ai': {e}")
    print(f"[VoiceService] Listing files in project root: {os.listdir(project_root)}")


class VoiceService:
    """Service for orchestrating voice processing pipeline"""

    def __init__(
        self,
        stt_model: str = "base",
        stt_language: str = "en",
        stt_device: str = "cpu",
        ollama_base_url: str = "http://localhost:11435",
        ollama_model: str = "qwen2.5:0.5b",
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
        self.stt_model = stt_model
        self.stt_language = stt_language
        self.stt_device = stt_device
        self.ollama_base_url = ollama_base_url
        self.ollama_model = ollama_model
        self.tts_model = tts_model

        # Lazy initialization of providers
        self._stt_provider = None
        self._llm_provider = None
        self._tts_provider = None
        self._agent = None

        # Session management
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def _get_stt_provider(self):
        """Lazy load STT provider"""
        if self._stt_provider is None:
            # Ensure project root is in path (for uvicorn subprocesses)
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            from ai.stt.providers.whisper import WhisperProvider
            self._stt_provider = WhisperProvider(
                model_size=self.stt_model,
                device=self.stt_device
            )
        return self._stt_provider

    def _get_llm_provider(self):
        """Lazy load LLM provider"""
        if self._llm_provider is None:
            # Ensure project root is in path (for uvicorn subprocesses)
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            from ai.llm.providers.ollama import OllamaProvider
            self._llm_provider = OllamaProvider(
                base_url=self.ollama_base_url,
                model=self.ollama_model
            )
        return self._llm_provider

    def _get_tts_provider(self):
        """Lazy load TTS provider"""
        if self._tts_provider is None:
            try:
                # Ensure project root is in path (for uvicorn subprocesses)
                if project_root not in sys.path:
                    sys.path.insert(0, project_root)
                from ai.tts.providers.piper import PiperProvider
                self._tts_provider = PiperProvider(model=self.tts_model)
            except Exception as e:
                print(f"Warning: Could not initialize TTS provider: {e}")
                print("TTS will be disabled")
        return self._tts_provider

    def _get_agent(self):
        """Lazy load agent"""
        if self._agent is None:
            # Ensure project root is in path (for uvicorn subprocesses)
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            from ai.agent.graph.simple_agent import SimpleAgent
            self._agent = SimpleAgent(llm_provider=self._get_llm_provider())
        return self._agent

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
            stt_provider = self._get_stt_provider()
            transcription = await stt_provider.transcribe(audio_data)
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
            agent = self._get_agent()
            agent_response = await agent.process(transcript)
            timings["llm_latency_ms"] = (time.time() - llm_start) * 1000

            response_text = agent_response.action.content

            # Step 3: Text-to-Speech
            audio_url = None
            tts_provider = self._get_tts_provider()
            if tts_provider:
                tts_start = time.time()
                try:
                    tts_result = await tts_provider.synthesize(response_text)
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

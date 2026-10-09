import asyncio
import os
import tempfile
from typing import Optional, Dict, Any, AsyncIterator
from ai.tts.interfaces.base import TextToSpeechProvider, AudioGenerationResult


class PiperProvider(TextToSpeechProvider):
    """Piper TTS provider for fast neural text-to-speech"""

    def __init__(
        self,
        model: str = "en_US-lessac-medium",
        model_dir: Optional[str] = None,
        use_gpu: bool = False
    ):
        """
        Initialize Piper provider

        Args:
            model: Model name (e.g., 'en_US-lessac-medium')
            model_dir: Directory containing model files
            use_gpu: Whether to use GPU acceleration
        """
        self.model = model
        self.model_dir = model_dir or os.path.expanduser("~/.local/share/piper-voices")
        self.use_gpu = use_gpu
        self._check_model_available()

    def _check_model_available(self):
        """Check if the model is available"""
        model_path = os.path.join(self.model_dir, f"{self.model}.onnx")
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Piper model not found: {model_path}. "
                f"Please download the model using: "
                f"piper-tts download --model {self.model}"
            )

    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        **kwargs
    ) -> AudioGenerationResult:
        """
        Synthesize text to audio using Piper

        Args:
            text: Text to synthesize
            voice: Voice model to use (overrides default)
            speed: Speech speed multiplier
            **kwargs: Additional parameters

        Returns:
            AudioGenerationResult
        """
        model = voice or self.model

        # Run synthesis in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._synthesize_sync,
            text,
            model,
            speed,
            kwargs
        )

    def _synthesize_sync(
        self,
        text: str,
        model: str,
        speed: Optional[float],
        kwargs: dict
    ) -> AudioGenerationResult:
        """Synchronous synthesis helper"""
        try:
            from piper import PiperVoice

            # Load model
            model_path = os.path.join(self.model_dir, f"{model}.onnx")
            config_path = os.path.join(self.model_dir, f"{model}.onnx.json")

            voice = PiperVoice.load(model_path, config_path)

            # Synthesize
            if speed is not None:
                # Adjust synthesis speed
                audio_bytes = voice.synthesize(text, speed=speed)
            else:
                audio_bytes = voice.synthesize(text)

            # Get audio duration (approximate)
            duration = len(audio_bytes) / (voice.config.sample_rate * 2)  # 16-bit audio

            return AudioGenerationResult(
                audio_data=audio_bytes,
                format="wav",
                duration=duration,
                metadata={
                    "model": model,
                    "sample_rate": voice.config.sample_rate,
                    "speed": speed or 1.0
                }
            )
        except ImportError:
            raise RuntimeError(
                "Piper TTS not installed. Install with: pip install piper-tts"
            )
        except Exception as e:
            raise RuntimeError(f"Piper synthesis failed: {e}")

    async def synthesize_stream(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        **kwargs
    ) -> AsyncIterator[bytes]:
        """
        Synthesize text to audio with streaming

        Note: Piper doesn't natively support streaming, so this will
        synthesize the full text and yield it in chunks.

        Args:
            text: Text to synthesize
            voice: Voice model to use
            speed: Speech speed multiplier
            **kwargs: Additional parameters

        Yields:
            Audio chunks
        """
        result = await self.synthesize(text, voice, speed, **kwargs)

        # Yield in chunks
        chunk_size = 4096  # 4KB chunks
        audio_data = result.audio_data

        for i in range(0, len(audio_data), chunk_size):
            yield audio_data[i:i + chunk_size]

    def get_available_voices(self) -> list[str]:
        """Get list of available Piper voices"""
        voices = []

        if os.path.exists(self.model_dir):
            for file in os.listdir(self.model_dir):
                if file.endswith(".onnx"):
                    voice_name = file.replace(".onnx", "")
                    voices.append(voice_name)

        return voices

    async def download_model(self, model: str):
        """
        Download a Piper model

        Args:
            model: Model name to download
        """
        import subprocess

        # Create model directory if it doesn't exist
        os.makedirs(self.model_dir, exist_ok=True)

        # Run piper download command
        cmd = [
            "piper-tts",
            "download",
            "--model", model,
            "--download-dir", self.model_dir
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise RuntimeError(
                f"Failed to download model: {stderr.decode()}"
            )

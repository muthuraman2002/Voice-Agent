import asyncio
from typing import Optional
from faster_whisper import WhisperModel
import numpy as np
import io
import wave
from ai.stt.interfaces.base import SpeechToTextProvider, TranscriptionResult


class WhisperProvider(SpeechToTextProvider):
    """Whisper STT provider using faster-whisper"""

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8"
    ):
        """
        Initialize Whisper provider

        Args:
            model_size: Model size (tiny, base, small, medium, large)
            device: Device to run on (cpu, cuda)
            compute_type: Compute type (int8, int16, float16, float32)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load Whisper model"""
        try:
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load Whisper model: {e}")

    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        **kwargs
    ) -> TranscriptionResult:
        """
        Transcribe audio bytes to text

        Args:
            audio_data: Raw audio bytes (WAV format)
            language: Language code (e.g., 'en', 'es')
            **kwargs: Additional parameters

        Returns:
            TranscriptionResult
        """
        # Run transcription in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._transcribe_sync,
            audio_data,
            language,
            kwargs
        )

    def _transcribe_sync(
        self,
        audio_data: bytes,
        language: Optional[str],
        kwargs: dict
    ) -> TranscriptionResult:
        """Synchronous transcription helper"""
        try:
            # Convert bytes to audio data
            audio = self._convert_bytes_to_audio(audio_data)

            # Transcribe
            segments, info = self.model.transcribe(
                audio,
                language=language,
                **kwargs
            )

            # Collect results
            text_parts = []
            segment_data = []
            total_duration = 0

            for segment in segments:
                text_parts.append(segment.text)
                segment_data.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text
                })
                total_duration = max(total_duration, segment.end)

            full_text = " ".join(text_parts).strip()

            return TranscriptionResult(
                text=full_text,
                language=info.language,
                duration=total_duration,
                segments=segment_data,
                metadata={
                    "language_probability": info.language_probability,
                    "model_size": self.model_size
                }
            )
        except Exception as e:
            raise RuntimeError(f"Transcription failed: {e}")

    async def transcribe_file(
        self,
        file_path: str,
        language: Optional[str] = None,
        **kwargs
    ) -> TranscriptionResult:
        """
        Transcribe audio file to text

        Args:
            file_path: Path to audio file
            language: Language code
            **kwargs: Additional parameters

        Returns:
            TranscriptionResult
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._transcribe_file_sync,
            file_path,
            language,
            kwargs
        )

    def _transcribe_file_sync(
        self,
        file_path: str,
        language: Optional[str],
        kwargs: dict
    ) -> TranscriptionResult:
        """Synchronous file transcription helper"""
        try:
            segments, info = self.model.transcribe(
                file_path,
                language=language,
                **kwargs
            )

            text_parts = []
            segment_data = []
            total_duration = 0

            for segment in segments:
                text_parts.append(segment.text)
                segment_data.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text
                })
                total_duration = max(total_duration, segment.end)

            full_text = " ".join(text_parts).strip()

            return TranscriptionResult(
                text=full_text,
                language=info.language,
                duration=total_duration,
                segments=segment_data,
                metadata={
                    "language_probability": info.language_probability,
                    "model_size": self.model_size
                }
            )
        except Exception as e:
            raise RuntimeError(f"File transcription failed: {e}")

    def _convert_bytes_to_audio(self, audio_bytes: bytes) -> str:
        """
        Convert audio bytes to format accepted by Whisper

        Args:
            audio_bytes: Raw audio bytes

        Returns:
            Path to temporary audio file
        """
        import tempfile
        import os

        # Create temporary file
        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False
        ) as temp_file:
            temp_path = temp_file.name

        try:
            # Write audio data to temp file
            with wave.open(temp_path, 'wb') as wav_file:
                # Parse the input bytes as WAV
                audio_io = io.BytesIO(audio_bytes)
                with wave.open(audio_io, 'rb') as input_wav:
                    params = input_wav.getparams()
                    wav_file.setparams(params)
                    wav_file.writeframes(input_wav.readframes(params.nframes))

            return temp_path
        except Exception:
            # If it's not WAV, just write the bytes directly
            with open(temp_path, 'wb') as f:
                f.write(audio_bytes)
            return temp_path

    def get_supported_languages(self) -> list[str]:
        """Get list of supported languages"""
        # Whisper supports ~99 languages
        return [
            "en", "es", "fr", "de", "it", "pt", "nl", "pl", "ru", "ja",
            "ko", "zh", "ar", "hi", "tr", "vi", "th", "id", "ms", "sv",
            "da", "no", "fi", "el", "cs", "ro", "hu", "uk", "he", "fa"
        ]

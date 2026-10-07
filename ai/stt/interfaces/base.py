from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pydantic import BaseModel


class TranscriptionResult(BaseModel):
    """Result of speech-to-text transcription"""
    text: str
    language: str
    duration: float
    segments: Optional[list] = None
    metadata: Optional[Dict[str, Any]] = None


class SpeechToTextProvider(ABC):
    """Abstract base class for speech-to-text providers"""

    @abstractmethod
    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        **kwargs
    ) -> TranscriptionResult:
        """
        Transcribe audio data to text

        Args:
            audio_data: Raw audio bytes
            language: Language code (e.g., 'en', 'es')
            **kwargs: Additional provider-specific parameters

        Returns:
            TranscriptionResult with transcribed text and metadata
        """
        pass

    @abstractmethod
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
            language: Language code (e.g., 'en', 'es')
            **kwargs: Additional provider-specific parameters

        Returns:
            TranscriptionResult with transcribed text and metadata
        """
        pass

    @abstractmethod
    def get_supported_languages(self) -> list[str]:
        """
        Get list of supported language codes

        Returns:
            List of language codes
        """
        pass

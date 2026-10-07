from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, AsyncIterator
from pydantic import BaseModel


class AudioGenerationResult(BaseModel):
    """Result of text-to-speech generation"""
    audio_data: bytes
    format: str  # wav, mp3, etc.
    duration: float
    metadata: Optional[Dict[str, Any]] = None


class TextToSpeechProvider(ABC):
    """Abstract base class for text-to-speech providers"""

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        **kwargs
    ) -> AudioGenerationResult:
        """
        Synthesize text to audio

        Args:
            text: Text to synthesize
            voice: Voice/model to use
            speed: Speech speed multiplier
            **kwargs: Additional provider-specific parameters

        Returns:
            AudioGenerationResult with audio data
        """
        pass

    @abstractmethod
    async def synthesize_stream(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        **kwargs
    ) -> AsyncIterator[bytes]:
        """
        Synthesize text to audio with streaming

        Args:
            text: Text to synthesize
            voice: Voice/model to use
            speed: Speech speed multiplier
            **kwargs: Additional provider-specific parameters

        Yields:
            Audio chunks as they are generated
        """
        pass

    @abstractmethod
    def get_available_voices(self) -> list[str]:
        """
        Get list of available voices/models

        Returns:
            List of voice identifiers
        """
        pass

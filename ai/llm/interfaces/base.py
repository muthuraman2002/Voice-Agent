from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, AsyncIterator, List
from pydantic import BaseModel


class Message(BaseModel):
    """Chat message"""
    role: str  # system, user, assistant
    content: str
    metadata: Optional[Dict[str, Any]] = None


class ToolCall(BaseModel):
    """Tool/function call from LLM"""
    name: str
    arguments: Dict[str, Any]


class LLMResponse(BaseModel):
    """Response from LLM"""
    content: str
    finish_reason: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    metadata: Optional[Dict[str, Any]] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response from the LLM

        Args:
            messages: List of conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: List of available tools for function calling
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse with generated content
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response from the LLM

        Args:
            messages: List of conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: List of available tools for function calling
            **kwargs: Additional provider-specific parameters

        Yields:
            Content chunks as they are generated
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model

        Returns:
            Dictionary with model information
        """
        pass

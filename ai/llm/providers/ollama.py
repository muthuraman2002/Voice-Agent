import asyncio
import httpx
from typing import Optional, Dict, Any, AsyncIterator, List
from .interfaces.base import LLMProvider, LLMResponse, Message, ToolCall


class OllamaProvider(LLMProvider):
    """Ollama LLM provider for local inference"""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:7b",
        timeout: float = 120.0
    ):
        """
        Initialize Ollama provider

        Args:
            base_url: Ollama API base URL
            model: Model name to use
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.client = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=self.timeout)
        return self.client

    async def generate(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response from Ollama

        Args:
            messages: List of conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: List of available tools (function calling)
            **kwargs: Additional parameters

        Returns:
            LLMResponse
        """
        client = await self._get_client()

        # Convert messages to Ollama format
        ollama_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        # Build request payload
        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
            **kwargs
        }

        if temperature is not None:
            payload["options"] = payload.get("options", {})
            payload["options"]["temperature"] = temperature

        if max_tokens is not None:
            payload["options"] = payload.get("options", {})
            payload["options"]["num_predict"] = max_tokens

        # Add tools if provided (Ollama tool calling support)
        if tools:
            payload["tools"] = tools

        try:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            message = data.get("message", {})
            content = message.get("content", "")

            # Parse tool calls if present
            tool_calls = None
            if "tool_calls" in message:
                tool_calls = [
                    ToolCall(
                        name=tc.get("function", {}).get("name"),
                        arguments=tc.get("function", {}).get("arguments", {})
                    )
                    for tc in message["tool_calls"]
                ]

            return LLMResponse(
                content=content,
                finish_reason=data.get("done_reason"),
                tool_calls=tool_calls,
                metadata={
                    "model": self.model,
                    "eval_count": data.get("eval_count"),
                    "eval_duration": data.get("eval_duration"),
                    "load_duration": data.get("load_duration")
                }
            )
        except httpx.HTTPError as e:
            raise RuntimeError(f"Ollama API error: {e}")

    async def generate_stream(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response from Ollama

        Args:
            messages: List of conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: List of available tools
            **kwargs: Additional parameters

        Yields:
            Content chunks as they are generated
        """
        client = await self._get_client()

        # Convert messages to Ollama format
        ollama_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        # Build request payload
        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": True,
            **kwargs
        }

        if temperature is not None:
            payload["options"] = payload.get("options", {})
            payload["options"]["temperature"] = temperature

        if max_tokens is not None:
            payload["options"] = payload.get("options", {})
            payload["options"]["num_predict"] = max_tokens

        if tools:
            payload["tools"] = tools

        try:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = line
                            # Parse JSON response
                            import json
                            chunk = json.loads(data)

                            if "message" in chunk:
                                content = chunk["message"].get("content", "")
                                if content:
                                    yield content

                            # Check if done
                            if chunk.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
        except httpx.HTTPError as e:
            raise RuntimeError(f"Ollama streaming error: {e}")

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "provider": "ollama",
            "model": self.model,
            "base_url": self.base_url,
            "supports_streaming": True,
            "supports_tools": True
        }

    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()
            self.client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

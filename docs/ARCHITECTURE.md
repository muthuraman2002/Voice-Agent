# Voice Agent Architecture

## Overview

The AI Voice Agent Platform follows a modular, microservices-oriented architecture designed for low-latency voice interactions and production scalability.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                         │
│                    Next.js + React + TypeScript              │
│                     (Web Audio API / WebRTC)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                    WebSocket
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    Nginx Reverse Proxy                        │
│              (Load Balancing / SSL Termination)              │
└──────┬───────────────────────┬───────────────────────────────┘
       │                       │
       ▼                       ▼
┌──────────────┐      ┌──────────────┐
│   Frontend   │      │   Backend    │
│   Next.js    │      │   FastAPI    │
└──────────────┘      └──────┬───────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
         ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
         │   STT   │    │  Agent  │    │   TTS   │
         │ Whisper │    │  /LLM   │    │  Piper  │
         └─────────┘    └────┬────┘    └─────────┘
                              │
                       ┌──────▼───────┐
                       │     RAG      │
                       │    Qdrant    │
                       └──────┬───────┘
                              │
                       ┌──────▼───────┐
                       │ PostgreSQL /  │
                       │   MongoDB     │
                       └───────────────┘
```

## Component Responsibilities

### Frontend (Next.js)
- **Voice Recording**: MediaRecorder API for capturing microphone input
- **Audio Playback**: Web Audio API for playing TTS responses
- **Real-time Communication**: WebSocket for low-latency streaming
- **User Interface**: React components for voice controls and conversation display
- **State Management**: Zustand for client-side state
- **Authentication**: JWT token management

### Backend (FastAPI)
- **API Gateway**: RESTful and WebSocket endpoints
- **Orchestration**: Coordinates STT, LLM, and TTS services
- **Session Management**: Maintains conversation state
- **Authentication**: JWT validation and refresh tokens
- **Rate Limiting**: Request throttling and abuse prevention
- **Error Handling**: Structured error responses

### STT Service (Whisper)
- **Audio Processing**: Receives audio chunks from frontend
- **Transcription**: Converts speech to text using faster-whisper
- **Language Detection**: Auto-detects input language
- **Timestamping**: Provides word-level timestamps for VAD
- **Interface**: Abstracted behind SpeechToTextProvider

### LLM Service (Ollama/vLLM)
- **Inference**: Runs open-source LLMs (Qwen, Llama, Mistral)
- **Conversation Memory**: Maintains context across turns
- **Tool Calling**: Executes functions when needed
- **Streaming**: Provides token-by-token response streaming
- **Interface**: Abstracted behind LLMProvider

### TTS Service (Piper)
- **Synthesis**: Converts text to natural speech
- **Streaming**: Streams audio chunks for low latency
- **Voice Selection**: Multiple voice models available
- **Speed Control**: Adjustable speech rate
- **Interface**: Abstracted behind TextToSpeechProvider

### Agent Layer
- **Intent Understanding**: Determines user's goal
- **Tool Selection**: Decides which tools to invoke
- **Response Generation**: Crafts natural responses
- **Context Management**: Maintains conversation state
- **Tool Execution**: Runs functions and integrates results

### RAG System
- **Document Ingestion**: Loads and processes documents
- **Chunking**: Splits documents into manageable pieces
- **Embedding**: Converts text to vector representations
- **Retrieval**: Finds relevant context from Qdrant
- **Citation**: Sources information back to documents

### Database Layer
- **PostgreSQL**: Structured data (users, conversations, messages)
- **MongoDB**: Flexible metadata (agent runs, tool calls)
- **Redis**: Caching and rate limiting

## Data Flow

### Voice Request Flow

1. **User speaks** → Frontend captures audio via MediaRecorder
2. **Audio upload** → Frontend sends audio to backend via WebSocket/HTTP
3. **STT Processing** → Whisper transcribes audio to text
4. **Agent Processing** → Agent analyzes input and determines action
5. **LLM Generation** → LLM generates response (streaming)
6. **TTS Synthesis** → Piper converts response to audio
7. **Audio Playback** → Frontend plays audio via Web Audio API

### Latency Targets

- **STT**: < 500ms
- **LLM First Token**: < 800ms
- **TTS Start**: < 300ms
- **End-to-End**: < 2s (perceived)

## Provider Interfaces

All AI components are abstracted behind interfaces to enable easy replacement:

### SpeechToTextProvider
```python
async def transcribe(audio_data: bytes) -> TranscriptionResult
async def transcribe_file(file_path: str) -> TranscriptionResult
get_supported_languages() -> list[str]
```

### LLMProvider
```python
async def generate(messages: List[Message]) -> LLMResponse
async def generate_stream(messages: List[Message]) -> AsyncIterator[str]
get_model_info() -> Dict[str, Any]
```

### TextToSpeechProvider
```python
async def synthesize(text: str) -> AudioGenerationResult
async def synthesize_stream(text: str) -> AsyncIterator[bytes]
get_available_voices() -> list[str]
```

## Security Considerations

- **Authentication**: JWT with refresh tokens
- **Authorization**: Role-based access control
- **Rate Limiting**: Per-user request throttling
- **Input Validation**: Pydantic models for all inputs
- **Prompt Injection**: Separation of system instructions, user input, and retrieved context
- **RAG Access Control**: Document-level permissions
- **Secrets Management**: Environment variables only

## Scalability

### Horizontal Scaling
- Stateless services (API, STT, TTS) can scale horizontally
- Session state stored in Redis
- Load balancing via Nginx

### Vertical Scaling
- LLM services may require GPU resources
- STT/TTS benefit from GPU acceleration
- Database sizing based on user count

### Caching
- LLM responses cached for common queries
- RAG embeddings cached
- Static assets CDN cached

## Monitoring

### Metrics Tracked
- STT latency
- LLM first-token latency
- LLM total latency
- TTS latency
- End-to-end latency
- Token usage
- Error rates
- Active sessions

### Logging
- Structured JSON logs
- Correlation IDs for request tracing
- Log levels: DEBUG, INFO, WARNING, ERROR

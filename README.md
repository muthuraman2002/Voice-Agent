# AI Voice Agent Platform

A production-oriented, modular AI Voice Agent application using open-source technologies.

## Architecture Overview

```
┌──────────────┐
│   Next.js    │
│   Frontend   │
└──────┬───────┘
       │
WebSocket/WebRTC
       │
┌──────▼───────┐
│   FastAPI    │
│ API Gateway  │
└──────┬───────┘
       │
┌──────┼──────────────┐
│      │              │
┌────▼────┐ ┌────▼────┐ ┌────▼────┐
│   STT   │ │  Agent  │ │   TTS   │
│ Whisper │ │  /LLM   │ │  Piper  │
└─────────┘ └────┬────┘ └─────────┘
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

## Technology Stack

### Frontend
- Next.js 14+ with App Router
- React 18+
- TypeScript
- Tailwind CSS
- WebSocket / WebRTC
- Web Audio API / MediaRecorder

### Backend
- FastAPI
- Python 3.11+
- Pydantic for data validation
- Async/await patterns

### AI Components
- **STT**: faster-whisper (with interface for other providers)
- **LLM**: Qwen/Llama/Mistral via Ollama (dev) / vLLM (prod)
- **TTS**: Piper / Coqui TTS
- **RAG**: Qdrant + Sentence Transformers
- **Agent**: LangGraph / Custom orchestration

### Infrastructure
- Docker & Docker Compose
- Nginx reverse proxy
- Kubernetes (production)
- PostgreSQL (structured data)
- MongoDB (flexible metadata)

## Development Phases

### Phase 1 — Basic Voice Chat ✅
- Microphone → Whisper → LLM → Piper → Speaker
- End-to-end voice communication

### Phase 2 — Streaming
- WebSocket streaming
- Streaming STT, LLM, TTS
- Interruption handling

### Phase 3 — Agent
- Tool calling
- Agent state management
- Function execution
- Conversation memory

### Phase 4 — RAG
- Document upload
- Chunking & embeddings
- Qdrant integration
- Retrieval with citations

### Phase 5 — Production
- Docker & Kubernetes
- Monitoring & security
- CI/CD
- AWS deployment

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Docker & Docker Compose
- Ollama (for local LLM)

### Local Development

1. **Clone and setup**
```bash
git clone <repo-url>
cd voice-agent
cp .env.example .env
```

2. **Start services with Docker Compose**
```bash
docker compose up -d
```

3. **Install dependencies**
```bash
# Frontend
cd frontend
npm install

# Backend
cd ../backend
pip install -r requirements.txt
```

4. **Run frontend**
```bash
cd frontend
npm run dev
```

5. **Run backend**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Project Structure

```
voice-agent/
├── frontend/                 # Next.js frontend
│   ├── src/
│   │   ├── app/             # App Router pages
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom hooks
│   │   ├── lib/             # Utilities
│   │   └── types/           # TypeScript types
│   └── public/
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── api/             # API routes
│   │   ├── services/        # Business logic
│   │   ├── models/          # Database models
│   │   └── core/            # Core config
│   └── tests/
├── ai/                       # AI service modules
│   ├── stt/                 # Speech-to-Text
│   ├── llm/                 # LLM providers
│   ├── tts/                 # Text-to-Speech
│   ├── agent/               # Agent orchestration
│   ├── rag/                 # RAG system
│   └── tools/               # Agent tools
├── database/                 # Database schemas
├── infrastructure/           # Infrastructure configs
│   ├── docker/
│   ├── nginx/
│   └── kubernetes/
└── docs/                     # Documentation
```

## API Endpoints

### Authentication
- `POST /api/auth/login`
- `POST /api/auth/register`
- `POST /api/auth/refresh`

### Voice
- `POST /api/voice/session`
- `WS /api/voice/stream`

### Chat
- `POST /api/chat`
- `GET /api/conversations`
- `GET /api/conversations/{id}`

### RAG
- `POST /api/documents/upload`
- `POST /api/rag/index`
- `POST /api/rag/search`

### Models
- `GET /api/models`
- `POST /api/models/select`

## Configuration

See `.env.example` for all configuration options.

Key environment variables:
- `DATABASE_URL` - PostgreSQL connection string
- `MONGODB_URL` - MongoDB connection string
- `OLLAMA_BASE_URL` - Ollama endpoint
- `QDRANT_URL` - Qdrant vector database
- `JWT_SECRET` - JWT signing secret

## Security

- JWT authentication with refresh tokens
- Role-based authorization
- Rate limiting
- Input validation
- Prompt injection protection
- RAG document access control
- Secrets management

## Observability

Structured logging with tracking:
- STT latency
- LLM first-token latency
- TTS latency
- End-to-end latency
- Token usage
- Tool execution time
- Error rates

## License

MIT License - See LICENSE file

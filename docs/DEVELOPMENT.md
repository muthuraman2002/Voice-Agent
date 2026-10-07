# Development Guide

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker & Docker Compose
- Ollama (for local LLM)
- Git

### Initial Setup

1. **Clone the repository**
```bash
git clone <repo-url>
cd voice-agent
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start infrastructure services**
```bash
docker compose up -d postgres mongodb qdrant redis ollama
```

4. **Pull Ollama model**
```bash
docker exec -it voice-agent-ollama ollama pull qwen2.5:7b
```

5. **Install backend dependencies**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

6. **Install frontend dependencies**
```bash
cd frontend
npm install
```

### Running the Application

#### Development Mode

**Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

Access at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

#### Production Mode with Docker

```bash
docker compose up -d
```

## Project Structure

```
voice-agent/
├── frontend/              # Next.js frontend
│   ├── src/
│   │   ├── app/          # App Router pages
│   │   ├── components/   # React components
│   │   ├── hooks/        # Custom hooks
│   │   ├── lib/          # Utilities
│   │   └── types/        # TypeScript types
│   ├── public/           # Static assets
│   ├── package.json
│   └── tsconfig.json
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── services/    # Business logic
│   │   ├── models/      # Database models
│   │   └── core/        # Configuration
│   ├── requirements.txt
│   └── tests/
├── ai/                   # AI service modules
│   ├── stt/             # Speech-to-Text
│   │   ├── interfaces/  # Abstract interfaces
│   │   └── providers/   # Implementations
│   ├── llm/             # LLM providers
│   ├── tts/             # Text-to-Speech
│   ├── agent/           # Agent orchestration
│   ├── rag/             # RAG system
│   └── tools/           # Agent tools
├── infrastructure/      # Infrastructure configs
│   ├── docker/          # Dockerfiles
│   ├── nginx/           # Nginx config
│   └── kubernetes/      # K8s manifests
└── docs/                # Documentation
```

## Development Workflow

### Adding a New STT Provider

1. Create provider in `ai/stt/providers/your_provider.py`
2. Implement `SpeechToTextProvider` interface
3. Add provider selection logic in services
4. Add tests

### Adding a New LLM Provider

1. Create provider in `ai/llm/providers/your_provider.py`
2. Implement `LLMProvider` interface
3. Update configuration
4. Add documentation

### Adding a New Tool

1. Create tool in `ai/tools/builtin/your_tool.py`
2. Implement tool logic
3. Register tool in agent
4. Add tests

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Integration Tests
```bash
pytest tests/integration/
```

## Code Style

### Python
- Use Black for formatting
- Use Ruff for linting
- Use MyPy for type checking

```bash
black backend/
ruff check backend/
mypy backend/
```

### TypeScript
- Use ESLint
- Use Prettier

```bash
cd frontend
npm run lint
npm run type-check
```

## Debugging

### Backend
- Enable debug logging: `LOG_LEVEL=DEBUG`
- Use Python debugger: `import pdb; pdb.set_trace()`
- Check API docs at http://localhost:8000/docs

### Frontend
- Use React DevTools
- Check browser console
- Network tab for API calls

### AI Services
- Check Ollama logs: `docker logs voice-agent-ollama`
- Check Whisper model loading
- Verify audio format

## Common Issues

### Ollama Not Responding
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
docker restart voice-agent-ollama
```

### Whisper Model Not Found
```bash
# The model will be downloaded automatically on first use
# Or download manually:
python -c "from faster_whisper import WhisperModel; WhisperModel('base')"
```

### Piper TTS Model Not Found
```bash
# Download Piper model
piper-tts download --model en_US-lessac-medium
```

### Port Conflicts
- Change ports in `.env`
- Check with: `lsof -i :8000`

## Performance Optimization

### Reduce LLM Latency
- Use smaller models
- Enable GPU acceleration
- Use vLLM instead of Ollama for production

### Reduce TTS Latency
- Use smaller voice models
- Enable streaming
- Pre-load models

### Reduce STT Latency
- Use smaller Whisper models
- Enable GPU
- Stream audio processing

## Deployment

### Docker Deployment
```bash
docker compose -f docker-compose.prod.yml up -d
```

### Kubernetes Deployment
```bash
kubectl apply -f infrastructure/kubernetes/manifests/
```

See DEPLOYMENT.md for more details.

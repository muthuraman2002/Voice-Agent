# Phase 1 Setup Instructions

This document provides step-by-step instructions for setting up and running Phase 1 of the AI Voice Agent Platform.

## Phase 1 Scope

Phase 1 implements the basic voice chat pipeline:
- Microphone input → Whisper (STT) → LLM (Ollama) → Piper (TTS) → Speaker output

## Prerequisites

1. **Docker & Docker Compose**
   ```bash
   docker --version
   docker-compose --version
   ```

2. **Node.js 18+**
   ```bash
   node --version
   ```

3. **Python 3.11+**
   ```bash
   python3 --version
   ```

## Quick Start

### Option 1: Automated Setup

Run the setup script:
```bash
cd voice-agent
./setup.sh
```

### Option 2: Manual Setup

#### 1. Clone and Configure
```bash
cd voice-agent
cp .env.example .env
# Edit .env if needed (defaults should work for local development)
```

#### 2. Start Infrastructure Services
```bash
docker compose up -d postgres mongodb qdrant redis ollama
```

Wait for services to start (10-20 seconds).

#### 3. Pull Ollama Model
```bash
docker exec voice-agent-ollama ollama pull qwen2.5:0.5b 
```

This downloads the LLM model (~4GB for qwen2.5:0.5b ).

#### 4. Setup Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
mkdir -p static/audio
```

#### 5. Setup Frontend
```bash
cd frontend
npm install
```

## Running the Application

### Start Backend
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at http://localhost:8000
API documentation at http://localhost:8000/docs

### Start Frontend (in new terminal)
```bash
cd frontend
npm run dev
```

Frontend will be available at http://localhost:3000

## Testing Phase 1

1. Open http://localhost:3000 in your browser
2. Click the microphone button
3. Grant microphone permission when prompted
4. Speak something (e.g., "Hello, how are you?")
5. Wait for processing
6. You should see:
   - Your transcript displayed
   - AI response displayed
   - Audio response played (if TTS is configured)

## Troubleshooting

### Ollama Not Responding
```bash
# Check Ollama status
docker logs voice-agent-ollama

# Restart Ollama
docker restart voice-agent-ollama

# Re-pull model
docker exec voice-agent-ollama ollama pull qwen2.5:7b
```

### Whisper Model Not Found
The faster-whisper model will be downloaded automatically on first use from Hugging Face.

### Piper TTS Model Not Found
If you see a warning about Piper TTS model:
```bash
# Download Piper model (optional - TTS will work without it but audio won't play)
piper-tts download --model en_US-lessac-medium
```

Or set `TTS_MODEL` in `.env` to an available model.

### Port Already in Use
If port 8000 or 3000 is already in use:
```bash
# Check what's using the port
lsof -i :8000
lsof -i :3000

# Change ports in .env
API_PORT=8001
# And update frontend NEXT_PUBLIC_API_URL accordingly
```

### Backend Import Errors
If you see import errors for AI modules:
```bash
# Make sure you're running from the backend directory
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

The `voice_service.py` handles path resolution for AI modules.

### Frontend API Connection Errors
If the frontend can't connect to the backend:
1. Check backend is running: http://localhost:8000/health
2. Check `NEXT_PUBLIC_API_URL` in `.env` matches backend URL
3. Check CORS settings in backend config

## Phase 1 Limitations

Current limitations that will be addressed in later phases:

- No streaming (waits for full audio before processing)
- No interruption handling
- No conversation memory persistence
- No tool calling
- No RAG/knowledge base
- No authentication
- No WebSocket (uses HTTP upload)
- No VAD (Voice Activity Detection)

## Next Steps

After Phase 1 is working:

1. **Phase 2 - Streaming**: Implement WebSocket for real-time streaming
2. **Phase 3 - Agent**: Add tool calling and conversation memory
3. **Phase 4 - RAG**: Add document upload and knowledge base
4. **Phase 5 - Production**: Add Docker, Kubernetes, monitoring

See README.md for the full roadmap.

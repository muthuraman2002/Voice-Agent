# Project Structure

This document provides a detailed overview of the project structure and file organization.

## Root Directory

```
voice-agent/
├── README.md                    # Main project documentation
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── docker-compose.yml           # Docker Compose for local development
├── setup.sh                     # Automated setup script
├── PHASE1_SETUP.md             # Phase 1 setup instructions
├── PROJECT_STRUCTURE.md        # This file
│
├── frontend/                    # Next.js frontend application
│   ├── package.json            # Node dependencies
│   ├── tsconfig.json           # TypeScript configuration
│   ├── tailwind.config.ts      # Tailwind CSS configuration
│   ├── next.config.js          # Next.js configuration
│   ├── postcss.config.js       # PostCSS configuration
│   ├── .dockerignore           # Docker ignore rules
│   │
│   ├── src/
│   │   ├── app/                # Next.js App Router
│   │   │   ├── layout.tsx      # Root layout
│   │   │   ├── page.tsx        # Home page (voice UI)
│   │   │   └── globals.css     # Global styles
│   │   │
│   │   ├── components/         # React components
│   │   │   ├── VoiceRecorder.tsx   # Voice recording component
│   │   │   ├── AudioPlayer.tsx     # Audio playback component
│   │   │   ├── TranscriptDisplay.tsx # Transcript display
│   │   │   └── ResponseDisplay.tsx  # AI response display
│   │   │
│   │   ├── hooks/              # Custom React hooks
│   │   │   ├── useVoiceRecorder.ts  # Voice recording logic
│   │   │   ├── useWebSocket.ts      # WebSocket connection
│   │   │   └── useAudioPlayer.ts    # Audio playback logic
│   │   │
│   │   ├── lib/                # Utility functions
│   │   │   ├── api.ts          # API client
│   │   │   ├── audio.ts        # Audio utilities
│   │   │   └── utils.ts        # General utilities
│   │   │
│   │   └── types/              # TypeScript type definitions
│   │       ├── voice.ts        # Voice-related types
│   │       ├── chat.ts         # Chat-related types
│   │       └── api.ts          # API response types
│   │
│   └── public/                 # Static assets
│       └── audio/              # Generated audio files
│
├── backend/                     # FastAPI backend application
│   ├── requirements.txt        # Python dependencies
│   ├── .dockerignore           # Docker ignore rules
│   │
│   ├── app/
│   │   ├── main.py             # FastAPI application entry point
│   │   │
│   │   ├── api/                # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── voice.py        # Voice processing endpoints
│   │   │   ├── chat.py         # Chat endpoints (Phase 3)
│   │   │   ├── documents.py    # Document endpoints (Phase 4)
│   │   │   └── auth.py         # Authentication endpoints (Phase 5)
│   │   │
│   │   ├── services/           # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── voice_service.py  # Voice orchestration service
│   │   │   ├── chat_service.py   # Chat service
│   │   │   ├── auth_service.py   # Authentication service
│   │   │   └── rag_service.py    # RAG service
│   │   │
│   │   ├── models/             # Database models
│   │   │   ├── user.py         # User model
│   │   │   ├── conversation.py # Conversation model
│   │   │   ├── message.py      # Message model
│   │   │   └── document.py     # Document model
│   │   │
│   │   └── core/               # Core configuration
│   │       ├── __init__.py
│   │       ├── config.py       # Settings and configuration
│   │       ├── security.py     # Security utilities
│   │       └── logging.py      # Logging configuration
│   │
│   ├── static/                 # Static files (generated at runtime)
│   │   └── audio/              # TTS audio files
│   │
│   └── tests/                  # Backend tests
│       ├── test_voice.py
│       ├── test_chat.py
│       └── test_rag.py
│
├── ai/                          # AI service modules (shared)
│   ├── __init__.py
│   │
│   ├── stt/                    # Speech-to-Text
│   │   ├── __init__.py
│   │   ├── interfaces/
│   │   │   ├── __init__.py
│   │   │   └── base.py         # SpeechToTextProvider interface
│   │   └── providers/
│   │       ├── __init__.py
│   │       ├── whisper.py      # Whisper implementation
│   │       └── google.py       # Google STT (future)
│   │
│   ├── llm/                    # LLM providers
│   │   ├── __init__.py
│   │   ├── interfaces/
│   │   │   ├── __init__.py
│   │   │   └── base.py         # LLMProvider interface
│   │   └── providers/
│   │       ├── __init__.py
│   │       ├── ollama.py       # Ollama implementation
│   │       ├── vllm.py         # vLLM implementation
│   │       └── openai.py       # OpenAI-compatible (future)
│   │
│   ├── tts/                    # Text-to-Speech
│   │   ├── __init__.py
│   │   ├── interfaces/
│   │   │   ├── __init__.py
│   │   │   └── base.py         # TextToSpeechProvider interface
│   │   └── providers/
│   │       ├── __init__.py
│   │       ├── piper.py        # Piper implementation
│   │       └── coqui.py        # Coqui TTS (future)
│   │
│   ├── agent/                  # Agent orchestration
│   │   ├── __init__.py
│   │   ├── interfaces/
│   │   │   ├── __init__.py
│   │   │   └── base.py         # Agent interface
│   │   └── graph/
│   │       ├── __init__.py
│   │       ├── simple_agent.py # Simple LLM agent (Phase 1)
│   │       ├── tool_agent.py  # Tool-calling agent (Phase 3)
│   │       └── langgraph_agent.py # LangGraph agent (Phase 3)
│   │
│   ├── rag/                    # Retrieval-Augmented Generation
│   │   ├── __init__.py
│   │   ├── embeddings/
│   │   │   ├── sentence_transformers.py # Embedding generation
│   │   ├── retrieval/
│   │   │   ├── qdrant_retriever.py     # Vector retrieval
│   │   ├── indexing/
│   │   │   ├── document_loader.py      # Document loading
│   │   │   └── chunker.py              # Text chunking
│   │   └── prompts/
│   │       └── rag_prompt.py           # RAG prompts
│   │
│   └── tools/                  # Agent tools
│       ├── __init__.py
│       ├── builtin/
│       │   ├── calculator.py   # Calculator tool
│       │   ├── web_search.py   # Web search tool
│       │   └── database.py     # Database query tool
│       └── custom/             # Custom business tools
│
├── database/                    # Database schemas and migrations
│   ├── migrations/             # Database migration files
│   │   ├── 001_initial.sql
│   │   └── 002_add_documents.sql
│   └── seeds/                  # Seed data
│       └── initial_data.sql
│
├── infrastructure/              # Infrastructure configuration
│   ├── docker/
│   │   ├── frontend/
│   │   │   └── Dockerfile
│   │   ├── backend/
│   │   │   └── Dockerfile
│   │   ├── stt/
│   │   │   └── Dockerfile
│   │   ├── llm/
│   │   │   └── Dockerfile
│   │   ├── tts/
│   │   │   └── Dockerfile
│   │   ├── postgres/
│   │   │   └── Dockerfile
│   │   └── qdrant/
│   │       └── Dockerfile
│   │
│   ├── nginx/
│   │   └── conf/
│   │       └── nginx.conf      # Nginx configuration
│   │
│   └── kubernetes/             # Kubernetes manifests
│       ├── manifests/
│       │   ├── deployment.yaml
│       │   ├── service.yaml
│       │   ├── ingress.yaml
│       │   └── configmap.yaml
│       ├── configmaps/
│       │   └── app-config.yaml
│       └── secrets/
│           └── app-secrets.yaml
│
└── docs/                        # Documentation
    ├── ARCHITECTURE.md         # System architecture
    ├── DEVELOPMENT.md          # Development guide
    ├── DEPLOYMENT.md           # Deployment guide
    ├── API.md                  # API documentation
    └── CONTRIBUTING.md         # Contribution guidelines
```

## Key Design Principles

### Modularity
- Each AI component (STT, LLM, TTS) is abstracted behind an interface
- Providers can be swapped without changing core logic
- Services are independent and loosely coupled

### Separation of Concerns
- Frontend: UI and user interaction
- Backend: API and orchestration
- AI Modules: Provider-specific implementations
- Infrastructure: Deployment and networking

### Scalability
- Stateless services for horizontal scaling
- Microservices-ready architecture
- Containerized for easy deployment

### Extensibility
- Easy to add new providers
- Plugin-like tool system
- Configurable via environment variables

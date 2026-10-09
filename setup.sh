#!/bin/bash

# Voice Agent Setup Script
# This script sets up the development environment

set -e

echo "🎤 Setting up AI Voice Agent Platform..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

# Check for FFmpeg (required for faster-whisper)
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  FFmpeg not found. Some AI features may not work."
    echo "   Install with: sudo apt-get install ffmpeg (Linux)"
    echo "   See docs/SYSTEM_DEPENDENCIES.md for details"
fi

echo "✅ Prerequisites check passed"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your configuration before running the application"
else
    echo "✅ .env file already exists"
fi

# Start infrastructure services
echo "🐳 Starting infrastructure services (PostgreSQL, MongoDB, Qdrant, Redis, Ollama)..."
docker compose up -d postgres mongodb qdrant redis ollama

echo "⏳ Waiting for services to be ready..."
sleep 10

# Pull Ollama model
echo "🤖 Pulling Ollama model (qwen2.5:0.5b )..."
docker exec voice-agent-ollama ollama pull qwen2.5:0.5b

# Setup backend
echo "🐍 Setting up backend..."
cd backend

# Create virtual environment
if [ ! -d venv ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create static directory
mkdir -p static/audio

cd ..

# Setup frontend
echo "⚛️  Setting up frontend..."
cd frontend

# Install dependencies
echo "Installing Node dependencies..."
npm install

cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env with your configuration if needed"
echo "2. Start the backend:"
echo "   cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "3. Start the frontend (in another terminal):"
echo "   cd frontend && npm run dev"
echo "4. Open http://localhost:3000 in your browser"
echo ""
echo "📚 For more information, see docs/DEVELOPMENT.md"

# System Dependencies

This document lists the system dependencies required for running the Voice Agent platform.

## Linux (Ubuntu/Debian)

### Required for Backend

```bash
sudo apt-get update
sudo apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    gcc \
    g++ \
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libavdevice-dev \
    libavutil-dev \
    libavfilter-dev \
    libswscale-dev \
    libswresample-dev \
    pkg-config \
    libsndfile1
```

### Required for Frontend

- Node.js 18+ (install via nvm or download from nodejs.org)
- npm (comes with Node.js)

## macOS

### Required for Backend

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python3 ffmpeg pkg-config libsndfile
```

### Required for Frontend

```bash
brew install node
```

## Windows

### Required for Backend

1. Install Python 3.11+ from https://www.python.org/downloads/

2. Install FFmpeg:
   - Download from https://ffmpeg.org/download.html
   - Add to PATH

3. Install pkg-config:
   - Download from https://github.com/pkgconf/pkgconf/releases
   - Add to PATH

4. Install MinGW or Visual Studio Build Tools for compilation

### Required for Frontend

- Install Node.js 18+ from https://nodejs.org/

## Docker (Recommended)

The easiest way to avoid system dependency issues is to use Docker:

```bash
docker compose up -d
```

The Dockerfile includes all necessary system dependencies.

## Dependency Explanation

### FFmpeg Libraries
- `libavcodec-dev`: Audio/video codec library
- `libavformat-dev`: Audio/video container formats
- `libavdevice-dev`: Audio/video device library
- `libavutil-dev`: Utility functions
- `libavfilter-dev`: Audio/video filtering
- `libswscale-dev`: Image scaling
- `libswresample-dev`: Audio resampling

These are required by the `av` Python package (dependency of faster-whisper).

### libsndfile1
- Audio file I/O library
- Required for audio processing

### pkg-config
- Library compilation tool
- Required for building packages with native dependencies

## Troubleshooting

### "Package libavformat was not found"
Install FFmpeg development libraries as shown above.

### "pkg-config could not find libraries"
Ensure pkg-config is installed and libraries are in standard paths.

### Python version issues
Use Python 3.11+ for best compatibility:
```bash
python3 --version
```

### Virtual environment issues
Always use a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

## Docker Alternative

If you encounter persistent dependency issues, use Docker:

```bash
# Build and run all services
docker compose up -d

# Or build just the backend
docker compose build backend
docker compose up -d backend
```

This ensures all dependencies are correctly installed in an isolated environment.

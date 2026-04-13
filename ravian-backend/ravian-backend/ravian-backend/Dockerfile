# ---- Stage 1: Build dependencies ----
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build tools needed for compiling C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps into /build/.local
COPY requirements-prod.txt .
RUN pip install --no-cache-dir --user -r requirements-prod.txt

# ---- Stage 2: Production image (slim) ----
FROM python:3.11-slim

WORKDIR /app

# Install only runtime system libs (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Remove files not needed in production to save space
RUN rm -rf \
    .env .env.* \
    google-calendar-key.json \
    venv/ .venv/ \
    __pycache__/ \
    chroma_db/ \
    storage/documents/ \
    storage/audio/ \
    static/audio/ \
    *.pyc \
    tests/ \
    .git/

# Create required directories
RUN mkdir -p storage/audio/tts storage/documents chroma_db

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Start server - Railway injects PORT env var
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]

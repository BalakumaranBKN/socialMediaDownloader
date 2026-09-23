# =======================================================
# Stage 1: Build Angular Frontend
# =======================================================
FROM node:22-alpine AS frontend-builder
WORKDIR /build

COPY frontend/package*.json ./
RUN npm ci --legacy-peer-deps || npm install --legacy-peer-deps

COPY frontend/ ./
RUN npm run build

# =======================================================
# Stage 2: Python FastAPI Runtime with FFmpeg
# =======================================================
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    FRONTEND_DIST=/app/frontend_dist

WORKDIR /app

# Install system dependencies & FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./

# Copy built Angular frontend from stage 1
COPY --from=frontend-builder /build/dist/frontend/browser /app/frontend_dist

EXPOSE 8000

# Start Uvicorn on dynamic PORT (compatible with Render, Railway, Fly.io, Heroku)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

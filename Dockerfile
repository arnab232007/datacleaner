# ── DataCleaner Dockerfile ────────────────────────────────────────
# Multi-stage build: keeps final image lean.

# Stage 1: dependency builder
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev libssl-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt


# Stage 2: runtime image
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY backend/  ./backend/
COPY frontend/ ./frontend/
COPY .env.example .env

# Create runtime directories
RUN mkdir -p backend/uploads backend/cleaned_files backend/reports backend/logs

# Set working directory to backend so relative imports resolve
WORKDIR /app/backend

EXPOSE 5000

# Run with gunicorn in production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", \
     "--timeout", "120", "--log-level", "info", "app:create_app()"]

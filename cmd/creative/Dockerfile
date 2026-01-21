# SyncCreate™ Creative Engine - Dockerfile
# Multi-stage build for Python-based AI creative generation service

# Stage 1: Build environment
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime environment
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY synccreate.py .
COPY variant_strategy.py .
COPY variant_testing.py .
COPY variant_integration.py .
COPY variant_examples.py .
COPY vision_guard.py .
COPY vision_guard_integration.py .
COPY demo_vision_guard.py .
COPY server.py .
COPY __init__.py .

# Create output directories
RUN mkdir -p /app/output /app/cache

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/root/.local/bin:$PATH \
    PORT=8084 \
    SHIELD_URL=http://syncshield:8081/check \
    OUTPUT_DIR=/app/output \
    CACHE_DIR=/app/cache

# Expose port
EXPOSE 8084

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8084/health || exit 1

# Non-root user for security
RUN useradd -m -u 1000 synccreate && \
    chown -R synccreate:synccreate /app
USER synccreate

# Run the service
CMD ["python", "server.py"]

# =============================================================================
# LLM Gateway - Multi-stage Production Dockerfile
# =============================================================================
# Stage 1: Builder - Install dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip with longer timeout
RUN pip install --no-cache-dir --timeout=300 pip setuptools wheel

# Copy requirements
COPY requirements.txt .

# Pre-install dependencies into wheels for faster subsequent builds
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt || \
    pip install --no-cache-dir --timeout=300 -r requirements.txt

# =============================================================================
# Stage 2: Runtime - Minimal production image
FROM python:3.11-slim AS runtime

WORKDIR /app

# Security: Create non-root user
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy wheels from builder
COPY --from=builder /app/wheels /wheels

# Install from wheels (faster and more reliable)
RUN pip install --no-cache-dir --no-deps /wheels/*.whl 2>/dev/null || \
    pip install --no-cache-dir --timeout=300 --find-links=/wheels /wheels/*.whl || \
    pip install --no-cache-dir --timeout=300 -r /app/requirements.txt

# Copy application
COPY app/ ./app/

# Set ownership
RUN chown -R appuser:appgroup /app

USER appuser

# Environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# ==============================================================================
# DeploySafe Backend Dockerfile (Production-Grade)
# ==============================================================================
FROM python:3.11-slim as base

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install minimal OS runtime dependencies (git is required for repo inspection & cloning)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Create non-root user and application directories
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/data /app/chroma_db /app/cloned_repos /app/backend/app && \
    chown -R appuser:appuser /app

# Copy application source code
COPY --chown=appuser:appuser backend/app /app/backend/app
COPY --chown=appuser:appuser demo-repos /app/demo-repos

# Switch to non-root user
USER appuser

# Expose FastAPI port
EXPOSE 8000

# Healthcheck to verify service availability
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Launch uvicorn server bound to all interfaces
CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

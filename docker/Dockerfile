# DevAssist Docker Image
# Multi-stage build for efficient container

# Stage 1: Build dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY pyproject.toml .
COPY README.md .
COPY src/ src/

# Install dependencies
RUN pip install --no-cache-dir build && \
    python -m build --wheel && \
    pip install --no-cache-dir dist/*.whl

# Stage 2: Runtime image
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 devassist

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/devassist /usr/local/bin/devassist

# Set up working directory
RUN mkdir -p /app/.devassist_work && \
    chown -R devassist:devassist /app

USER devassist

# Environment variables
ENV DEVASSIST_WORK_DIR=/app/.devassist_work
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import devassist; print('OK')" || exit 1

# Default command
ENTRYPOINT ["devassist"]
CMD ["--help"]

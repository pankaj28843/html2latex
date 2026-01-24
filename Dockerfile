# =============================================================================
# Stage 1: Builder
# =============================================================================
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock README.md /app/
COPY src /app/src
COPY demo-app/pyproject.toml /app/demo-app/

# Install dependencies (use cache mount for faster rebuilds)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --package html2latex-demo

# Copy remaining project files
COPY . /app

# Install project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --package html2latex-demo

# =============================================================================
# Stage 2: Runtime
# =============================================================================
FROM python:3.14-slim-bookworm AS runtime

# OCI Image Format Specification labels
# https://github.com/opencontainers/image-spec/blob/main/annotations.md
LABEL org.opencontainers.image.title="html2latex-demo" \
      org.opencontainers.image.description="Demo Flask app for html2latex - Convert HTML to LaTeX" \
      org.opencontainers.image.source="https://github.com/pankaj28843/html2latex" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.vendor="Pankaj Kumar Singh"

# Install security updates
RUN apt-get update && apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy the virtual environment and application from builder
COPY --from=builder --chown=appuser:appgroup /app /app

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 15005

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:15005/')" || exit 1

CMD ["python", "demo-app/app.py"]

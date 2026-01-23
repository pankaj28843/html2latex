FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy project files for dependency installation
COPY pyproject.toml uv.lock README.md /app/
COPY src /app/src

# Install dependencies (use cache mount for faster rebuilds)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --group demo

# Copy remaining project files
COPY . /app

# Install project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --group demo

EXPOSE 15005

CMD ["uv", "run", "python", "demo-app/app.py"]

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

# Copy project files for dependency installation
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

EXPOSE 15005

CMD ["uv", "run", "--package", "html2latex-demo", "python", "demo-app/app.py"]

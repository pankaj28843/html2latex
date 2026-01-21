FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md /app/
RUN uv sync --locked --group demo

COPY . /app

EXPOSE 15005

CMD ["uv", "run", "python", "demo-app/app.py"]

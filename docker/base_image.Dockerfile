FROM python:3.14.0-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/root/.local/bin:$PATH"

# Системные зависимости + UV
RUN apt-get update && apt-get install -y --no-install-recommends curl build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/0.10.9/install.sh | sh
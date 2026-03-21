FROM python_uv_base_image:latest AS python_base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY src /app/src
COPY pyproject.toml uv.lock /app/

RUN uv sync
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

WORKDIR /app

# Copy metadata first to leverage Docker layer caching for dependencies
COPY pyproject.toml README.md ./

# Backend package must be present when building the wheel, so copy it
COPY backend ./backend

RUN pip install --upgrade pip && \
    pip install .[dev]

COPY frontend-htmx ./frontend-htmx

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

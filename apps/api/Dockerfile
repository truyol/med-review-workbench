FROM python:3.11-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build
COPY pyproject.toml ./
COPY app ./app
ARG INSTALL_POSTGRES=false
RUN if [ "$INSTALL_POSTGRES" = "true" ]; then \
      python -m pip wheel --wheel-dir /wheels ".[postgres]"; \
    else \
      python -m pip wheel --wheel-dir /wheels .; \
    fi

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=container \
    APP_DATABASE_URL=sqlite:////data/medreview.db \
    APP_STORAGE_ROOT=/data/uploads \
    APP_PREVIEW_ROOT=/data/previews

RUN groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid appuser --create-home appuser \
    && mkdir -p /app /data/uploads /data/previews \
    && chown -R appuser:appuser /app /data

WORKDIR /app
RUN --mount=type=bind,from=builder,source=/wheels,target=/wheels \
    python -m pip install --no-cache-dir --no-compile /wheels/*
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser migrations ./migrations

USER appuser
EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]

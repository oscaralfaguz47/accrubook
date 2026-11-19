# syntax=docker/dockerfile:1
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PORT=8000

# Pinned uv version for reproducible builds.
COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /uvx /bin/

WORKDIR /app

# Dependencies are installed before copying the source code, so this layer
# stays cached until pyproject.toml or uv.lock change.
# The venv lives in /opt/venv, outside /app, so a bind mount of the source
# code in development never hides it.
ARG INSTALL_DEV=false
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    if [ "$INSTALL_DEV" = "true" ]; then \
        uv sync --frozen --no-install-project; \
    else \
        uv sync --frozen --no-install-project --no-dev; \
    fi

COPY . .

# Never run the application as root.
RUN useradd --create-home --uid 1000 app && chown -R app:app /app
USER app

EXPOSE 8000

# Gunicorn binds to 0.0.0.0:$PORT when PORT is set (the hosting platform injects it).
CMD ["gunicorn", "config.wsgi:application", "--workers", "2", "--access-logfile", "-"]
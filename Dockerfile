# FastAPI backend. Used by docker-compose.yml (production, behind caddy) and
# docker-compose.dev.yml (which overrides the command to `fastapi dev`).
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    PATH="/app/.venv/bin:$PATH"

# Dependencies first so code changes don't reinstall them.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

COPY app/ ./app/

# SQLite lives here; compose mounts a volume and points DATABASE_URL at it.
RUN mkdir -p /data
VOLUME /data

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/')" || exit 1
# --proxy-headers so client IPs and https come from caddy's X-Forwarded-* headers.
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]

FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src/ src/

EXPOSE 3003

CMD ["uv", "run", "granian", "--interface", "wsgi", "--host", "0.0.0.0", "--port", "3003", "referee_dashboard.app:create_app"]

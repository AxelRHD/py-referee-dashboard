FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies only
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Run as non-root user
RUN useradd --create-home --uid 1000 app
USER app

# Source code mounted at /data/src via volume
ENV PYTHONPATH=/data/src

EXPOSE 3000

CMD ["uv", "run", "--no-project", "granian", "--interface", "wsgi", "--host", "0.0.0.0", "--port", "3000", "--factory", "referee_dashboard.app:create_app"]

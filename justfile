[private]
default:
    @just --list --unsorted

# ============================================================
# Development
# ============================================================

# Start dev server with auto-reload
[group('dev')]
dev:
    uv run flask --app referee_dashboard.app:create_app run --port 3003 --debug

# ============================================================
# Setup & Qualität
# ============================================================

# Sync dependencies
[group('quality')]
sync:
    uv sync

# Format code
[group('quality')]
fmt:
    uv run ruff format src/ tests/

# Lint code
[group('quality')]
lint:
    uv run ruff check src/ tests/

# Lint and fix
[group('quality')]
fix:
    uv run ruff check --fix src/ tests/

# ============================================================
# Test
# ============================================================

# Run tests
[group('test')]
test:
    uv run pytest

# ============================================================
# Datenbank
# ============================================================

# Initialize the database
[group('db')]
db-init:
    uv run python -c "from referee_dashboard.db import init_db; init_db()"

# Import games from Notion CSV export
[group('db')]
db-import csv:
    uv run python scripts/import_notion.py {{csv}}

# ============================================================
# Production
# ============================================================

# Start production server locally
[group('production')]
serve:
    uv run granian --interface wsgi --host 0.0.0.0 --port 3003 referee_dashboard.app:create_app

# ============================================================
# Deployment
# ============================================================

remote := "mimir"
appdata_dir := "/mnt/data/docker/appdata/referee-dashboard"

# Build Docker image locally
[group('deploy')]
build:
    docker build -t referee-dashboard .

# Upload source code to mimir
[group('deploy')]
deploy-src:
    scp -r src/ {{remote}}:{{appdata_dir}}/

# Push image to mimir
[group('deploy')]
deploy-image:
    docker save referee-dashboard | ssh {{remote}} docker load

# Full deploy: build + push image + upload source
[group('deploy')]
deploy: build deploy-image deploy-src

# Show container logs
[group('deploy')]
deploy-logs:
    gosctl run logs

# Show container status
[group('deploy')]
deploy-status:
    gosctl run status

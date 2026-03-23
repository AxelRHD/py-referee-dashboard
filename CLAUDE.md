# Referee Dashboard

## Stack
- Python 3.13, uv, just, asdf
- Flask + Plotly.js (basic) for inline charts
- SQLAlchemy ORM (via flask-sqlalchemy) — no raw SQL
- htpy for HTML generation — no Jinja templates
- Bootstrap 5.3 + Bootstrap Icons via CDN — no npm, no build step
- htmx for server-side filtering (games list)
- Alpine.js for theme toggle
- Plotly.js (basic) for inline charts
- SQLite database
- Nord theme with dark/light toggle (localStorage persistence)
- granian as production server (with `--factory` flag for app factory)
- Config via .env files (python-dotenv)
- Docker for deployment (image built locally, pushed to mimir)
- gosctl for remote task execution via SSH

## Project Layout
- `src/referee_dashboard/` — source root (src layout)
- `src/referee_dashboard/app.py` — Flask app factory + /health endpoint
- `src/referee_dashboard/db.py` — SQLAlchemy instance + init + position seeding
- `src/referee_dashboard/models.py` — ORM models (League, Team, Position, Game)
- `src/referee_dashboard/config.py` — Config dataclass from .env
- `src/referee_dashboard/validation.py` — form validation (validate_game/team/league)
- `src/referee_dashboard/export.py` — CSV/SQL export functions + SQLite dump
- `src/referee_dashboard/import_data.py` — SQL sanitizer + CSV/SQL import
- `src/referee_dashboard/routes/` — Flask blueprints (CRUD + dashboard + data)
- `src/referee_dashboard/routes/dashboard.py` — Dashboard with widget endpoints
- `src/referee_dashboard/routes/data.py` — Data management (import/export)
- `src/referee_dashboard/views/` — htpy view functions + shared components
- `src/referee_dashboard/views/components.py` — reusable form/table components
- `src/referee_dashboard/views/dashboard.py` — dashboard widgets (Plotly.js charts)
- `src/referee_dashboard/views/data.py` — data management page
- `src/referee_dashboard/static/css/nord.css` — Nord theme overrides for Bootstrap
- `scripts/import_notion.py` — import games from Notion CSV export

## Conventions
- Use `create_app()` factory pattern for Flask
- Database path from `DB_PATH` in .env (default: `referee.db`)
- All dates stored as ISO 8601 (YYYY-MM-DD)
- Season derived from game_date year (March–October within one calendar year)
- Currency formatted as German locale (comma decimal, dot thousands): `1.234,56 €`
- CSV export uses semicolons (`;`) as delimiter + UTF-8 BOM for Excel
- SQL import whitelist: only INSERT and CREATE TABLE allowed
- htmx for partial page updates (HX-Request header → return partial HTML)
- Dashboard widgets loaded via htmx lazy-loading (hx-trigger="load")
- ruff for formatting and linting
- `just dev` for development, `just serve` for local production

## Deployment
- Target: mimir (OpenMediaVault server with Docker)
- Image built locally, pushed via `docker save | ssh mimir docker load`
- Source code uploaded to appdata via scp (not baked into image)
- Container mounts appdata volume at `/data` (contains `src/` + `referee.db`)
- `PYTHONPATH=/data/src` for module resolution
- Container runs as non-root user (UID 1000)
- Container lifecycle managed via OMV Docker UI
- `just build` — build image locally
- `just deploy` — build + push image + upload source
- `just deploy-src` — upload source only (code changes)
- `just deploy-image` — push image only (dependency changes)
- `sctl.toml` — gosctl tasks for logs/status

## Models
- **League** — name, sorter, remarks
- **Team** — name, state (Bundesland), is_active, remarks
- **Position** — position (PK), long, sorter (seeded on init)
- **Game** — game_date, game_time, home_team, away_team, venue, league, position, referee_fee, travel_costs, km_driven, exhibition, remarks

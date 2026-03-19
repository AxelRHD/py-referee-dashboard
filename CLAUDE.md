# Referee Dashboard

## Stack
- Python 3.13, uv, just, asdf
- Flask + Dash (mounted on Flask at /dashboard/)
- SQLAlchemy ORM (via flask-sqlalchemy) — no raw SQL
- htpy for HTML generation — no Jinja templates
- Bootstrap 5.3 + Bootstrap Icons via CDN — no npm, no build step
- htmx for server-side filtering (games list)
- Alpine.js for theme toggle
- Plotly.js (basic) for inline charts
- SQLite database
- Nord theme with dark/light toggle (localStorage persistence)
- granian as production server
- Config via .env files (python-dotenv)

## Project Layout
- `src/referee_dashboard/` — source root (src layout)
- `src/referee_dashboard/app.py` — Flask app factory + Dash mount
- `src/referee_dashboard/db.py` — SQLAlchemy instance + init + position seeding
- `src/referee_dashboard/models.py` — ORM models (League, Team, Position, Game)
- `src/referee_dashboard/config.py` — Config dataclass from .env
- `src/referee_dashboard/routes/` — Flask blueprints (CRUD)
- `src/referee_dashboard/views/` — htpy view functions + shared components
- `src/referee_dashboard/views/components.py` — reusable form/table components
- `src/referee_dashboard/dashboard/` — Dash app (placeholder)
- `src/referee_dashboard/static/css/nord.css` — Nord theme overrides for Bootstrap
- `scripts/import_notion.py` — import games from Notion CSV export

## Conventions
- Use `create_app()` factory pattern for Flask
- Database path from `DB_PATH` in .env (default: `referee.db`)
- All dates stored as ISO 8601 (YYYY-MM-DD)
- Season derived from game_date year (March–October within one calendar year)
- Currency formatted as German locale (comma decimal, dot thousands): `1.234,56 €`
- htmx for partial page updates (HX-Request header → return partial HTML)
- ruff for formatting and linting
- `just dev` for development, `just serve` for production

## Models
- **League** — name, sorter, remarks
- **Team** — name, state (Bundesland), is_active, remarks
- **Position** — position (PK), long, sorter (seeded on init)
- **Game** — game_date, game_time, home_team, away_team, venue, league, position, referee_fee, travel_costs, km_driven, exhibition, remarks

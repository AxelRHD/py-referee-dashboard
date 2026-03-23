<p align="center">
  <img src="src/referee_dashboard/static/pfeife.png" alt="Referee Dashboard" width="96">
</p>

<h1 align="center">Referee Dashboard</h1>

<p align="center">
  Self-hosted dashboard for managing American Football referee assignments, fees, and statistics.
</p>

---

## Features

- **Game Management** — Track games with date, teams, venue, league, position, fees, and travel costs
- **Team & League Management** — Maintain teams (with Bundesland) and leagues with sorting
- **Dashboard** — Multi-year overview with interactive Plotly.js charts, filters, and statistics
- **Import / Export** — CSV and SQL export per entity, SQLite dump, file upload and direct paste import
- **Form Validation** — Server-side validation with inline error messages
- **Autocomplete** — Inline type-ahead for venue and Bundesland fields
- **Dark / Light Mode** — Nord theme with persistent toggle (localStorage)
- **Healthcheck** — `/health` endpoint for Docker container monitoring

## Screenshots

> *Coming soon*

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13, Flask, SQLAlchemy ORM |
| Frontend | htpy (HTML generation), Bootstrap 5.3, Bootstrap Icons |
| Interactivity | htmx, Alpine.js, Plotly.js |
| Database | SQLite |
| Server | granian (WSGI) |
| Deployment | Docker, gosctl, just |
| Theme | Nord color palette |

**No npm, no build step, no Jinja templates** — HTML is generated server-side with [htpy](https://htpy.dev), assets loaded via CDN.

## Prerequisites

- [Python 3.13](https://www.python.org/) (via [asdf](https://asdf-vm.com/))
- [uv](https://docs.astral.sh/uv/) — Python package manager
- [just](https://just.systems/) — command runner

## Getting Started

```bash
# Clone the repository
git clone git@github.com:AxelRHD/py-referee-dashboard.git
cd py-referee-dashboard

# Install dependencies
just sync

# Start development server
just dev
```

The app will be available at [http://localhost:8080](http://localhost:8080).

On first start, the database is created automatically with seeded referee positions (R, CJ, U, LJ, LM, BJ, FJ, SJ).

## Configuration

Configuration via `.env` file in the project root:

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_PATH` | `referee.db` | Path to SQLite database file |
| `PORT` | `8080` | Server port |
| `DEBUG` | `false` | Enable Flask debug mode |
| `SECRET_KEY` | `change-me-in-production` | Flask session secret key |

## Just Recipes

```
just --list
```

### Development

| Recipe | Description |
|--------|-------------|
| `just dev` | Start dev server with auto-reload |
| `just sync` | Install/sync dependencies |
| `just fmt` | Format code with ruff |
| `just lint` | Lint code with ruff |
| `just fix` | Lint and auto-fix |
| `just test` | Run tests with pytest |

### Database

| Recipe | Description |
|--------|-------------|
| `just db-init` | Initialize the database |
| `just db-import <csv>` | Import games from Notion CSV export |

### Deployment

| Recipe | Description |
|--------|-------------|
| `just build` | Build Docker image locally |
| `just deploy` | Full deploy: build + push image + sync source |
| `just deploy-src` | Sync source code to server |
| `just deploy-image` | Push Docker image to server |
| `just deploy-logs` | Show container logs |
| `just deploy-status` | Show container status |

## Deployment

The app is designed for self-hosting, e.g. on an OpenMediaVault (OMV) server with Docker.

### Architecture

```
Local (WSL)                          Server (e.g. OMV)
┌──────────────┐                     ┌──────────────────────────┐
│ docker build │──docker save/load──▶│ Docker image             │
│              │                     │                          │
│ rsync src/   │────────────────────▶│ appdata/                 │
│              │                     │   ├── src/               │
│              │                     │   ├── referee.db         │
│              │                     │   └── VERSION            │
└──────────────┘                     └──────────────────────────┘
```

- **Docker image** contains only Python + dependencies (no source code)
- **Source code** is synced separately to the appdata volume
- **Database** persists in the appdata volume
- **Container lifecycle** managed via OMV Docker UI

### Docker Compose

```yaml
services:
  referee-dashboard:
    image: referee-dashboard
    container_name: referee-dashboard
    restart: unless-stopped
    ports:
      - "3001:3000"
    volumes:
      - CHANGE_TO_COMPOSE_DATA_PATH/referee-dashboard:/data
    environment:
      - DB_PATH=/data/referee.db
      - SECRET_KEY=${SECRET_KEY}
```

### Version Tagging

The app displays its version in the navbar, derived from git tags:

```bash
git tag v0.2.0
just deploy    # VERSION file generated from git describe
```

- Tagged commit → `v0.2.0`
- Untagged commit → short commit hash (e.g. `a1b2c3d`)

## Data Management

### Export

Each list page (Games, Teams, Leagues) offers CSV and SQL export buttons. The data management page (`/data`) provides:

- **SQLite Dump** — Complete backup with schema and data
- **All Data Export** — INSERT statements for all tables in FK order

### Import

- **SQL** — Paste or upload INSERT/CREATE TABLE statements (DROP, DELETE, UPDATE are blocked)
- **CSV** — Upload or paste CSV data with German headers, auto-resolves team/league names to IDs

CSV format uses semicolons (`;`) as delimiters and UTF-8 with BOM for Excel compatibility.

## Project Structure

```
src/referee_dashboard/
├── app.py                 # Flask app factory + /health endpoint
├── config.py              # Config dataclass from .env
├── db.py                  # SQLAlchemy instance + init
├── models.py              # ORM models (League, Team, Position, Game)
├── validation.py          # Form validation functions
├── export.py              # CSV/SQL export + SQLite dump
├── import_data.py         # SQL sanitizer + CSV/SQL import
├── routes/
│   ├── dashboard.py       # Dashboard with widget endpoints
│   ├── data.py            # Data management (import/export)
│   ├── games.py           # Game CRUD + export
│   ├── teams.py           # Team CRUD + export
│   └── leagues.py         # League CRUD + export
├── views/
│   ├── components.py      # Reusable form/table components
│   ├── dashboard.py       # Dashboard widgets (Plotly.js charts)
│   ├── data.py            # Data management page
│   ├── games.py           # Game list + form views
│   ├── teams.py           # Team list + form views
│   ├── leagues.py         # League list + form views
│   └── layout.py          # Base page layout + navbar
└── static/
    ├── css/nord.css        # Nord theme overrides
    └── pfeife.png         # App icon
```

## License

Private project — not licensed for redistribution.

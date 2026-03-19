# Referee Dashboard — Project Spec

## Overview

A self-hosted personal dashboard for managing and analyzing American Football referee assignments.
Consists of two services:

- **Web app** — Dash (visualizations) mounted on Flask (CRUD), htpy for HTML generation
- **Telegram bot** — on-demand statistics as PNG or PDF

Hosted on `mimir` via Docker Compose.

---

## Architecture

```
docker-compose (mimir)
├── referee-app   :3003   # Python, Flask+Dash, read/write referee.db
├── telegram-bot          # Python, read-only referee.db
└── volume: referee-data/
    └── referee.db
```

### Tech Stack

| Component     | Stack                                                                    |
|---------------|--------------------------------------------------------------------------|
| Web App       | Python, Flask, Dash (mounted on Flask), htpy, Plotly                    |
| Telegram Bot  | Python, python-telegram-bot, matplotlib/kaleido (PNG), weasyprint (PDF) |
| Database      | SQLite with WAL mode                                                     |
| Hosting       | Docker Compose on mimir (Debian/OMV)                                     |

### App Structure Notes

- Dash mounted on Flask: `Dash(__name__, server=flask_app, url_base_pathname="/dashboard/")`
- Flask handles all CRUD routes (`/games`, `/teams`, `/leagues`)
- htpy for HTML generation — no Jinja templates
- Bootstrap via CDN, Alpine.js via CDN — no npm, no build step

---

## Database Schema

### WAL Mode

```sql
PRAGMA journal_mode = WAL;
```

### Table: leagues

```sql
CREATE TABLE leagues (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    state      TEXT    NOT NULL,
    remarks    TEXT,
    created_at TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TRIGGER leagues_updated_at
    AFTER UPDATE ON leagues
    WHEN NEW.updated_at = OLD.updated_at
    BEGIN
        UPDATE leagues SET updated_at = datetime('now', 'localtime') WHERE id = NEW.id;
    END;
```

### Table: teams

Teams are league- and season-agnostic. League and season context lives on `games`.

```sql
CREATE TABLE teams (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    remarks    TEXT,
    created_at TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TRIGGER teams_updated_at
    AFTER UPDATE ON teams
    WHEN NEW.updated_at = OLD.updated_at
    BEGIN
        UPDATE teams SET updated_at = datetime('now', 'localtime') WHERE id = NEW.id;
    END;
```

### Table: positions

Lookup table for referee positions. No timestamps needed.

```sql
CREATE TABLE positions (
    position TEXT    PRIMARY KEY,
    long     TEXT    NOT NULL,
    sorter   INTEGER NOT NULL UNIQUE
);

INSERT INTO positions (position, long, sorter) VALUES
    ('R',  'Referee',      10),
    ('CJ', 'Center Judge', 20),
    ('U',  'Umpire',       30),
    ('LJ', 'Line Judge',   40),
    ('LM', 'Linesman',     50),
    ('BJ', 'Back Judge',   60),
    ('FJ', 'Field Judge',  70),
    ('SJ', 'Side Judge',   80);
```

### Table: games

Season is derived from `game_date` via `strftime('%Y', game_date)`. The season runs
March through October within a single calendar year, so derivation is unambiguous.

```sql
CREATE TABLE games (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    game_date    TEXT    NOT NULL,              -- ISO 8601: YYYY-MM-DD
    game_time    TEXT,                          -- HH:MM, nullable
    home_team_id INTEGER NOT NULL REFERENCES teams(id),
    away_team_id INTEGER NOT NULL REFERENCES teams(id),
    league_id    INTEGER NOT NULL REFERENCES leagues(id),
    position     TEXT    NOT NULL REFERENCES positions(position),
    referee_fee  REAL    NOT NULL DEFAULT 0.0,  -- in EUR
    travel_costs REAL    NOT NULL DEFAULT 0.0,  -- in EUR
    km_driven    INTEGER NOT NULL DEFAULT 0,
    remarks      TEXT,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TRIGGER games_updated_at
    AFTER UPDATE ON games
    WHEN NEW.updated_at = OLD.updated_at
    BEGIN
        UPDATE games SET updated_at = datetime('now', 'localtime') WHERE id = NEW.id;
    END;
```

### Derived: season

Anywhere a season filter is needed:

```sql
CAST(strftime('%Y', game_date) AS INTEGER) AS season
```

---

## Telegram Bot

The bot is read-only on the database. Commands (examples, to be refined):

| Command          | Output       | Description                        |
|------------------|--------------|------------------------------------|
| `/season`        | PNG          | Full current season overview       |
| `/stats <month>` | PNG          | Games and fees for a given month   |
| `/fees`          | PNG or PDF   | Fee summary for current season     |
| `/games`         | Text or PNG  | Upcoming/recent games              |

---

## Open Questions / Later

- Auth for web frontend (single-user for now, but mimir is reachable from outside)
- `referee_fee` DEFAULT may need adjustment once typical fee amounts are known
- Multi-user / Verband use case deferred

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

POSITIONS_SEED = [
    ("R", "Referee", 10),
    ("CJ", "Center Judge", 20),
    ("U", "Umpire", 30),
    ("LJ", "Line Judge", 40),
    ("LM", "Linesman", 50),
    ("BJ", "Back Judge", 60),
    ("FJ", "Field Judge", 70),
    ("SJ", "Side Judge", 80),
]


def seed_positions():
    """Seed the positions table if empty."""
    from referee_dashboard.models import Position

    if not db.session.query(Position).first():
        for pos, long, sorter in POSITIONS_SEED:
            db.session.add(Position(position=pos, long=long, sorter=sorter))
        db.session.commit()


def init_app(app):
    """Initialize SQLAlchemy with the Flask app."""
    db.init_app(app)

    with app.app_context():
        import referee_dashboard.models  # noqa: F401

        db.create_all()
        _migrate_venue(db)
        seed_positions()


def _migrate_venue(database):
    """Migrate venue text field to venue_id FK."""
    conn = database.engine.raw_connection()
    cursor = conn.connection.cursor()

    # Check if games still has the old venue text column
    cursor.execute("PRAGMA table_info(games)")
    cols = {row[1]: row[2] for row in cursor.fetchall()}
    if "venue" not in cols or "venue_id" in cols:
        conn.close()
        return

    cursor.execute("PRAGMA foreign_keys=OFF")

    # Populate venues table from distinct venue strings
    cursor.execute("SELECT DISTINCT venue FROM games WHERE venue IS NOT NULL AND venue != ''")
    for (name,) in cursor.fetchall():
        cursor.execute(
            "INSERT OR IGNORE INTO venues (city, stadium, created_at, updated_at)"
            " VALUES (?, '', datetime('now'), datetime('now'))",
            (name,),
        )

    # Rebuild games table with venue_id instead of venue

    cursor.execute("""
        CREATE TABLE games_new (
            id INTEGER PRIMARY KEY,
            game_date VARCHAR NOT NULL,
            game_time VARCHAR,
            home_team_id INTEGER NOT NULL REFERENCES teams(id),
            away_team_id INTEGER NOT NULL REFERENCES teams(id),
            venue_id INTEGER REFERENCES venues(id),
            league_id INTEGER NOT NULL REFERENCES leagues(id),
            position VARCHAR NOT NULL REFERENCES positions(position),
            referee_fee REAL NOT NULL DEFAULT 0.0,
            travel_costs REAL NOT NULL DEFAULT 0.0,
            km_driven INTEGER NOT NULL DEFAULT 0,
            exhibition INTEGER NOT NULL DEFAULT 0,
            remarks VARCHAR DEFAULT '',
            created_at VARCHAR NOT NULL,
            updated_at VARCHAR NOT NULL
        )
    """)
    cursor.execute("""
        INSERT INTO games_new
            (id, game_date, game_time, home_team_id, away_team_id,
             venue_id, league_id, position, referee_fee, travel_costs,
             km_driven, exhibition, remarks, created_at, updated_at)
        SELECT g.id, g.game_date, g.game_time, g.home_team_id, g.away_team_id,
             v.id, g.league_id, g.position, g.referee_fee, g.travel_costs,
             g.km_driven, g.exhibition, g.remarks, g.created_at, g.updated_at
        FROM games g
        LEFT JOIN venues v ON v.city = g.venue
    """)
    cursor.execute("DROP TABLE games")
    cursor.execute("ALTER TABLE games_new RENAME TO games")
    cursor.execute("PRAGMA foreign_keys=ON")
    conn.connection.commit()
    conn.close()


def init_db():
    """Standalone DB initialization for CLI usage."""
    from referee_dashboard.app import create_app

    create_app()

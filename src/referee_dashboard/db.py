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
        _migrate(db)
        seed_positions()


def _migrate(database):
    """Run lightweight schema migrations for existing databases."""
    conn = database.engine.raw_connection()
    cursor = conn.connection.cursor()

    # Ensure short_name is after name in leagues (requires table rebuild)
    cursor.execute("PRAGMA table_info(leagues)")
    col_names = [row[1] for row in cursor.fetchall()]
    needs_rebuild = (
        "short_name" not in col_names
        or col_names.index("short_name") != col_names.index("name") + 1
    )
    if needs_rebuild:
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.execute("""
            CREATE TABLE leagues_new (
                id INTEGER PRIMARY KEY,
                name VARCHAR NOT NULL,
                short_name VARCHAR NOT NULL DEFAULT '',
                sorter INTEGER NOT NULL DEFAULT 0,
                remarks VARCHAR DEFAULT '',
                created_at VARCHAR NOT NULL,
                updated_at VARCHAR NOT NULL
            )
        """)
        has_short = "short_name" in col_names
        if has_short:
            cursor.execute("""
                INSERT INTO leagues_new
                    (id, name, short_name, sorter, remarks, created_at, updated_at)
                SELECT id, name, short_name, sorter, remarks, created_at, updated_at
                FROM leagues
            """)
        else:
            cursor.execute("""
                INSERT INTO leagues_new
                    (id, name, short_name, sorter, remarks, created_at, updated_at)
                SELECT id, name, '', sorter, remarks, created_at, updated_at
                FROM leagues
            """)
        cursor.execute("DROP TABLE leagues")
        cursor.execute("ALTER TABLE leagues_new RENAME TO leagues")
        cursor.execute("PRAGMA foreign_keys=ON")
        conn.connection.commit()

    conn.close()


def init_db():
    """Standalone DB initialization for CLI usage."""
    from referee_dashboard.app import create_app

    create_app()

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
        seed_positions()


def init_db():
    """Standalone DB initialization for CLI usage."""
    from referee_dashboard.app import create_app

    create_app()

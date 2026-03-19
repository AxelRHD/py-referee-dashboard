from pathlib import Path

from flask import Flask
from markupsafe import Markup

from referee_dashboard.config import load_config
from referee_dashboard.dashboard.app import create_dash_app
from referee_dashboard.db import init_app
from referee_dashboard.views.layout import base_page


def create_app():
    """Flask application factory."""
    config = load_config()

    app = Flask(__name__)
    app.secret_key = config.SECRET_KEY

    db_path = Path(config.DB_PATH).resolve()
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    init_app(app)

    create_dash_app(app)

    # Register blueprints
    from referee_dashboard.routes.games import bp as games_bp
    from referee_dashboard.routes.leagues import bp as leagues_bp
    from referee_dashboard.routes.teams import bp as teams_bp

    app.register_blueprint(leagues_bp)
    app.register_blueprint(teams_bp)
    app.register_blueprint(games_bp)

    @app.route("/")
    def index():
        page = base_page(
            "Start",
            Markup("<h1>Referee Dashboard</h1>"),
            Markup("<p>Willkommen. Verwende die Navigation oben.</p>"),
        )
        return str(page)

    return app


def main():
    config = load_config()
    app = create_app()
    app.run(port=config.PORT, debug=config.DEBUG)

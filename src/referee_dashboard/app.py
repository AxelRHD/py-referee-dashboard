from pathlib import Path

from flask import Flask, redirect, url_for

from referee_dashboard.config import load_config
from referee_dashboard.db import init_app


def create_app():
    """Flask application factory."""
    config = load_config()

    app = Flask(__name__)
    app.secret_key = config.SECRET_KEY

    db_path = Path(config.DB_PATH).resolve()
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    init_app(app)

    # Register blueprints
    from referee_dashboard.routes.dashboard import bp as dashboard_bp
    from referee_dashboard.routes.data import bp as data_bp
    from referee_dashboard.routes.games import bp as games_bp
    from referee_dashboard.routes.leagues import bp as leagues_bp
    from referee_dashboard.routes.teams import bp as teams_bp

    app.register_blueprint(leagues_bp)
    app.register_blueprint(teams_bp)
    app.register_blueprint(games_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(data_bp)

    @app.route("/")
    def index():
        return redirect(url_for("dashboard.index"))

    return app


def main():
    config = load_config()
    app = create_app()
    app.run(port=config.PORT, debug=config.DEBUG)

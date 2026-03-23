from flask import Blueprint, jsonify
from sqlalchemy import func

from referee_dashboard.db import db
from referee_dashboard.models import Game, League, Position
from referee_dashboard.views.dashboard import dashboard_page
from referee_dashboard.views.layout import base_page

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def _latest_season():
    """Get the most recent season that has games."""
    result = (
        db.session.query(func.substr(Game.game_date, 1, 4))
        .order_by(func.substr(Game.game_date, 1, 4).desc())
        .first()
    )
    return result[0] if result else ""


def _all_seasons():
    """All seasons with games."""
    return [
        s[0]
        for s in db.session.query(func.substr(Game.game_date, 1, 4))
        .distinct()
        .order_by(func.substr(Game.game_date, 1, 4).desc())
        .all()
    ]


@bp.route("/")
def index():
    """Dashboard page — Alpine.js handles data + filtering client-side."""
    seasons = _all_seasons()
    default_season = seasons[0] if seasons else ""
    return str(
        base_page(
            "Dashboard",
            *dashboard_page(seasons, default_season),
            container="",
        )
    )


@bp.route("/api/overview")
def api_overview():
    """JSON endpoint: lightweight game list for overview aggregation."""
    games = Game.query.order_by(Game.game_date).all()
    positions = [p.position for p in Position.query.order_by(Position.sorter).all()]
    leagues_map = {lg.id: lg.name for lg in League.query.all()}

    league_ids = {g.league_id for g in games}
    available_leagues = [
        {"id": lg.id, "name": lg.name}
        for lg in League.query.filter(League.id.in_(league_ids))
        .order_by(League.sorter, League.name)
        .all()
    ]

    data = [
        {
            "year": g.game_date[:4],
            "date": g.game_date,
            "position": g.position,
            "league_id": g.league_id,
            "league": leagues_map.get(g.league_id, ""),
            "fee": g.referee_fee,
            "travel": g.travel_costs,
            "km": g.km_driven,
        }
        for g in games
    ]

    return jsonify({
        "games": data,
        "positions": positions,
        "available_leagues": available_leagues,
    })


@bp.route("/api/data/<season>")
def api_data(season):
    """JSON endpoint: all games for a season with resolved names."""
    games = Game.query.filter(Game.game_date.like(f"{season}-%")).all()

    leagues = {lg.id: lg.name for lg in League.query.all()}
    positions = [p.position for p in Position.query.order_by(Position.sorter).all()]

    data = []
    for g in games:
        data.append(
            {
                "date": g.game_date,
                "month": g.game_date[5:7],
                "home": g.home_team.name,
                "away": g.away_team.name,
                "venue": g.venue or "",
                "league": leagues.get(g.league_id, ""),
                "league_id": g.league_id,
                "position": g.position,
                "fee": g.referee_fee,
                "travel": g.travel_costs,
                "km": g.km_driven,
                "exhibition": bool(g.exhibition),
            }
        )

    # Available filter options for this season
    league_ids = {g.league_id for g in games}
    available_leagues = [
        {"id": lg.id, "name": lg.name}
        for lg in League.query.filter(League.id.in_(league_ids))
        .order_by(League.sorter, League.name)
        .all()
    ]

    game_positions = {g.position for g in games}
    available_positions = [p for p in positions if p in game_positions]

    return jsonify(
        {
            "season": season,
            "games": data,
            "positions": positions,
            "available_positions": available_positions,
            "available_leagues": available_leagues,
        }
    )

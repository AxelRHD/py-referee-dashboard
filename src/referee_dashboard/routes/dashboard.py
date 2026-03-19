from collections import Counter

from flask import Blueprint, request
from sqlalchemy import func

from referee_dashboard.db import db
from referee_dashboard.models import Game, League, Position
from referee_dashboard.views.dashboard import (
    dashboard_content,
    dashboard_page,
)
from referee_dashboard.views.layout import base_page

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def _get_filters():
    """Extract filter values from query params."""
    return {
        "season": request.args.get("season", ""),
        "league_id": request.args.get("league_id", ""),
        "position": request.args.get("position", ""),
    }


def _base_query(filters):
    """Build a filtered Game query (season only — for cascading options)."""
    query = Game.query
    if filters["season"]:
        query = query.filter(Game.game_date.like(f"{filters['season']}-%"))
    return query


def _full_query(filters):
    """Build a fully filtered Game query."""
    query = _base_query(filters)
    if filters["league_id"]:
        query = query.filter(Game.league_id == int(filters["league_id"]))
    if filters["position"]:
        query = query.filter(Game.position == filters["position"])
    return query


def _filter_options(filters):
    """Build cascading filter options based on current selection."""
    # Seasons — always show all
    seasons = (
        db.session.query(func.substr(Game.game_date, 1, 4))
        .distinct()
        .order_by(func.substr(Game.game_date, 1, 4).desc())
        .all()
    )

    # Leagues + positions — scoped to season (cascade from season)
    scoped = _base_query(filters)

    league_ids = {r[0] for r in scoped.with_entities(Game.league_id).distinct().all()}
    leagues = (
        League.query.filter(League.id.in_(league_ids)).order_by(League.sorter, League.name).all()
        if league_ids
        else []
    )

    position_codes = {r[0] for r in scoped.with_entities(Game.position).distinct().all()}
    positions = (
        Position.query.filter(Position.position.in_(position_codes)).order_by(Position.sorter).all()
        if position_codes
        else []
    )

    return {
        "seasons": [s[0] for s in seasons],
        "leagues": leagues,
        "positions": positions,
    }


def _query_without_position(filters):
    """Filtered query ignoring the position filter (for position widget)."""
    query = _base_query(filters)
    if filters["league_id"]:
        query = query.filter(Game.league_id == int(filters["league_id"]))
    return query


def _query_without_league(filters):
    """Filtered query ignoring the league filter (for league widget)."""
    query = _base_query(filters)
    if filters["position"]:
        query = query.filter(Game.position == filters["position"])
    return query


def _compute_stats(games):
    """Compute stats from a list of games."""
    return {
        "count": len(games),
        "total_fee": sum(g.referee_fee for g in games),
        "total_travel": sum(g.travel_costs for g in games),
        "total_km": sum(g.km_driven for g in games),
    }


def _compute_widget_data(filters):
    """Compute all widget data respecting filter exclusions."""
    stats = _compute_stats(_full_query(filters).all())

    # Position chart: ignores position filter
    pos_games = _query_without_position(filters).all()
    pos_counts = Counter(g.position for g in pos_games)
    pos_data = [{"position": p, "count": c} for p, c in pos_counts.items()]

    # Monthly chart: stacked by position, all filters apply
    monthly_games = _full_query(filters).all()
    monthly_data = {}
    for g in monthly_games:
        month = g.game_date[5:7]
        pos = g.position
        monthly_data.setdefault(month, Counter())[pos] += 1

    # League chart: stacked by month, ignores league filter
    league_games = _query_without_league(filters).all()
    league_data = {}
    for g in league_games:
        league = g.league.name
        month = g.game_date[5:7]
        league_data.setdefault(league, Counter())[month] += 1

    return stats, pos_data, monthly_data, league_data


@bp.route("/")
def index():
    """Full dashboard page."""
    filters = _get_filters()
    return str(
        base_page(
            "Dashboard",
            *dashboard_page(_filter_options(filters), filters),
            container="",
        )
    )


@bp.route("/content")
def content():
    """htmx partial: filter bar + widgets with data (for filter changes)."""
    filters = _get_filters()
    stats, pos_data, monthly_data, league_data = _compute_widget_data(filters)
    return str(
        dashboard_content(
            _filter_options(filters), filters, stats, pos_data, monthly_data, league_data
        )
    )

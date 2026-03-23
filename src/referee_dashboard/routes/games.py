from collections import Counter

from flask import Blueprint, flash, redirect, request, url_for
from sqlalchemy import func, or_

from referee_dashboard.db import db
from referee_dashboard.models import Game, League, Position, Team
from referee_dashboard.validation import validate_game
from referee_dashboard.views.games import game_form, game_list, game_table
from referee_dashboard.views.layout import base_page

bp = Blueprint("games", __name__)


def _form_data():
    """Fetch teams, leagues, positions for the game form."""
    teams = Team.query.order_by(Team.name).all()
    leagues = League.query.order_by(League.sorter, League.name).all()
    positions = Position.query.order_by(Position.sorter).all()
    return teams, leagues, positions


def _venues():
    """Fetch distinct venue values for autocomplete."""
    rows = (
        db.session.query(Game.venue)
        .filter(Game.venue != "", Game.venue.isnot(None))
        .distinct()
        .order_by(Game.venue)
        .all()
    )
    return [r[0] for r in rows]


MONTH_NAMES = {
    "01": "Januar",
    "02": "Februar",
    "03": "März",
    "04": "April",
    "05": "Mai",
    "06": "Juni",
    "07": "Juli",
    "08": "August",
    "09": "September",
    "10": "Oktober",
    "11": "November",
    "12": "Dezember",
}


def _filter_options(season=""):
    """Build filter option lists from existing data."""
    seasons = (
        db.session.query(func.substr(Game.game_date, 1, 4))
        .distinct()
        .order_by(func.substr(Game.game_date, 1, 4).desc())
        .all()
    )

    # Months that have games, optionally scoped to a season
    month_query = db.session.query(func.substr(Game.game_date, 6, 2)).distinct()
    if season:
        month_query = month_query.filter(Game.game_date.like(f"{season}-%"))
    month_query = month_query.order_by(func.substr(Game.game_date, 6, 2))
    available_months = [(m[0], MONTH_NAMES.get(m[0], m[0])) for m in month_query.all()]

    leagues = League.query.order_by(League.sorter, League.name).all()
    positions = Position.query.order_by(Position.sorter).all()
    return {
        "seasons": [s[0] for s in seasons],
        "leagues": leagues,
        "positions": positions,
        "months": available_months,
    }


@bp.route("/games")
def index():
    query = Game.query

    # Filters
    season = request.args.get("season", "")
    month = request.args.get("month", "")
    league_id = request.args.get("league_id", "")
    pos = request.args.get("position", "")
    search = request.args.get("q", "").strip()

    if season:
        query = query.filter(Game.game_date.like(f"{season}-%"))
    if month:
        query = query.filter(func.substr(Game.game_date, 6, 2) == month)
    if league_id:
        query = query.filter(Game.league_id == int(league_id))
    if pos:
        query = query.filter(Game.position == pos)
    if search:
        pattern = f"%{search}%"
        ht = db.aliased(Team)
        at = db.aliased(Team)
        query = (
            query.join(ht, Game.home_team_id == ht.id)
            .join(at, Game.away_team_id == at.id)
            .filter(
                or_(
                    ht.name.ilike(pattern),
                    at.name.ilike(pattern),
                    Game.venue.ilike(pattern),
                    Game.remarks.ilike(pattern),
                )
            )
        )

    # Default sort: date desc, time asc
    query = query.order_by(Game.game_date.desc(), Game.game_time.asc())

    games = query.all()

    # Compute stats from filtered results
    stats = {
        "count": len(games),
        "total_fee": sum(g.referee_fee for g in games),
        "total_travel": sum(g.travel_costs for g in games),
        "total_km": sum(g.km_driven for g in games),
        "positions": Counter(g.position for g in games),
    }

    page = int(request.args.get("page", 1) or 1)

    filters = {
        "season": season,
        "month": month,
        "league_id": league_id,
        "position": pos,
        "q": search,
        "page": str(page),
    }

    # htmx request → return only the partial (stats + table + pagination)
    if request.headers.get("HX-Request"):
        return str(game_table(games, stats, page, filters))

    return str(base_page("Spiele", *game_list(games, _filter_options(season), filters, stats)))


@bp.route("/games/new", methods=["GET", "POST"])
def new():
    teams, leagues, positions = _form_data()
    if request.method == "POST":
        data, errors = validate_game(request.form)
        if errors:
            return (
                str(
                    base_page(
                        "Neues Spiel",
                        *game_form(
                            teams=teams,
                            leagues=leagues,
                            positions=positions,
                            errors=errors,
                            data=data,
                            venues=_venues(),
                        ),
                    )
                ),
                422,
            )
        game = Game(**data)
        db.session.add(game)
        db.session.commit()
        flash("Spiel wurde erstellt.", "success")
        return redirect(url_for("games.index"))
    return str(
        base_page(
            "Neues Spiel",
            *game_form(teams=teams, leagues=leagues, positions=positions, venues=_venues()),
        )
    )


@bp.route("/games/<int:id>/edit", methods=["GET", "POST"])
def edit(id):
    game = db.get_or_404(Game, id)
    teams, leagues, positions = _form_data()
    if request.method == "POST":
        data, errors = validate_game(request.form)
        if errors:
            return (
                str(
                    base_page(
                        "Spiel bearbeiten",
                        *game_form(
                            game=game,
                            teams=teams,
                            leagues=leagues,
                            positions=positions,
                            errors=errors,
                            data=data,
                            venues=_venues(),
                        ),
                    )
                ),
                422,
            )
        for key, val in data.items():
            setattr(game, key, val)
        db.session.commit()
        flash("Spiel wurde aktualisiert.", "success")
        return redirect(url_for("games.index"))
    return str(
        base_page(
            "Spiel bearbeiten",
            *game_form(
                game=game, teams=teams, leagues=leagues, positions=positions, venues=_venues()
            ),
        )
    )


@bp.route("/games/<int:id>/delete", methods=["POST"])
def delete(id):
    game = db.get_or_404(Game, id)
    db.session.delete(game)
    db.session.commit()
    flash("Spiel wurde gelöscht.", "success")
    return redirect(url_for("games.index"))

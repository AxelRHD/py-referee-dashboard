from flask import Blueprint, Response, flash, redirect, request, url_for

from referee_dashboard.db import db
from referee_dashboard.models import League
from referee_dashboard.validation import validate_league
from referee_dashboard.views.layout import base_page
from referee_dashboard.views.leagues import league_form, league_list

bp = Blueprint("leagues", __name__)


@bp.route("/leagues")
def index():
    leagues = League.query.order_by(League.sorter, League.name).all()
    return str(base_page("Ligen", *league_list(leagues)))


@bp.route("/leagues/new", methods=["GET", "POST"])
def new():
    if request.method == "POST":
        data, errors = validate_league(request.form)
        if errors:
            return str(base_page("Neue Liga", *league_form(errors=errors, data=data))), 422
        league = League(**data)
        db.session.add(league)
        db.session.commit()
        flash("Liga wurde erstellt.", "success")
        return redirect(url_for("leagues.index"))
    return str(base_page("Neue Liga", *league_form()))


@bp.route("/leagues/<int:id>/edit", methods=["GET", "POST"])
def edit(id):
    league = db.get_or_404(League, id)
    if request.method == "POST":
        data, errors = validate_league(request.form)
        if errors:
            return (
                str(
                    base_page(
                        "Liga bearbeiten",
                        *league_form(league=league, errors=errors, data=data),
                    )
                ),
                422,
            )
        for key, val in data.items():
            setattr(league, key, val)
        db.session.commit()
        flash("Liga wurde aktualisiert.", "success")
        return redirect(url_for("leagues.index"))
    return str(base_page("Liga bearbeiten", *league_form(league)))


@bp.route("/leagues/<int:id>/delete", methods=["POST"])
def delete(id):
    league = db.get_or_404(League, id)
    db.session.delete(league)
    db.session.commit()
    flash("Liga wurde gelöscht.", "success")
    return redirect(url_for("leagues.index"))


@bp.route("/leagues/export/csv")
def export_csv():
    from referee_dashboard.export import leagues_csv

    return Response(
        leagues_csv(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=ligen.csv"},
    )


@bp.route("/leagues/export/sql")
def export_sql():
    from referee_dashboard.export import leagues_sql

    return Response(
        leagues_sql(),
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment; filename=ligen.sql"},
    )

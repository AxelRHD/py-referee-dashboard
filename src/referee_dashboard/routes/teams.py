from flask import Blueprint, Response, flash, redirect, request, url_for

from referee_dashboard.db import db
from referee_dashboard.models import Team
from referee_dashboard.validation import validate_team
from referee_dashboard.views.layout import base_page
from referee_dashboard.views.teams import team_form, team_list

bp = Blueprint("teams", __name__)


@bp.route("/teams")
def index():
    teams = Team.query.order_by(Team.name).all()
    return str(base_page("Teams", *team_list(teams)))


@bp.route("/teams/new", methods=["GET", "POST"])
def new():
    if request.method == "POST":
        data, errors = validate_team(request.form)
        if errors:
            return str(base_page("Neues Team", *team_form(errors=errors, data=data))), 422
        team = Team(**data)
        db.session.add(team)
        db.session.commit()
        flash("Team wurde erstellt.", "success")
        return redirect(url_for("teams.index"))
    return str(base_page("Neues Team", *team_form()))


@bp.route("/teams/<int:id>/edit", methods=["GET", "POST"])
def edit(id):
    team = db.get_or_404(Team, id)
    if request.method == "POST":
        data, errors = validate_team(request.form)
        if errors:
            return (
                str(base_page("Team bearbeiten", *team_form(team=team, errors=errors, data=data))),
                422,
            )
        for key, val in data.items():
            setattr(team, key, val)
        db.session.commit()
        flash("Team wurde aktualisiert.", "success")
        return redirect(url_for("teams.index"))
    return str(base_page("Team bearbeiten", *team_form(team)))


@bp.route("/teams/<int:id>/delete", methods=["POST"])
def delete(id):
    team = db.get_or_404(Team, id)
    db.session.delete(team)
    db.session.commit()
    flash("Team wurde gelöscht.", "success")
    return redirect(url_for("teams.index"))


@bp.route("/teams/export/csv")
def export_csv():
    from referee_dashboard.export import teams_csv

    return Response(
        teams_csv(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=teams.csv"},
    )


@bp.route("/teams/export/sql")
def export_sql():
    from referee_dashboard.export import teams_sql

    return Response(
        teams_sql(),
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment; filename=teams.sql"},
    )

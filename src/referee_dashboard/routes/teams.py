from flask import Blueprint, redirect, request, url_for

from referee_dashboard.db import db
from referee_dashboard.models import Team
from referee_dashboard.views.layout import base_page
from referee_dashboard.views.teams import team_form, team_list

bp = Blueprint("teams", __name__)


@bp.route("/teams")
def index():
    teams = Team.query.order_by(Team.name).all()
    return str(base_page("Teams", *team_list(teams)))


@bp.route("/teams/new")
def new():
    return str(base_page("Neues Team", *team_form()))


@bp.route("/teams", methods=["POST"])
def create():
    team = Team(
        name=request.form["name"],
        state=request.form.get("state", ""),
        is_active=1 if request.form.get("is_active") else 0,
        remarks=request.form.get("remarks", ""),
    )
    db.session.add(team)
    db.session.commit()
    return redirect(url_for("teams.index"))


@bp.route("/teams/<int:id>/edit")
def edit(id):
    team = db.get_or_404(Team, id)
    return str(base_page("Team bearbeiten", *team_form(team)))


@bp.route("/teams/<int:id>", methods=["POST"])
def update(id):
    team = db.get_or_404(Team, id)
    team.name = request.form["name"]
    team.state = request.form.get("state", "")
    team.is_active = 1 if request.form.get("is_active") else 0
    team.remarks = request.form.get("remarks", "")
    db.session.commit()
    return redirect(url_for("teams.index"))


@bp.route("/teams/<int:id>/delete", methods=["POST"])
def delete(id):
    team = db.get_or_404(Team, id)
    db.session.delete(team)
    db.session.commit()
    return redirect(url_for("teams.index"))

from flask import Blueprint, redirect, request, url_for

from referee_dashboard.db import db
from referee_dashboard.models import League
from referee_dashboard.views.layout import base_page
from referee_dashboard.views.leagues import league_form, league_list

bp = Blueprint("leagues", __name__)


@bp.route("/leagues")
def index():
    leagues = League.query.order_by(League.sorter, League.name).all()
    return str(base_page("Ligen", *league_list(leagues)))


@bp.route("/leagues/new")
def new():
    return str(base_page("Neue Liga", *league_form()))


@bp.route("/leagues", methods=["POST"])
def create():
    league = League(
        name=request.form["name"],
        sorter=int(request.form.get("sorter", 0)),
        remarks=request.form.get("remarks", ""),
    )
    db.session.add(league)
    db.session.commit()
    return redirect(url_for("leagues.index"))


@bp.route("/leagues/<int:id>/edit")
def edit(id):
    league = db.get_or_404(League, id)
    return str(base_page("Liga bearbeiten", *league_form(league)))


@bp.route("/leagues/<int:id>", methods=["POST"])
def update(id):
    league = db.get_or_404(League, id)
    league.name = request.form["name"]
    league.sorter = int(request.form.get("sorter", 0))
    league.remarks = request.form.get("remarks", "")
    db.session.commit()
    return redirect(url_for("leagues.index"))


@bp.route("/leagues/<int:id>/delete", methods=["POST"])
def delete(id):
    league = db.get_or_404(League, id)
    db.session.delete(league)
    db.session.commit()
    return redirect(url_for("leagues.index"))

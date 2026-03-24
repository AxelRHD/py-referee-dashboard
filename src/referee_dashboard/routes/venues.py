import json
import urllib.parse
import urllib.request

from flask import Blueprint, Response, flash, redirect, request, url_for

from referee_dashboard.db import db
from referee_dashboard.models import Venue
from referee_dashboard.validation import validate_venue
from referee_dashboard.views.layout import base_page
from referee_dashboard.views.venues import venue_form, venue_list

bp = Blueprint("venues", __name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "RefereeApp/1.0"


@bp.route("/venues")
def index():
    venues = Venue.query.order_by(Venue.city).all()
    return str(base_page("Spielorte", *venue_list(venues)))


@bp.route("/venues/new", methods=["GET", "POST"])
def new():
    if request.method == "POST":
        data, errors = validate_venue(request.form)
        if errors:
            return (
                str(base_page("Neuer Spielort", *venue_form(errors=errors, data=data))),
                422,
            )
        venue = Venue(**data)
        db.session.add(venue)
        db.session.commit()
        flash("Spielort wurde erstellt.", "success")
        return redirect(url_for("venues.index"))
    return str(base_page("Neuer Spielort", *venue_form()))


@bp.route("/venues/<int:id>/edit", methods=["GET", "POST"])
def edit(id):
    venue = db.get_or_404(Venue, id)
    if request.method == "POST":
        data, errors = validate_venue(request.form)
        if errors:
            return (
                str(
                    base_page(
                        "Spielort bearbeiten",
                        *venue_form(venue=venue, errors=errors, data=data),
                    )
                ),
                422,
            )
        for key, val in data.items():
            setattr(venue, key, val)
        db.session.commit()
        flash("Spielort wurde aktualisiert.", "success")
        return redirect(url_for("venues.index"))
    return str(base_page("Spielort bearbeiten", *venue_form(venue)))


@bp.route("/venues/<int:id>/delete", methods=["POST"])
def delete(id):
    venue = db.get_or_404(Venue, id)
    db.session.delete(venue)
    db.session.commit()
    flash("Spielort wurde gelöscht.", "success")
    return redirect(url_for("venues.index"))


@bp.route("/venues/<int:id>/geocode", methods=["POST"])
def geocode(id):
    venue = db.get_or_404(Venue, id)

    query = f"{venue.stadium}, {venue.city}" if venue.stadium else venue.city
    query += ", Germany"

    params = urllib.parse.urlencode({"q": query, "format": "json", "limit": "1"})
    url = f"{NOMINATIM_URL}?{params}"

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            results = json.loads(resp.read().decode())
        if results:
            venue.lat = float(results[0]["lat"])
            venue.lon = float(results[0]["lon"])
            db.session.commit()
            flash(f"Koordinaten gefunden: {venue.lat:.4f}, {venue.lon:.4f}", "success")
        else:
            flash("Keine Koordinaten gefunden.", "warning")
    except Exception as e:
        flash(f"Geocoding-Fehler: {e}", "danger")

    return redirect(url_for("venues.edit", id=venue.id))


@bp.route("/venues/export/csv")
def export_csv():
    from referee_dashboard.export import venues_csv

    return Response(
        venues_csv(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=spielorte.csv"},
    )


@bp.route("/venues/export/sql")
def export_sql():
    from referee_dashboard.export import venues_sql

    return Response(
        venues_sql(),
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment; filename=spielorte.sql"},
    )

from flask import Blueprint, Response, flash, redirect, request, url_for

from referee_dashboard.export import all_data_sql, full_dump
from referee_dashboard.import_data import execute_sql, import_csv, sanitize_sql
from referee_dashboard.views.data import data_page
from referee_dashboard.views.layout import base_page

bp = Blueprint("data", __name__)


@bp.route("/data")
def index():
    return str(base_page("Datenverwaltung", *data_page()))


@bp.route("/data/dump")
def dump():
    return Response(
        full_dump(),
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment; filename=referee_dump.sql"},
    )


@bp.route("/data/export-all")
def export_all():
    return Response(
        all_data_sql(),
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment; filename=referee_data.sql"},
    )


@bp.route("/data/import", methods=["POST"])
def import_file():
    file = request.files.get("file")
    if not file or not file.filename:
        flash("Keine Datei ausgewählt.", "danger")
        return redirect(url_for("data.index"))

    text = file.read().decode("utf-8-sig")
    fmt = request.form.get("format", "sql")

    return _process_import(text, fmt, request.form.get("entity", "games"))


@bp.route("/data/paste", methods=["POST"])
def paste():
    text = request.form.get("content", "").strip()
    if not text:
        flash("Keine Daten eingegeben.", "danger")
        return redirect(url_for("data.index"))

    fmt = request.form.get("format", "sql")

    return _process_import(text, fmt, request.form.get("entity", "games"))


def _process_import(text: str, fmt: str, entity: str):
    """Process SQL or CSV import and flash results."""
    if fmt == "sql":
        statements, parse_errors = sanitize_sql(text)
        if parse_errors:
            for err in parse_errors:
                flash(err, "danger")
        if statements:
            count, exec_errors = execute_sql(statements)
            for err in exec_errors:
                flash(err, "danger")
            if count > 0:
                flash(f"{count} SQL-Statement(s) erfolgreich ausgeführt.", "success")
        elif not parse_errors:
            flash("Keine gültigen SQL-Statements gefunden.", "warning")
    else:
        count, errors = import_csv(text, entity)
        for err in errors:
            flash(err, "danger")
        if count > 0:
            flash(f"{count} Datensatz/Datensätze importiert.", "success")
        elif not errors:
            flash("Keine Daten zum Importieren gefunden.", "warning")

    return redirect(url_for("data.index"))

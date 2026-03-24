from htpy import a, button, div, h1, small, td, tr
from htpy import form as html_form

from referee_dashboard.views.components import (
    action_links,
    data_table,
    form_field,
    form_row,
    submit_button,
    text_input,
)


def venue_list(venues):
    """View: list all venues."""
    return [
        h1["Spielorte"],
        div(".d-flex.justify-content-between.mb-3")[
            a(".btn.btn-success", href="/venues/new")["Neuer Spielort"],
            div[
                a(".btn.btn-sm.btn-outline-secondary.me-1", href="/venues/export/csv")["CSV"],
                a(".btn.btn-sm.btn-outline-secondary", href="/venues/export/sql")["SQL"],
            ],
        ],
        data_table(
            ["Stadt", "Stadion", "Lat", "Lon", "Aktionen"],
            [
                tr[
                    td[v.city],
                    td[v.stadium or ""],
                    td(".text-muted")[f"{v.lat:.4f}" if v.lat is not None else ""],
                    td(".text-muted")[f"{v.lon:.4f}" if v.lon is not None else ""],
                    action_links(
                        f"/venues/{v.id}/edit",
                        f"/venues/{v.id}/delete",
                    ),
                ]
                for v in venues
            ],
        ),
    ]


def venue_form(venue=None, errors=None, data=None):
    """View: create/edit venue form."""
    errors = errors or {}
    is_edit = venue is not None

    if data:
        vals = data
    elif is_edit:
        vals = {
            "city": venue.city,
            "stadium": venue.stadium or "",
        }
    else:
        vals = {}

    title = "Spielort bearbeiten" if is_edit else "Neuer Spielort"
    action = f"/venues/{venue.id}/edit" if is_edit else "/venues/new"

    lat_display = f"{venue.lat:.6f}" if is_edit and venue.lat is not None else "–"
    lon_display = f"{venue.lon:.6f}" if is_edit and venue.lon is not None else "–"

    geocode_btn = ""
    if is_edit:
        geocode_btn = html_form(
            method="post",
            action=f"/venues/{venue.id}/geocode",
            style="display:inline",
        )[button(".btn.btn-sm.btn-outline-primary", type="submit")["Koordinaten nachschlagen"],]

    return [
        h1[title],
        html_form(method="post", action=action)[
            form_row(
                form_field(
                    "Stadt",
                    text_input(
                        "city",
                        value=str(vals.get("city", "")),
                        required=True,
                        error=errors.get("city", ""),
                    ),
                    error=errors.get("city", ""),
                ),
                form_field(
                    "Stadion",
                    text_input(
                        "stadium",
                        value=str(vals.get("stadium", "")),
                    ),
                ),
            ),
            div(".mb-3")[
                small(".text-muted")[f"Koordinaten: {lat_display}, {lon_display}"],
                div(".mt-1")[geocode_btn] if geocode_btn else "",
            ]
            if is_edit
            else "",
            submit_button(cancel_url="/venues"),
        ],
    ]

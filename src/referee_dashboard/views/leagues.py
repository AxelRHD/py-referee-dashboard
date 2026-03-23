from htpy import a, div, h1, td, tr
from htpy import form as html_form

from referee_dashboard.views.components import (
    action_links,
    data_table,
    form_field,
    form_row,
    number_input,
    submit_button,
    text_input,
    textarea_input,
)


def league_list(leagues):
    """View: list all leagues."""
    return [
        h1["Ligen"],
        div(".d-flex.justify-content-between.mb-3")[
            a(".btn.btn-success", href="/leagues/new")["Neue Liga"],
            div[
                a(".btn.btn-sm.btn-outline-secondary.me-1", href="/leagues/export/csv")["CSV"],
                a(".btn.btn-sm.btn-outline-secondary", href="/leagues/export/sql")["SQL"],
            ],
        ],
        data_table(
            ["#", "Name", "Kürzel", "Bemerkungen", "Aktionen"],
            [
                tr[
                    td(".text-end")[str(league.sorter)],
                    td[league.name],
                    td[league.short_name or ""],
                    td[league.remarks or ""],
                    action_links(
                        f"/leagues/{league.id}/edit",
                        f"/leagues/{league.id}/delete",
                    ),
                ]
                for league in leagues
            ],
        ),
    ]


def league_form(league=None, errors=None, data=None):
    """View: create/edit league form."""
    errors = errors or {}
    is_edit = league is not None

    if data:
        vals = data
    elif is_edit:
        vals = {
            "name": league.name,
            "short_name": league.short_name or "",
            "sorter": league.sorter,
            "remarks": league.remarks or "",
        }
    else:
        vals = {}

    title = "Liga bearbeiten" if is_edit else "Neue Liga"
    action = f"/leagues/{league.id}" if is_edit else "/leagues"

    return [
        h1[title],
        html_form(method="post", action=action)[
            form_row(
                form_field(
                    "Name",
                    text_input(
                        "name",
                        value=str(vals.get("name", "")),
                        required=True,
                        error=errors.get("name", ""),
                    ),
                    error=errors.get("name", ""),
                ),
                form_field(
                    "Kürzel",
                    text_input(
                        "short_name",
                        value=str(vals.get("short_name", "")),
                    ),
                ),
                form_field(
                    "Sortierung",
                    number_input(
                        "sorter",
                        value=str(vals.get("sorter", "0")),
                        step="1",
                        error=errors.get("sorter", ""),
                    ),
                    error=errors.get("sorter", ""),
                ),
            ),
            form_field(
                "Bemerkungen",
                textarea_input("remarks", value=str(vals.get("remarks", "")), rows=2),
            ),
            submit_button(cancel_url="/leagues"),
        ],
    ]

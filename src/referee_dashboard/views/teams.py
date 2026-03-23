from htpy import a, div, h1, td, tr
from htpy import form as html_form

from referee_dashboard.validation import BUNDESLAENDER
from referee_dashboard.views.components import (
    action_links,
    checkbox_input,
    data_table,
    datalist_input,
    form_field,
    form_row,
    submit_button,
    text_input,
    textarea_input,
)


def team_list(teams):
    """View: list all teams."""
    return [
        h1["Teams"],
        div(".d-flex.justify-content-between.mb-3")[
            a(".btn.btn-success", href="/teams/new")["Neues Team"],
            div[
                a(".btn.btn-sm.btn-outline-secondary.me-1", href="/teams/export/csv")["CSV"],
                a(".btn.btn-sm.btn-outline-secondary", href="/teams/export/sql")["SQL"],
            ],
        ],
        data_table(
            ["Name", "Bundesland", "Aktiv", "Bemerkungen", "Aktionen"],
            [
                tr[
                    td[team.name],
                    td[team.state or ""],
                    td["Ja" if team.is_active else "Nein"],
                    td[team.remarks or ""],
                    action_links(
                        f"/teams/{team.id}/edit",
                        f"/teams/{team.id}/delete",
                    ),
                ]
                for team in teams
            ],
        ),
    ]


def team_form(team=None, errors=None, data=None):
    """View: create/edit team form."""
    errors = errors or {}
    is_edit = team is not None

    if data:
        vals = data
    elif is_edit:
        vals = {
            "name": team.name,
            "state": team.state or "",
            "is_active": team.is_active,
            "remarks": team.remarks or "",
        }
    else:
        vals = {"is_active": 1, "state": "Baden-Württemberg"}

    title = "Team bearbeiten" if is_edit else "Neues Team"
    action = f"/teams/{team.id}/edit" if is_edit else "/teams/new"

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
                    "Bundesland",
                    datalist_input(
                        "state",
                        value=str(vals.get("state", "")),
                        datalist_id="state-list",
                        options=BUNDESLAENDER,
                    ),
                ),
            ),
            form_row(
                form_field(
                    "Bemerkungen",
                    textarea_input("remarks", value=str(vals.get("remarks", "")), rows=1),
                ),
            ),
            checkbox_input(
                "is_active",
                checked=bool(vals.get("is_active", True)),
                field_label="Aktiv",
            ),
            submit_button(cancel_url="/teams"),
        ],
    ]

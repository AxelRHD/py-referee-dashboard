from htpy import a, h1, td, tr
from htpy import form as html_form

from referee_dashboard.views.components import (
    action_links,
    checkbox_input,
    data_table,
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
        a(".btn.btn-success.mb-3", href="/teams/new")["Neues Team"],
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


def team_form(team=None):
    """View: create/edit team form."""
    is_edit = team is not None
    title = "Team bearbeiten" if is_edit else "Neues Team"
    action = f"/teams/{team.id}" if is_edit else "/teams"

    name = team.name if is_edit else ""
    state = team.state or "" if is_edit else ""
    remarks = team.remarks or "" if is_edit else ""

    return [
        h1[title],
        html_form(method="post", action=action)[
            form_row(
                form_field("Name", text_input("name", value=name, required=True)),
                form_field("Bundesland", text_input("state", value=state)),
            ),
            form_row(
                form_field("Bemerkungen", textarea_input("remarks", value=remarks, rows=1)),
            ),
            checkbox_input(
                "is_active",
                checked=bool(team.is_active) if is_edit else True,
                field_label="Aktiv",
            ),
            submit_button(),
        ],
    ]

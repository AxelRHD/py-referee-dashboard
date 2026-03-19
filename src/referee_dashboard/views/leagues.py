from htpy import a, h1, td, tr
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
        a(".btn.btn-success.mb-3", href="/leagues/new")["Neue Liga"],
        data_table(
            ["#", "Name", "Bemerkungen", "Aktionen"],
            [
                tr[
                    td(".text-end")[str(league.sorter)],
                    td[league.name],
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


def league_form(league=None):
    """View: create/edit league form."""
    is_edit = league is not None
    title = "Liga bearbeiten" if is_edit else "Neue Liga"
    action = f"/leagues/{league.id}" if is_edit else "/leagues"

    name = league.name if is_edit else ""
    sorter = str(league.sorter) if is_edit else "0"
    remarks = league.remarks or "" if is_edit else ""

    return [
        h1[title],
        html_form(method="post", action=action)[
            form_row(
                form_field("Name", text_input("name", value=name, required=True)),
                form_field("Sortierung", number_input("sorter", value=sorter, step="1")),
            ),
            form_field("Bemerkungen", textarea_input("remarks", value=remarks, rows=2)),
            submit_button(),
        ],
    ]

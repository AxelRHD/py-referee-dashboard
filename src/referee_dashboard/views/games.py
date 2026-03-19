import json

from htpy import a, div, h1, li, nav, option, select, small, span, td, tr
from htpy import form as html_form
from htpy import input as html_input
from markupsafe import Markup

from referee_dashboard.views.components import (
    action_links,
    checkbox_input,
    data_table,
    date_input,
    form_field,
    form_row,
    number_input,
    select_field,
    submit_button,
    text_input,
    textarea_input,
    time_input,
)

GAMES_PER_PAGE = 25


def _eur(value: float) -> str:
    """Format float as German EUR string: 1.234,56 €"""
    s = f"{value:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s} €"


def _filter_select(name, options, selected="", label="Alle"):
    """Compact select for the filter bar."""
    return select(
        ".form-select.form-select-sm",
        name=name,
    )[
        option(value="")[label],
        [option(value=val, selected=(val == selected))[lbl] for val, lbl in options],
    ]


def _filter_bar(filter_options, filters):
    """Filter bar with htmx — auto-submits on change, debounces text input."""
    season_opts = [(s, s) for s in filter_options["seasons"]]
    month_opts = filter_options["months"]
    league_opts = [(str(lg.id), lg.name) for lg in filter_options["leagues"]]
    pos_opts = [(p.position, p.position) for p in filter_options["positions"]]

    hx_attrs = {
        "hx-get": "/games",
        "hx-target": "#games-content",
        "hx-trigger": "change",
        "hx-push-url": "true",
    }

    return html_form(".mb-3", method="get", action="/games", **hx_attrs)[
        div(".row.g-2.align-items-end")[
            div(".col-auto")[
                small(".text-muted")["Saison"],
                _filter_select("season", season_opts, filters.get("season", "")),
            ],
            div(".col-auto")[
                small(".text-muted")["Monat"],
                _filter_select("month", month_opts, filters.get("month", "")),
            ],
            div(".col-auto")[
                small(".text-muted")["Liga"],
                _filter_select("league_id", league_opts, filters.get("league_id", "")),
            ],
            div(".col-auto")[
                small(".text-muted")["Position"],
                _filter_select("position", pos_opts, filters.get("position", "")),
            ],
            div(".col")[
                small(".text-muted")["Suche"],
                html_input(
                    ".form-control.form-control-sm",
                    type="text",
                    name="q",
                    value=filters.get("q", ""),
                    placeholder="Team, Spielort, Bemerkung...",
                    **{
                        "hx-get": "/games",
                        "hx-target": "#games-content",
                        "hx-trigger": "input changed delay:400ms, search",
                        "hx-push-url": "true",
                    },
                ),
            ],
            div(".col-auto")[
                a(
                    ".btn.btn-sm.btn-outline-secondary",
                    href="/games",
                )["Zurücksetzen"],
            ],
        ],
    ]


def _stats_cards(stats):
    """Summary cards for the filtered games."""
    total = stats["total_fee"] + stats["total_travel"]

    def card(label, value):
        return div(".col")[
            div(".card")[
                div(".card-body.py-2.px-3")[
                    small(".text-muted.d-block")[label],
                    span(".fw-bold")[value],
                ],
            ]
        ]

    return div(".row.g-2.mb-3")[
        card("Spiele", str(stats["count"])),
        card("Vergütung", _eur(stats["total_fee"])),
        card("Fahrtkosten", _eur(stats["total_travel"])),
        card("Gesamt", _eur(total)),
        card("Kilometer", f"{stats['total_km']:,}".replace(",", ".")),
    ]


def _position_chart(positions):
    """Inline Plotly pie chart for position distribution."""
    if not positions:
        return ""

    labels = list(positions.keys())
    values = list(positions.values())

    # Nord Frost + Aurora colors
    colors = [
        "#5E81AC",
        "#88C0D0",
        "#8FBCBB",
        "#81A1C1",
        "#A3BE8C",
        "#EBCB8B",
        "#D08770",
        "#BF616A",
    ]

    chart_data = json.dumps(
        {
            "data": [
                {
                    "labels": labels,
                    "values": values,
                    "type": "pie",
                    "hole": 0.4,
                    "textinfo": "label+value",
                    "textposition": "inside",
                    "marker": {"colors": colors[: len(labels)]},
                }
            ],
            "layout": {
                "height": 200,
                "margin": {"t": 10, "b": 10, "l": 10, "r": 10},
                "showlegend": False,
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "font": {"color": "#D8DEE9", "size": 11},
            },
        }
    )

    chart_id = "position-chart"
    script = (
        f"<script>"
        f"(function render(){{"
        f"  if(typeof Plotly==='undefined'){{setTimeout(render,50);return}}"
        f"  var d={chart_data};"
        f"  d.layout.font.color=getComputedStyle(document.body).color;"
        f'  Plotly.newPlot("{chart_id}",d.data,d.layout,'
        f"    {{responsive:true,displayModeBar:false}});"
        f"}})()"
        f"</script>"
    )

    return div(".col-md-3")[
        div(".card")[
            div(".card-body.py-2.px-3")[
                small(".text-muted.d-block.mb-1")["Positionen"],
                div(id=chart_id),
                Markup(script),
            ],
        ]
    ]


def _stats_row(stats):
    """Stats cards + position chart in a row."""
    return div(".row.g-2.mb-3")[
        div(".col-md-9")[_stats_cards(stats)],
        _position_chart(stats.get("positions", {})),
    ]


def _pagination(page, total_pages, filters):
    """Bootstrap pagination with htmx."""
    if total_pages <= 1:
        return ""

    def page_url(p):
        params = {k: v for k, v in filters.items() if v}
        params["page"] = p
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        return f"/games?{qs}"

    items = []

    # Previous
    if page > 1:
        items.append(li(".page-item")[a(".page-link", href=page_url(page - 1))["«"]])
    else:
        items.append(li(".page-item.disabled")[span(".page-link")["«"]])

    # Page numbers
    for p in range(1, total_pages + 1):
        if p == page:
            items.append(li(".page-item.active")[span(".page-link")[str(p)]])
        else:
            items.append(li(".page-item")[a(".page-link", href=page_url(p))[str(p)]])

    # Next
    if page < total_pages:
        items.append(li(".page-item")[a(".page-link", href=page_url(page + 1))["»"]])
    else:
        items.append(li(".page-item.disabled")[span(".page-link")["»"]])

    return nav[
        Markup('<ul class="pagination pagination-sm justify-content-center">'),
        items,
        Markup("</ul>"),
    ]


def game_table(games, stats=None, page=1, filters=None):
    """Partial: stats + paginated games table (htmx target)."""
    filters = filters or {}
    stats = stats or {}
    total = len(games)
    total_pages = max(1, (total + GAMES_PER_PAGE - 1) // GAMES_PER_PAGE)
    page = max(1, min(page, total_pages))
    start = (page - 1) * GAMES_PER_PAGE
    page_games = games[start : start + GAMES_PER_PAGE]

    return div(id="games-content")[
        _stats_row(stats) if stats else "",
        data_table(
            [
                "Datum",
                "Zeit",
                "Pos",
                "Liga",
                "Heim",
                "Gast",
                "Spielort",
                "Vergütung",
                "Fahrtkosten",
                "Gesamt",
                "Aktionen",
            ],
            [
                tr[
                    td[game.game_date],
                    td[game.game_time or ""],
                    td[game.position],
                    td[game.league.name],
                    td[game.home_team.name],
                    td[game.away_team.name],
                    td[game.venue or ""],
                    td(".text-end")[_eur(game.referee_fee)],
                    td(".text-end")[_eur(game.travel_costs)],
                    td(".text-end")[_eur(game.referee_fee + game.travel_costs)],
                    action_links(
                        f"/games/{game.id}/edit",
                        f"/games/{game.id}/delete",
                    ),
                ]
                for game in page_games
            ],
        ),
        _pagination(page, total_pages, filters),
    ]


def game_list(games, filter_options=None, filters=None, stats=None):
    """View: full games page with filter bar, stats, and table."""
    filters = filters or {}
    page = int(filters.get("page", 1) or 1)
    return [
        h1["Spiele"],
        div(".d-flex.justify-content-between.mb-3")[
            a(".btn.btn-success", href="/games/new")["Neues Spiel"],
        ],
        _filter_bar(filter_options, filters) if filter_options else "",
        game_table(games, stats, page, filters),
    ]


def game_form(game=None, teams=None, leagues=None, positions=None):
    """View: create/edit game form with dropdowns."""
    teams = teams or []
    leagues = leagues or []
    positions = positions or []

    is_edit = game is not None
    title = "Spiel bearbeiten" if is_edit else "Neues Spiel"
    action = f"/games/{game.id}" if is_edit else "/games"

    team_options = [(str(t.id), t.name) for t in teams]
    league_options = [(str(lg.id), lg.name) for lg in leagues]
    position_options = [(p.position, f"{p.position} — {p.long}") for p in positions]

    return [
        h1[title],
        html_form(method="post", action=action)[
            # Datum + Uhrzeit
            form_row(
                form_field(
                    "Datum",
                    date_input(
                        "game_date",
                        value=game.game_date if is_edit else "",
                        required=True,
                    ),
                ),
                form_field(
                    "Uhrzeit",
                    time_input(
                        "game_time",
                        value=game.game_time or "" if is_edit else "",
                    ),
                ),
            ),
            # Heim + Gast
            form_row(
                form_field(
                    "Heimteam",
                    select_field(
                        "home_team_id",
                        team_options,
                        selected=str(game.home_team_id) if is_edit else "",
                        required=True,
                    ),
                ),
                form_field(
                    "Gastteam",
                    select_field(
                        "away_team_id",
                        team_options,
                        selected=str(game.away_team_id) if is_edit else "",
                        required=True,
                    ),
                ),
            ),
            # Spielort + Liga + Position
            form_row(
                form_field(
                    "Spielort",
                    text_input(
                        "venue",
                        value=game.venue or "" if is_edit else "",
                    ),
                ),
                form_field(
                    "Liga",
                    select_field(
                        "league_id",
                        league_options,
                        selected=str(game.league_id) if is_edit else "",
                        required=True,
                    ),
                ),
                form_field(
                    "Position",
                    select_field(
                        "position",
                        position_options,
                        selected=game.position if is_edit else "",
                        required=True,
                    ),
                ),
            ),
            # Vergütung + Fahrtkosten + km
            form_row(
                form_field(
                    "Honorar (€)",
                    number_input(
                        "referee_fee",
                        value=str(game.referee_fee) if is_edit else "0",
                        step="0.01",
                    ),
                ),
                form_field(
                    "Fahrtkosten (€)",
                    number_input(
                        "travel_costs",
                        value=str(game.travel_costs) if is_edit else "0",
                        step="0.01",
                    ),
                ),
                form_field(
                    "km",
                    number_input(
                        "km_driven",
                        value=str(game.km_driven) if is_edit else "0",
                        step="1",
                    ),
                ),
            ),
            # Freundschaftsspiel + Bemerkungen
            checkbox_input(
                "exhibition",
                checked=bool(game.exhibition) if is_edit else False,
                field_label="Freundschaftsspiel",
            ),
            form_field(
                "Bemerkungen",
                textarea_input(
                    "remarks",
                    value=game.remarks or "" if is_edit else "",
                    rows=2,
                ),
            ),
            submit_button(),
        ],
    ]

import json

from htpy import a, div, h1, h6, option, select, small, span
from htpy import form as html_form
from markupsafe import Markup

# Nord color palette for charts
NORD_COLORS = [
    "#5E81AC",
    "#81A1C1",
    "#88C0D0",
    "#8FBCBB",
    "#A3BE8C",
    "#EBCB8B",
    "#D08770",
    "#BF616A",
    "#B48EAD",
]


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


def _widget_skeleton(height: str = "200px"):
    """Placeholder skeleton shown on initial load."""
    return div(".placeholder-glow")[
        div(
            ".placeholder.w-100.rounded",
            style=f"height: {height}",
        ),
    ]


def _filter_bar(filter_options, filters):
    """Filter bar. On change: reload filter bar (cascading) + widgets."""
    season_opts = [(s, s) for s in filter_options["seasons"]]
    league_opts = [(str(lg.id), lg.name) for lg in filter_options["leagues"]]
    pos_opts = [(p.position, p.position) for p in filter_options["positions"]]

    return html_form(
        "#dashboard-filters.mb-4",
        method="get",
        action="/dashboard/",
        **{
            "hx-get": "/dashboard/content",
            "hx-target": "#dashboard-content",
            "hx-trigger": "change",
            "hx-push-url": "/dashboard/",
        },
    )[
        div(".row.g-2.align-items-end")[
            div(".col-auto")[
                small(".text-muted")["Saison"],
                _filter_select("season", season_opts, filters.get("season", "")),
            ],
            div(".col-auto")[
                small(".text-muted")["Liga"],
                _filter_select("league_id", league_opts, filters.get("league_id", "")),
            ],
            div(".col-auto")[
                small(".text-muted")["Position"],
                _filter_select("position", pos_opts, filters.get("position", "")),
            ],
            div(".col-auto")[
                a(".btn.btn-sm.btn-outline-secondary", href="/dashboard/")["Zurücksetzen"],
            ],
        ],
    ]


def dashboard_content(
    filter_options, filters, stats=None, position_data=None, monthly_data=None, league_data=None
):
    """Filter bar + widgets. Used for both initial load and htmx updates."""
    has_data = stats is not None

    if has_data:
        return div(id="dashboard-content")[
            div(".container")[
                _filter_bar(filter_options, filters),
                stats_widget(stats),
            ],
            div(".container-dashboard.mt-3")[_charts(position_data, monthly_data, league_data),],
        ]

    # Initial load: filter bar + skeleton that lazy-loads everything
    qs = "&".join(f"{k}={v}" for k, v in filters.items() if v)
    qs_suffix = f"?{qs}" if qs else ""

    return div(
        id="dashboard-content",
        **{
            "hx-get": f"/dashboard/content{qs_suffix}",
            "hx-trigger": "load",
            "hx-swap": "outerHTML",
        },
    )[
        div(".container")[
            _filter_bar(filter_options, filters),
            div(".row.g-2.mb-2")[
                div(".col")[div(".card")[div(".card-body.py-2")[_widget_skeleton("40px")]]],
            ],
        ],
        div(".container-dashboard.mt-3")[
            div(".row.g-3")[
                div(".col-md-3")[div(".card")[div(".card-body")[_widget_skeleton()]]],
                div(".col-md-5")[div(".card")[div(".card-body")[_widget_skeleton()]]],
                div(".col-md-4")[div(".card")[div(".card-body")[_widget_skeleton()]]],
            ],
        ],
    ]


def _widget_card(title, content):
    """Card wrapper for a widget."""
    return div(".card")[
        div(".card-body")[
            h6(".card-title.text-muted")[title],
            content,
        ],
    ]


def _charts(position_data, monthly_data=None, league_data=None):
    """Chart row at wider width."""
    return div(".row.g-3")[
        div(".col-md-3")[_widget_card("Einsätze nach Position", positions_widget(position_data)),],
        div(".col-md-5")[_widget_card("Einsätze nach Monat", monthly_widget(monthly_data)),],
        div(".col-md-4")[_widget_card("Einsätze nach Liga", league_widget(league_data)),],
    ]


def dashboard_page(filter_options, filters):
    """Full dashboard page (initial load — widgets lazy-load)."""
    return [
        div(".container")[h1["Dashboard"]],
        dashboard_content(filter_options, filters),
    ]


def stats_widget(stats):
    """Stats summary cards."""

    def card(label, value):
        return div(".col")[
            div(".card")[
                div(".card-body.py-2.px-3")[
                    small(".text-muted.d-block")[label],
                    span(".fw-bold")[value],
                ],
            ]
        ]

    total = stats["total_fee"] + stats["total_travel"]

    return div(".row.g-2.mb-2")[
        card("Spiele", str(stats["count"])),
        card("Vergütung", _eur(stats["total_fee"])),
        card("Fahrtkosten", _eur(stats["total_travel"])),
        card("Gesamt", _eur(total)),
        card("Kilometer", f"{stats['total_km']:,}".replace(",", ".")),
    ]


CHART_HEIGHT = 350

MONTH_LABELS = [
    "Jan",
    "Feb",
    "Mär",
    "Apr",
    "Mai",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Okt",
    "Nov",
    "Dez",
]


def _render_chart(chart_id, chart_data):
    """Render a Plotly chart with theme-aware colors."""
    json_data = json.dumps(chart_data)
    render_script = (
        f"<script>(function render(){{"
        f"if(typeof Plotly==='undefined'){{setTimeout(render,50);return}}"
        f"var d={json_data};"
        f"var dark=document.documentElement.getAttribute('data-bs-theme')==='dark';"
        f"d.layout.font.color=getComputedStyle(document.body).color;"
        f"var gc=dark?'#3B4252':'#D8DEE9';"
        f"if(d.layout.xaxis)d.layout.xaxis.gridcolor=gc;"
        f"if(d.layout.yaxis)d.layout.yaxis.gridcolor=gc;"
        f"Plotly.newPlot('{chart_id}',d.data,d.layout,"
        f"{{responsive:true,displayModeBar:false}});"
        f"}})()</script>"
    )
    return div[
        div(id=chart_id),
        Markup(render_script),
    ]


def _bar_layout(height, **overrides):
    """Common layout for bar charts."""
    layout = {
        "height": height,
        "margin": {"t": 10, "b": 30, "l": 40, "r": 10},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": "#D8DEE9", "size": 12},
        "xaxis": {"gridcolor": "#3B4252"},
        "yaxis": {"gridcolor": "#3B4252"},
    }
    layout.update(overrides)
    return layout


def positions_widget(position_data):
    """Horizontal bar chart for position distribution."""
    if not position_data:
        return div(".text-muted.text-center.py-4")["Keine Daten"]

    sorted_data = sorted(position_data, key=lambda x: x["count"])
    labels = [d["position"] for d in sorted_data]
    values = [d["count"] for d in sorted_data]

    return _render_chart(
        "chart-positions",
        {
            "data": [
                {
                    "x": values,
                    "y": labels,
                    "type": "bar",
                    "orientation": "h",
                    "marker": {"color": NORD_COLORS[: len(labels)]},
                    "text": values,
                    "textposition": "auto",
                }
            ],
            "layout": _bar_layout(
                CHART_HEIGHT,
                yaxis={
                    "gridcolor": "#3B4252",
                    "categoryorder": "array",
                    "categoryarray": labels,
                    "ticksuffix": "  ",
                },
            ),
        },
    )


def monthly_widget(monthly_data):
    """Stacked column chart: games per month, stacked by position."""
    if not monthly_data:
        return div(".text-muted.text-center.py-4")["Keine Daten"]

    all_months = [f"{i:02d}" for i in range(1, 13)]
    month_labels = [MONTH_LABELS[int(m) - 1] for m in all_months]

    # Collect all positions across months
    all_positions = sorted({pos for counts in monthly_data.values() for pos in counts})

    # One trace per position, stacked
    traces = []
    for idx, pos in enumerate(all_positions):
        values = [monthly_data.get(m, {}).get(pos, 0) for m in all_months]
        traces.append(
            {
                "x": month_labels,
                "y": values,
                "type": "bar",
                "name": pos,
                "marker": {"color": NORD_COLORS[idx % len(NORD_COLORS)]},
            }
        )

    return _render_chart(
        "chart-monthly",
        {
            "data": traces,
            "layout": _bar_layout(
                CHART_HEIGHT,
                barmode="stack",
                showlegend=False,
                margin={"t": 10, "b": 30, "l": 30, "r": 10},
            ),
        },
    )


def league_widget(league_data):
    """Stacked horizontal bar chart: games per league, stacked by month."""
    if not league_data:
        return div(".text-muted.text-center.py-4")["Keine Daten"]

    # Sort leagues ascending (highest at top in horizontal bar)
    league_totals = {lg: sum(months.values()) for lg, months in league_data.items()}
    sorted_leagues = sorted(league_totals, key=lambda lg: league_totals[lg])

    # Collect all months across leagues
    all_months_present = sorted({m for months in league_data.values() for m in months})

    # One trace per month, stacked horizontally
    traces = []
    for idx, month in enumerate(all_months_present):
        label = MONTH_LABELS[int(month) - 1]
        values = [league_data.get(lg, {}).get(month, 0) for lg in sorted_leagues]
        traces.append(
            {
                "x": values,
                "y": sorted_leagues,
                "type": "bar",
                "orientation": "h",
                "name": label,
                "marker": {"color": NORD_COLORS[idx % len(NORD_COLORS)]},
            }
        )

    return _render_chart(
        "chart-leagues",
        {
            "data": traces,
            "layout": _bar_layout(
                CHART_HEIGHT,
                barmode="stack",
                showlegend=False,
                yaxis={
                    "gridcolor": "#3B4252",
                    "categoryorder": "array",
                    "categoryarray": sorted_leagues,
                    "ticksuffix": "  ",
                },
                margin={"t": 10, "b": 30, "l": 120, "r": 10},
            ),
        },
    )

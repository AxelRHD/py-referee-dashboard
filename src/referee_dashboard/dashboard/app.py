import dash
import plotly.graph_objects as go
from dash import Input, Output, dcc, html
from sqlalchemy import func

from referee_dashboard.db import db
from referee_dashboard.models import Game, League

# Nord color palette
NORD_FROST = ["#5E81AC", "#81A1C1", "#88C0D0", "#8FBCBB"]
NORD_AURORA = ["#A3BE8C", "#EBCB8B", "#D08770", "#BF616A", "#B48EAD"]
NORD_COLORS = NORD_FROST + NORD_AURORA
NORD_BG = "rgba(0,0,0,0)"
NORD_TEXT = "#D8DEE9"
NORD_GRID = "#3B4252"


def _base_layout(**overrides):
    """Common Plotly layout settings for Nord theme."""
    layout = dict(
        paper_bgcolor=NORD_BG,
        plot_bgcolor=NORD_BG,
        font=dict(color=NORD_TEXT, size=12),
        margin=dict(t=10, b=30, l=40, r=10),
        xaxis=dict(gridcolor=NORD_GRID),
        yaxis=dict(gridcolor=NORD_GRID),
    )
    layout.update(overrides)
    return layout


def _query_filter_options(server):
    """Query available seasons and leagues for filter dropdowns."""
    with server.app_context():
        seasons = (
            db.session.query(func.substr(Game.game_date, 1, 4))
            .distinct()
            .order_by(func.substr(Game.game_date, 1, 4).desc())
            .all()
        )
        leagues = League.query.order_by(League.sorter, League.name).all()
        return [s[0] for s in seasons], leagues


def create_dash_app(server):
    """Create and mount the Dash app on the Flask server."""
    dash_app = dash.Dash(
        __name__,
        server=server,
        url_base_pathname="/dashboard/",
        external_stylesheets=[
            "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css",
            "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css",
            "/static/css/nord.css",
        ],
    )

    # Inject theme init + toggle into the Dash index HTML
    dash_app.index_string = """<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>{%title%}</title>
    {%css%}
    <script>
        (function() {
            var t = localStorage.getItem('theme') || 'dark';
            document.documentElement.setAttribute('data-bs-theme', t);
        })();
    </script>
</head>
<body>
    {%app_entry%}
    <footer>
        {%config%}
        {%scripts%}
        {%renderer%}
    </footer>
    <script>
        // Set initial icon based on theme
        document.addEventListener('DOMContentLoaded', function() {
            var t = localStorage.getItem('theme') || 'dark';
            var icon = document.getElementById('theme-toggle-icon');
            if (icon) icon.className = t === 'dark' ? 'bi bi-sun' : 'bi bi-moon';
        });
    </script>
</body>
</html>"""

    def serve_layout():
        return _build_layout(server)

    dash_app.layout = serve_layout

    _register_callbacks(dash_app, server)

    if server.debug:
        dash_app.enable_dev_tools(debug=True)

    return dash_app


def _build_layout(server):
    """Build the dashboard layout (called on each page load for fresh data)."""
    seasons, leagues = _query_filter_options(server)

    season_options = [{"label": "Alle Saisons", "value": ""}] + [
        {"label": s, "value": s} for s in seasons
    ]
    league_options = [{"label": "Alle Ligen", "value": ""}] + [
        {"label": lg.name, "value": str(lg.id)} for lg in leagues
    ]

    return html.Div(
        children=[
            # Navbar (same as Flask layout)
            html.Nav(
                className="navbar navbar-expand-lg",
                children=html.Div(
                    className="container",
                    children=[
                        html.A("Referee Dashboard", className="navbar-brand", href="/"),
                        html.Div(
                            className="d-flex align-items-center",
                            children=[
                                html.Div(
                                    className="navbar-nav me-auto",
                                    children=[
                                        html.A("Ligen", className="nav-link", href="/leagues"),
                                        html.A("Teams", className="nav-link", href="/teams"),
                                        html.A("Spiele", className="nav-link", href="/games"),
                                        html.A(
                                            "Dashboard",
                                            className="nav-link active",
                                            href="/dashboard/",
                                        ),
                                    ],
                                ),
                                html.Button(
                                    id="theme-toggle-btn",
                                    className="theme-toggle",
                                    title="Theme wechseln",
                                    children=html.I(
                                        id="theme-toggle-icon",
                                        className="bi bi-sun",
                                    ),
                                ),
                            ],
                        ),
                    ],
                ),
            ),
            # Content
            html.Div(
                className="container mt-4",
                children=[
                    html.H1("Dashboard", className="mb-3"),
                    # Filters
                    html.Div(
                        className="row g-3 mb-4",
                        children=[
                            html.Div(
                                className="col-auto",
                                children=[
                                    html.Small("Saison", className="text-muted d-block"),
                                    dcc.Dropdown(
                                        id="filter-season",
                                        options=season_options,
                                        value="",
                                        style={"width": "150px"},
                                    ),
                                ],
                            ),
                            html.Div(
                                className="col-auto",
                                children=[
                                    html.Small("Liga", className="text-muted d-block"),
                                    dcc.Dropdown(
                                        id="filter-league",
                                        options=league_options,
                                        value="",
                                        style={"width": "250px"},
                                    ),
                                ],
                            ),
                        ],
                    ),
                    # Charts row
                    html.Div(
                        className="row g-3",
                        children=[
                            # Position chart
                            html.Div(
                                className="col-md-6",
                                children=[
                                    html.Div(
                                        className="card",
                                        children=html.Div(
                                            className="card-body",
                                            children=[
                                                html.H6(
                                                    "Einsätze nach Position",
                                                    className="card-title text-muted",
                                                ),
                                                dcc.Graph(
                                                    id="chart-positions",
                                                    config={"displayModeBar": False},
                                                ),
                                            ],
                                        ),
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ]
    )


def _register_callbacks(dash_app, server):
    """Register Dash callbacks for interactivity."""

    # Theme toggle (clientside, no server roundtrip)
    dash_app.clientside_callback(
        """
        function(n_clicks) {
            if (!n_clicks) return window.dash_clientside.no_update;
            var html = document.documentElement;
            var dark = html.getAttribute('data-bs-theme') === 'dark';
            var theme = dark ? 'light' : 'dark';
            html.setAttribute('data-bs-theme', theme);
            localStorage.setItem('theme', theme);
            var icon = document.getElementById('theme-toggle-icon');
            if (icon) {
                icon.className = theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon';
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output("theme-toggle-btn", "title"),
        Input("theme-toggle-btn", "n_clicks"),
        prevent_initial_call=True,
    )

    @dash_app.callback(
        Output("chart-positions", "figure"),
        Input("filter-season", "value"),
        Input("filter-league", "value"),
    )
    def update_position_chart(season, league_id):
        with server.app_context():
            query = db.session.query(Game.position, func.count().label("count"))

            if season:
                query = query.filter(Game.game_date.like(f"{season}-%"))
            if league_id:
                query = query.filter(Game.league_id == int(league_id))

            query = query.group_by(Game.position)
            results = query.all()

            if not results:
                fig = go.Figure()
                fig.update_layout(**_base_layout(height=300))
                fig.add_annotation(
                    text="Keine Daten",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                )
                return fig

            # Sort ascending so highest is at top in horizontal bar
            results = sorted(results, key=lambda r: r.count)

            labels = [r.position for r in results]
            values = [r.count for r in results]
            colors = NORD_COLORS[: len(labels)]

            fig = go.Figure(
                go.Bar(
                    x=values,
                    y=labels,
                    orientation="h",
                    marker_color=colors,
                    text=values,
                    textposition="auto",
                )
            )

            fig.update_layout(
                **_base_layout(
                    height=max(200, len(labels) * 40 + 40),
                    yaxis=dict(
                        gridcolor=NORD_GRID,
                        categoryorder="array",
                        categoryarray=labels,
                        ticksuffix="  ",
                    ),
                )
            )

            return fig

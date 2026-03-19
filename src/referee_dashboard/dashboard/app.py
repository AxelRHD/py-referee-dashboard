import dash
from dash import html


def create_dash_app(server):
    """Create and mount the Dash app on the Flask server."""
    dash_app = dash.Dash(
        __name__,
        server=server,
        url_base_pathname="/dashboard/",
    )

    dash_app.layout = html.Div(
        [
            html.H1("Referee Dashboard"),
            html.P("Statistiken und Auswertungen werden hier angezeigt."),
        ]
    )

    return dash_app

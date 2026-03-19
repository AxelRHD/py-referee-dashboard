from htpy import a, body, button, div, head, html, i, link, meta, nav, script, title
from markupsafe import Markup

# Inline script to set theme before render to avoid flash
_theme_init_script = Markup("""<script>
(function() {
    var t = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-bs-theme', t);
})();
</script>""")

# Theme toggle with Surreal.js (runs after DOM + Surreal are loaded)
_theme_toggle_script = Markup("""<script>
me('#theme-toggle').on('click', () => {
    var dark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    var theme = dark ? 'light' : 'dark';
    document.documentElement.setAttribute('data-bs-theme', theme);
    localStorage.setItem('theme', theme);
    me('#icon-sun').classToggle('d-none');
    me('#icon-moon').classToggle('d-none');
});
</script>""")


def base_page(page_title: str, *content, container: str = "container"):
    """Base HTML layout. Set container='' to manage layout in content."""
    return html[
        head[
            meta(charset="utf-8"),
            meta(name="viewport", content="width=device-width, initial-scale=1"),
            title[f"{page_title} — Referee Dashboard"],
            link(
                rel="stylesheet",
                href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css",
            ),
            link(
                rel="stylesheet",
                href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css",
            ),
            link(rel="stylesheet", href="/static/css/nord.css"),
            _theme_init_script,
        ],
        body[
            _navbar(),
            div(f".{container}.mt-4")[content] if container else div(".mt-4")[content],
            script(
                src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js",
            ),
            script(src="https://cdn.jsdelivr.net/npm/htmx.org@2/dist/htmx.min.js"),
            script(
                src="https://cdn.jsdelivr.net/npm/plotly.js-basic-dist-min@2/plotly-basic.min.js",
            ),
            script(
                src="https://cdn.jsdelivr.net/gh/gnat/surreal@main/surreal.js",
            ),
            _theme_toggle_script,
        ],
    ]


def _navbar():
    return nav(".navbar.navbar-expand-lg")[
        div(".container")[
            a(".navbar-brand", href="/")["Referee Dashboard"],
            div(".d-flex.align-items-center")[
                div(".navbar-nav.me-auto")[
                    a(".nav-link", href="/dashboard/")["Dashboard"],
                    a(".nav-link", href="/games")["Spiele"],
                    a(".nav-link", href="/teams")["Teams"],
                    a(".nav-link", href="/leagues")["Ligen"],
                ],
                _theme_toggle(),
            ],
        ]
    ]


def _theme_toggle():
    # Default is dark → show sun icon, hide moon icon
    return button(
        "#theme-toggle.theme-toggle",
        title="Theme wechseln",
    )[
        i("#icon-sun.bi.bi-sun"),
        i("#icon-moon.bi.bi-moon.d-none"),
    ]

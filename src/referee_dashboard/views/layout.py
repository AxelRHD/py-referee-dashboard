from htpy import a, body, button, div, head, html, i, link, meta, nav, script, title
from markupsafe import Markup

# Inline script to set theme before render to avoid flash
_theme_init_script = Markup("""<script>
(function() {
    var t = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-bs-theme', t);
})();
</script>""")

# Alpine.js theme toggle component
_theme_toggle_script = Markup("""<script>
document.addEventListener('alpine:init', () => {
    Alpine.data('themeToggle', () => ({
        dark: document.documentElement.getAttribute('data-bs-theme') === 'dark',
        toggle() {
            this.dark = !this.dark;
            var theme = this.dark ? 'dark' : 'light';
            document.documentElement.setAttribute('data-bs-theme', theme);
            localStorage.setItem('theme', theme);
            window.dispatchEvent(new Event('theme-changed'));
        }
    }));
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
            # alpine:init listeners must come before Alpine.js
            _theme_toggle_script,
            script(src="https://cdn.jsdelivr.net/npm/alpinejs@3/dist/cdn.min.js"),
        ],
    ]


def _navbar():
    return nav(".navbar.navbar-expand-lg.sticky-top")[
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
    return div(**{"x-data": "themeToggle"})[
        button(
            ".theme-toggle",
            **{"@click": "toggle()"},
            title="Theme wechseln",
        )[
            i(".bi.bi-sun", {"x-show": "dark"}),
            i(".bi.bi-moon", {"x-show": "!dark"}),
        ],
    ]

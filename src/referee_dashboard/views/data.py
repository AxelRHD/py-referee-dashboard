from htpy import a, div, h1, h5, label, option, select, textarea
from htpy import form as html_form
from htpy import input as html_input
from markupsafe import Markup

from referee_dashboard.views.components import submit_button

_TOGGLE_ENTITY_JS = Markup("""<script>
document.querySelectorAll('.format-toggle').forEach(function(sel) {
    var form = sel.closest('form');
    var entity = form.querySelector('.entity-group');
    function toggle() { entity.classList.toggle('d-none', sel.value !== 'csv'); }
    sel.addEventListener('change', toggle);
    toggle();
});
</script>""")


def data_page():
    """View: data management page."""
    return [
        h1["Datenverwaltung"],
        # Export section
        div(".card.mb-4")[
            div(".card-body")[
                h5(".card-title")["Export"],
                div(".d-flex.gap-2")[
                    a(".btn.btn-outline-primary", href="/data/dump")[
                        "SQLite-Dump (Schema + Daten)"
                    ],
                    a(".btn.btn-outline-primary", href="/data/export-all")[
                        "Alle Daten (nur INSERTs)"
                    ],
                ],
            ],
        ],
        # File import
        div(".card.mb-4")[
            div(".card-body")[
                h5(".card-title")["Datei importieren"],
                html_form(
                    method="post",
                    action="/data/import",
                    enctype="multipart/form-data",
                )[
                    div(".row.g-3.align-items-end")[
                        div(".col-auto")[
                            label(".form-label")["Format"],
                            _format_select(),
                        ],
                        div(".col-auto.entity-group.d-none")[
                            label(".form-label")["Entity"],
                            _entity_select(),
                        ],
                        div(".col")[
                            label(".form-label")["Datei"],
                            html_input(
                                ".form-control",
                                type="file",
                                name="file",
                                accept=".sql,.csv,.txt",
                            ),
                        ],
                        div(".col-auto")[submit_button("Importieren")],
                    ],
                ],
            ],
        ],
        # Textarea import
        div(".card.mb-4")[
            div(".card-body")[
                h5(".card-title")["Direkt einfügen"],
                html_form(method="post", action="/data/paste")[
                    div(".row.g-3.mb-3")[
                        div(".col-auto")[
                            label(".form-label")["Format"],
                            _format_select(),
                        ],
                        div(".col-auto.entity-group.d-none")[
                            label(".form-label")["Entity"],
                            _entity_select(),
                        ],
                    ],
                    textarea(
                        ".form-control.font-monospace",
                        name="content",
                        rows="12",
                        placeholder="SQL-Statements oder CSV-Daten hier einfügen...",
                    ),
                    div(".mt-3")[submit_button("Ausführen")],
                ],
            ],
        ],
        _TOGGLE_ENTITY_JS,
    ]


def _format_select():
    return select(".form-select.format-toggle", name="format")[
        option(value="sql")["SQL"],
        option(value="csv")["CSV"],
    ]


def _entity_select():
    return select(".form-select", name="entity")[
        option(value="games")["Spiele"],
        option(value="teams")["Teams"],
        option(value="leagues")["Ligen"],
    ]

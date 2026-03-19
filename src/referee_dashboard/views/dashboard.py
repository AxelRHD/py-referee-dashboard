from htpy import (
    button,
    div,
    h1,
    h6,
    i,
    input,
    label,
    option,
    select,
    small,
    span,
    template,
)
from markupsafe import Markup

NORD_COLORS_JS = (
    "['#5E81AC','#81A1C1','#88C0D0','#8FBCBB','#A3BE8C','#EBCB8B','#D08770','#BF616A','#B48EAD']"
)

MONTH_LABELS_JS = "['Jan','Feb','Mär','Apr','Mai','Jun','Jul','Aug','Sep','Okt','Nov','Dez']"


def _eur_js():
    """JS method for German EUR formatting (inside Alpine object)."""
    return """
    eur(v) {
        return v.toFixed(2).replace('.', ',').replace(/\\B(?=(\\d{3})+(?!\\d))/g, '.') + ' €';
    },
    """


def _plotly_layout_js():
    """JS method for base Plotly layout (inside Alpine object)."""
    return """
    baseLayout(height, extra) {
        var dark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
        var fg = getComputedStyle(document.body).color;
        var gc = dark ? '#3B4252' : '#D8DEE9';
        var layout = {
            height: height,
            margin: {t: 10, b: 30, l: 40, r: 10},
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: {color: fg, size: 12},
            xaxis: {gridcolor: gc},
            yaxis: {gridcolor: gc},
        };
        return Object.assign(layout, extra || {});
    },
    """


def _stat_card(label, x_text):
    """Single stat card with Alpine.js x-text binding."""
    return div(".card")[
        div(".card-body.py-2.px-3")[
            small(".text-muted.d-block")[label],
            span(".fw-bold", **{"x-text": x_text}),
        ]
    ]


def _collapsible_section(section_id, icon_class, title, *content):
    """Collapsible card section with Bootstrap collapse."""
    return div(".card.mt-3")[
        div(
            ".card-header.d-flex.justify-content-between.align-items-center.py-2",
            role="button",
            **{
                "data-bs-toggle": "collapse",
                "data-bs-target": f"#{section_id}",
                "aria-expanded": "true",
            },
        )[
            h6(".mb-0.text-muted")[i(f".{icon_class}.me-1"), title],
            i(".bi.bi-chevron-down.text-muted"),
        ],
        div(".collapse.show", id=section_id)[div(".card-body")[content],],
    ]


def _widget_card(title, chart_id):
    """Card with a title and a Plotly chart container."""
    return div(".card.h-100")[
        div(".card-body")[
            h6(".card-title.text-muted")[title],
            div(id=chart_id),
        ]
    ]


def _alpine_select(label, x_model, options_template):
    """Filter select with Alpine.js dynamic options."""
    return div(".mb-3")[
        small(".text-muted.d-block.mb-1")[label],
        select(
            ".form-select.form-select-sm",
            **{"x-model": x_model},
        )[
            option(value="")["Alle"],
            options_template,
        ],
    ]


def dashboard_page(seasons, default_season):
    """Full dashboard page with Alpine.js data component."""
    season_options = [option(value=s, selected=(s == default_season))[s] for s in seasons]

    alpine_script = Markup(f"""<script>
    document.addEventListener('alpine:init', () => {{
        Alpine.data('dashboard', () => ({{
            season: '{default_season}',
            games: [],
            positions: [],
            availableLeagues: [],
            availablePositions: [],
            filterLeague: '',
            filterPosition: '',
            loading: true,
            view: 'year',
            onlyCompleted: false,
            today: new Date().toISOString().slice(0, 10),

            get filtered() {{
                return this.games.filter(g => {{
                    if (this.onlyCompleted && g.date >= this.today) return false;
                    if (this.filterLeague && g.league_id != this.filterLeague) return false;
                    if (this.filterPosition && g.position !== this.filterPosition) return false;
                    return true;
                }});
            }},

            get stats() {{
                var f = this.filtered;
                var fee = f.reduce((s, g) => s + g.fee, 0);
                var travel = f.reduce((s, g) => s + g.travel, 0);
                return {{
                    count: f.length,
                    fee: fee,
                    travel: travel,
                    total: fee + travel,
                    km: f.reduce((s, g) => s + g.km, 0),
                }};
            }},

            init() {{
                this.loadSeason();
                this.$watch('season', () => this.loadSeason());
                this.$watch('filtered', () => this.renderCharts());
                this.$watch('filterLeague', () => this.renderPositionChart());
                this.$watch('onlyCompleted', () => this.renderCharts());
                window.addEventListener('theme-changed', () => {{
                    this.$nextTick(() => this.renderCharts());
                }});
            }},

            async loadSeason() {{
                this.loading = true;
                this.filterLeague = '';
                this.filterPosition = '';
                var res = await fetch('/dashboard/api/data/' + this.season);
                var data = await res.json();
                this.games = data.games;
                this.positions = data.positions;
                this.availableLeagues = data.available_leagues;
                this.availablePositions = data.available_positions;
                this.loading = false;
                this.$nextTick(() => this.renderCharts());
            }},

            renderCharts() {{
                this.renderPositionChart();
                this.renderMonthlyChart();
                this.renderLeagueChart();
                this.renderFeeBar('chart-fee-total', g => g.fee + g.travel);
                this.renderFeeBar('chart-fee-base', g => g.fee);
                this.renderFeeBar('chart-fee-travel', g => g.travel);
            }},

            {_eur_js()}
            {_plotly_layout_js()}

            stackAnnotations(categories, totals, horizontal, fmt) {{
                var fg = getComputedStyle(document.body).color;
                return categories.map((cat, i) => {{
                    var val = totals[i] || 0;
                    if (val === 0) return null;
                    var label = fmt ? fmt(val) : String(val);
                    return horizontal ? {{
                        x: val, y: cat, text: label,
                        xanchor: 'left', yanchor: 'middle',
                        xshift: 5, showarrow: false,
                        font: {{size: 11, color: fg}},
                    }} : {{
                        x: cat, y: val, text: label,
                        xanchor: 'center', yanchor: 'bottom',
                        yshift: 3, showarrow: false,
                        font: {{size: 11, color: fg}},
                    }};
                }}).filter(a => a);
            }},

            renderPositionChart() {{
                var colors = {NORD_COLORS_JS};
                var games = this.games.filter(g => {{
                    if (this.onlyCompleted && g.date >= this.today) return false;
                    if (this.filterLeague && g.league_id != this.filterLeague) return false;
                    return true;
                }});
                var counts = {{}};
                games.forEach(g => {{ counts[g.position] = (counts[g.position] || 0) + 1; }});
                var entries = Object.entries(counts).sort((a, b) => a[1] - b[1]);
                var labels = entries.map(e => e[0]);
                var values = entries.map(e => e[1]);
                Plotly.newPlot('chart-positions', [{{
                    x: values, y: labels, type: 'bar', orientation: 'h',
                    marker: {{color: labels.map((_, i) => colors[i % colors.length])}},
                    text: values, textposition: 'auto',
                }}], this.baseLayout(350, {{
                    yaxis: {{
                        gridcolor: this.baseLayout(0).yaxis.gridcolor,
                        categoryorder: 'array', categoryarray: labels,
                        ticksuffix: '  ',
                    }},
                }}), {{responsive: true, displayModeBar: false}});
            }},

            renderMonthlyChart() {{
                var colors = {NORD_COLORS_JS};
                var allMonths = {MONTH_LABELS_JS};
                var f = this.filtered;
                var raw = {{}};
                var activeMonths = new Set();
                f.forEach(g => {{
                    var m = parseInt(g.month) - 1;
                    raw[g.position] = raw[g.position] || {{}};
                    raw[g.position][m] = (raw[g.position][m] || 0) + 1;
                    activeMonths.add(m);
                }});
                // Only months that have games, in order
                var months = [...activeMonths].sort((a, b) => a - b);
                var monthLabels = months.map(m => allMonths[m]);

                var traces = this.positions
                    .filter(p => raw[p])
                    .map((p, idx) => ({{
                        x: monthLabels,
                        y: months.map(m => raw[p][m] || 0),
                        type: 'bar', name: p,
                        marker: {{color: colors[idx % colors.length]}},
                    }}));

                var totals = months.map(m => {{
                    var t = 0;
                    this.positions.forEach(p => {{
                        t += (raw[p] && raw[p][m]) || 0;
                    }});
                    return t;
                }});

                Plotly.newPlot('chart-monthly', traces, this.baseLayout(350, {{
                    barmode: 'stack',
                    showlegend: true,
                    legend: {{font: {{size: 10}}}},
                    margin: {{t: 20, b: 30, l: 30, r: 10}},
                    annotations: this.stackAnnotations(monthLabels, totals, false),
                }}), {{responsive: true, displayModeBar: false}});
            }},

            renderLeagueChart() {{
                var colors = {NORD_COLORS_JS};
                var monthLabels = {MONTH_LABELS_JS};
                var games = this.games.filter(g => {{
                    if (this.onlyCompleted && g.date >= this.today) return false;
                    if (this.filterPosition && g.position !== this.filterPosition) return false;
                    return true;
                }});
                var leagueData = {{}};
                var monthsPresent = new Set();
                games.forEach(g => {{
                    leagueData[g.league] = leagueData[g.league] || {{}};
                    var m = parseInt(g.month) - 1;
                    leagueData[g.league][m] = (leagueData[g.league][m] || 0) + 1;
                    monthsPresent.add(m);
                }});
                var leagues = Object.entries(leagueData)
                    .map(([lg, months]) => [lg, Object.values(months).reduce((a, b) => a + b, 0)])
                    .sort((a, b) => a[1] - b[1])
                    .map(e => e[0]);
                var sortedMonths = [...monthsPresent].sort((a, b) => a - b);
                var traces = sortedMonths.map((m, i) => ({{
                    x: leagues.map(lg => leagueData[lg][m] || 0),
                    y: leagues,
                    type: 'bar', orientation: 'h', name: monthLabels[m],
                    marker: {{color: colors[i % colors.length]}},
                }}));
                var leagueTotals = leagues.map(lg => {{
                    return Object.values(leagueData[lg]).reduce((a, b) => a + b, 0);
                }});
                Plotly.newPlot('chart-leagues', traces, this.baseLayout(350, {{
                    barmode: 'stack',
                    showlegend: true,
                    legend: {{font: {{size: 10}}}},
                    yaxis: {{
                        gridcolor: this.baseLayout(0).yaxis.gridcolor,
                        categoryorder: 'array', categoryarray: leagues,
                        ticksuffix: '  ',
                    }},
                    margin: {{t: 10, b: 30, l: 120, r: 30}},
                    annotations: this.stackAnnotations(leagues, leagueTotals, true),
                }}), {{responsive: true, displayModeBar: false}});
            }},

            renderFeeBar(chartId, valueFn) {{
                var colors = {NORD_COLORS_JS};
                var months = {MONTH_LABELS_JS};
                var f = this.filtered;
                var data = {{}};
                var monthsPresent = new Set();
                f.forEach(g => {{
                    var m = parseInt(g.month) - 1;
                    data[g.position] = data[g.position] || {{}};
                    data[g.position][m] = (data[g.position][m] || 0) + valueFn(g);
                    monthsPresent.add(m);
                }});
                var sortedMonths = [...monthsPresent].sort((a, b) => a - b);
                var monthLabels = sortedMonths.map(m => months[m] + ' ' + this.season);
                var traces = this.positions
                    .filter(p => data[p])
                    .map((p, i) => ({{
                        y: monthLabels,
                        x: sortedMonths.map(m => data[p][m] || 0),
                        type: 'bar', orientation: 'h', name: p,
                        marker: {{color: colors[i % colors.length]}},
                    }}));
                var totalArr = sortedMonths.map(m => {{
                    var t = 0;
                    this.positions.forEach(p => {{
                        t += (data[p] && data[p][m]) || 0;
                    }});
                    return t;
                }});
                var fmtEur = v => Math.round(v) + ' €';
                Plotly.newPlot(chartId, traces, this.baseLayout(350, {{
                    barmode: 'stack',
                    showlegend: true,
                    legend: {{font: {{size: 10}}}},
                    yaxis: {{
                        gridcolor: this.baseLayout(0).yaxis.gridcolor,
                        categoryorder: 'array',
                        categoryarray: monthLabels,
                        ticksuffix: '  ',
                    }},
                    margin: {{t: 10, b: 30, l: 90, r: 60}},
                    annotations: this.stackAnnotations(
                        monthLabels, totalArr, true, fmtEur
                    ),
                }}), {{responsive: true, displayModeBar: false}});
            }},
        }}));
    }});
    </script>""")

    # --- Layout ---

    # Sidebar: view toggle, filters, stats
    sidebar = div(".col-md-2")[
        div(style="position:sticky;top:4rem")[
            h1(".h5.mb-3")["Dashboard"],
            # View toggle
            div(".btn-group.btn-group-sm.w-100.mb-3", role="group")[
                button(
                    ".btn",
                    type="button",
                    **{
                        ":class": "view === 'year' ? 'btn-primary' : 'btn-outline-primary'",
                        "@click": "view = 'year'",
                    },
                )["Jahr"],
                button(
                    ".btn",
                    type="button",
                    **{
                        ":class": "view === 'overview' ? 'btn-primary' : 'btn-outline-primary'",
                        "@click": "view = 'overview'",
                    },
                )["Übersicht"],
            ],
            # Year view: filters + stats
            div({"x-show": "view === 'year'"})[
                div(".mb-3")[
                    small(".text-muted.d-block.mb-1")["Saison"],
                    select(
                        ".form-select.form-select-sm",
                        **{"x-model": "season"},
                    )[season_options],
                ],
                _alpine_select(
                    "Liga",
                    "filterLeague",
                    template({"x-for": "lg in availableLeagues", ":key": "lg.id"})[
                        option({":value": "lg.id", "x-text": "lg.name"}),
                    ],
                ),
                _alpine_select(
                    "Position",
                    "filterPosition",
                    template({"x-for": "p in availablePositions", ":key": "p"})[
                        option({":value": "p", "x-text": "p"}),
                    ],
                ),
                div(".form-check.mb-3")[
                    input(
                        "#only-completed.form-check-input",
                        type="checkbox",
                        **{"x-model": "onlyCompleted"},
                    ),
                    label(
                        ".form-check-label.small",
                        for_="only-completed",
                    )["Nur geleitet"],
                ],
                div(".d-flex.flex-column.gap-2")[
                    _stat_card("Spiele", "stats.count"),
                    _stat_card("Gesamt", "eur(stats.total)"),
                    _stat_card("Vergütung", "eur(stats.fee)"),
                    _stat_card("Fahrtkosten", "eur(stats.travel)"),
                    _stat_card("Kilometer", "stats.km.toLocaleString('de-DE')"),
                ],
            ],
            # Overview placeholder
            div(
                ".text-muted.small.py-3",
                {"x-show": "view === 'overview'"},
            )["Übersicht wird geladen..."],
        ],
    ]

    # Charts area (year view only)
    charts = div(".col-md-10", {"x-show": "view === 'year'"})[
        _collapsible_section(
            "charts-body",
            "bi.bi-bar-chart-fill",
            "Einsätze",
            div(".row.g-3")[
                div(".col-md-3")[_widget_card("nach Position", "chart-positions")],
                div(".col-md-5")[_widget_card("nach Monat", "chart-monthly")],
                div(".col-md-4")[_widget_card("nach Liga", "chart-leagues")],
            ],
        ),
        _collapsible_section(
            "fees-body",
            "bi.bi-currency-euro",
            "Vergütung",
            div(".row.g-3")[
                div(".col-md-4")[_widget_card("Gesamt", "chart-fee-total")],
                div(".col-md-4")[_widget_card("Pauschale", "chart-fee-base")],
                div(".col-md-4")[_widget_card("Fahrtkosten", "chart-fee-travel")],
            ],
        ),
    ]

    return [
        div(
            "#dashboard-app.container-dashboard",
            {"x-data": "dashboard"},
        )[
            # Loading spinner
            div(
                ".text-center.py-5",
                {"x-show": "loading"},
            )[
                div(".spinner-border.text-secondary", role="status")[
                    span(".visually-hidden")["Laden..."],
                ],
            ],
            # Content
            div({"x-show": "!loading", "x-cloak": ""})[div(".row.g-4")[sidebar, charts],],
        ],
        alpine_script,
    ]

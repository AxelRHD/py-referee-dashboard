from htpy import div, h1, h6, option, select, small
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


def dashboard_page(seasons, default_season):
    """Full dashboard page with Alpine.js data component."""
    season_options = [option(value=s, selected=(s == default_season))[s] for s in seasons]

    alpine_script = Markup(f"""<script>
    document.addEventListener('alpine:init', () => {{
        Alpine.data('dashboard', () => ({{
            // State
            season: '{default_season}',
            games: [],
            positions: [],
            availableLeagues: [],
            availablePositions: [],
            filterLeague: '',
            filterPosition: '',
            loading: true,

            // Computed
            get filtered() {{
                return this.games.filter(g => {{
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

            // Init
            init() {{
                this.loadSeason();
                this.$watch('season', () => this.loadSeason());
                this.$watch('filtered', () => this.renderCharts());
                this.$watch('filterLeague', () => this.renderPositionChart());
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

            // Annotations for stacked bar totals
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
                // Position chart ignores position filter
                var games = this.games.filter(g => {{
                    if (this.filterLeague && g.league_id != this.filterLeague) return false;
                    return true;
                }});
                var counts = {{}};
                games.forEach(g => {{ counts[g.position] = (counts[g.position] || 0) + 1; }});

                // Sort by count ascending (highest at top)
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
                var months = {MONTH_LABELS_JS};
                var f = this.filtered;

                // Group by month + position
                var data = {{}};
                f.forEach(g => {{
                    var m = parseInt(g.month) - 1;
                    data[g.position] = data[g.position] || new Array(12).fill(0);
                    data[g.position][m]++;
                }});

                // Use DB position order
                var traces = this.positions
                    .filter(p => data[p])
                    .map((p, i) => ({{
                        x: months, y: data[p], type: 'bar', name: p,
                        marker: {{color: colors[i % colors.length]}},
                    }}));

                // Calculate totals per month for annotations
                var totals = months.map((_, m) => {{
                    var t = 0;
                    this.positions.forEach(p => {{ t += (data[p] && data[p][m]) || 0; }});
                    return t;
                }});

                Plotly.newPlot('chart-monthly', traces, this.baseLayout(350, {{
                    barmode: 'stack',
                    showlegend: true,
                    legend: {{font: {{size: 10}}}},
                    margin: {{t: 20, b: 30, l: 30, r: 10}},
                    annotations: this.stackAnnotations(months, totals, false),
                }}), {{responsive: true, displayModeBar: false}});
            }},

            renderLeagueChart() {{
                var colors = {NORD_COLORS_JS};
                var monthLabels = {MONTH_LABELS_JS};
                // League chart ignores league filter
                var games = this.games.filter(g => {{
                    if (this.filterPosition && g.position !== this.filterPosition) return false;
                    return true;
                }});

                // Group by league + month
                var leagueData = {{}};
                var monthsPresent = new Set();
                games.forEach(g => {{
                    leagueData[g.league] = leagueData[g.league] || {{}};
                    var m = parseInt(g.month) - 1;
                    leagueData[g.league][m] = (leagueData[g.league][m] || 0) + 1;
                    monthsPresent.add(m);
                }});

                // Sort leagues by total ascending
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

                // Totals per league
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

                // Group by month + position
                var data = {{}};
                var monthsPresent = new Set();
                f.forEach(g => {{
                    var m = parseInt(g.month) - 1;
                    data[g.position] = data[g.position] || {{}};
                    data[g.position][m] = (data[g.position][m] || 0) + valueFn(g);
                    monthsPresent.add(m);
                }});

                // Months descending (newest on top)
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

                // Calculate totals per month for annotations
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

    return [
        div(
            "#dashboard-app.container-dashboard",
            **{"x-data": "dashboard"},
        )[
            # Loading spinner
            Markup("""
            <div x-show="loading" class="text-center py-5">
                <div class="spinner-border text-secondary" role="status">
                    <span class="visually-hidden">Laden...</span>
                </div>
            </div>
            """),
            # Content (hidden while loading)
            Markup('<div x-show="!loading" x-cloak>'),
            # Sidebar + Content layout
            div(".row.g-4")[
                # Left sidebar: filters + stats (sticky)
                div(".col-md-2")[
                    div(
                        style="position:sticky;top:4rem",
                    )[
                        h1(".h5.mb-3")["Dashboard"],
                        div(".mb-3")[
                            small(".text-muted.d-block.mb-1")["Saison"],
                            select(
                                ".form-select.form-select-sm",
                                **{"x-model": "season"},
                            )[season_options],
                        ],
                        Markup("""
                    <div class="mb-3">
                        <small class="text-muted d-block mb-1">Liga</small>
                        <select class="form-select form-select-sm"
                                x-model="filterLeague">
                            <option value="">Alle</option>
                            <template x-for="lg in availableLeagues"
                                      :key="lg.id">
                                <option :value="lg.id"
                                        x-text="lg.name"></option>
                            </template>
                        </select>
                    </div>
                    <div class="mb-4">
                        <small class="text-muted d-block mb-1">Position</small>
                        <select class="form-select form-select-sm"
                                x-model="filterPosition">
                            <option value="">Alle</option>
                            <template x-for="p in availablePositions"
                                      :key="p">
                                <option :value="p" x-text="p"></option>
                            </template>
                        </select>
                    </div>
                    """),
                        # Stats stacked vertically
                        Markup("""
                    <div class="d-flex flex-column gap-2">
                        <div class="card"><div class="card-body py-2 px-3">
                            <small class="text-muted d-block">Spiele</small>
                            <span class="fw-bold" x-text="stats.count">
                            </span>
                        </div></div>
                        <div class="card"><div class="card-body py-2 px-3">
                            <small class="text-muted d-block">Gesamt</small>
                            <span class="fw-bold" x-text="eur(stats.total)">
                            </span>
                        </div></div>
                        <div class="card"><div class="card-body py-2 px-3">
                            <small class="text-muted d-block">Vergütung</small>
                            <span class="fw-bold" x-text="eur(stats.fee)">
                            </span>
                        </div></div>
                        <div class="card"><div class="card-body py-2 px-3">
                            <small class="text-muted d-block">Fahrtkosten
                            </small>
                            <span class="fw-bold" x-text="eur(stats.travel)">
                            </span>
                        </div></div>
                        <div class="card"><div class="card-body py-2 px-3">
                            <small class="text-muted d-block">Kilometer</small>
                            <span class="fw-bold"
                                x-text="stats.km.toLocaleString('de-DE')">
                            </span>
                        </div></div>
                    </div>
                    """),
                    ],  # close sticky div
                ],
                # Right: chart sections
                div(".col-md-10")[
                    # Charts in collapsible section
                    Markup("""
                <div class="card">
                    <div class="card-header d-flex justify-content-between
                                align-items-center py-2"
                         role="button"
                         data-bs-toggle="collapse"
                         data-bs-target="#charts-body"
                         aria-expanded="true">
                        <h6 class="mb-0 text-muted">
                            <i class="bi bi-bar-chart-fill me-1"></i>
                            Einsätze
                        </h6>
                        <i class="bi bi-chevron-down text-muted"></i>
                    </div>
                    <div class="collapse show" id="charts-body">
                        <div class="card-body">
                """),
                    div(".row.g-3")[
                        div(".col-md-3")[
                            div(".card.h-100")[
                                div(".card-body")[
                                    h6(".card-title.text-muted")["nach Position"],
                                    div(id="chart-positions"),
                                ]
                            ],
                        ],
                        div(".col-md-5")[
                            div(".card.h-100")[
                                div(".card-body")[
                                    h6(".card-title.text-muted")["nach Monat"],
                                    div(id="chart-monthly"),
                                ]
                            ],
                        ],
                        div(".col-md-4")[
                            div(".card.h-100")[
                                div(".card-body")[
                                    h6(".card-title.text-muted")["nach Liga"],
                                    div(id="chart-leagues"),
                                ]
                            ],
                        ],
                    ],
                    Markup("</div></div></div>"),
                    # Vergütung section
                    Markup("""
                <div class="card">
                    <div class="card-header d-flex justify-content-between
                                align-items-center py-2"
                         role="button"
                         data-bs-toggle="collapse"
                         data-bs-target="#fees-body"
                         aria-expanded="true">
                        <h6 class="mb-0 text-muted">
                            <i class="bi bi-currency-euro me-1"></i>
                            Vergütung
                        </h6>
                        <i class="bi bi-chevron-down text-muted"></i>
                    </div>
                    <div class="collapse show" id="fees-body">
                        <div class="card-body">
                """),
                    div(".row.g-3")[
                        div(".col-md-4")[
                            div(".card.h-100")[
                                div(".card-body")[
                                    h6(".card-title.text-muted")["Gesamt"],
                                    div(id="chart-fee-total"),
                                ]
                            ],
                        ],
                        div(".col-md-4")[
                            div(".card.h-100")[
                                div(".card-body")[
                                    h6(".card-title.text-muted")["Pauschale"],
                                    div(id="chart-fee-base"),
                                ]
                            ],
                        ],
                        div(".col-md-4")[
                            div(".card.h-100")[
                                div(".card-body")[
                                    h6(".card-title.text-muted")["Fahrtkosten"],
                                    div(id="chart-fee-travel"),
                                ]
                            ],
                        ],
                    ],
                    Markup("</div></div></div>"),
                ],  # close col-md-10
            ],  # close row
            Markup("</div>"),  # close x-show="!loading" wrapper
        ],
        alpine_script,
    ]

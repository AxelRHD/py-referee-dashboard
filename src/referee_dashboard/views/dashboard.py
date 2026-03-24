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
    table,
    tbody,
    td,
    template,
    th,
    thead,
    tr,
)
from markupsafe import Markup

NORD_COLORS_JS = (
    "['#5E81AC','#81A1C1','#88C0D0','#8FBCBB','#A3BE8C','#EBCB8B','#D08770','#BF616A','#B48EAD']"
)

MONTH_LABELS_JS = "['Jan','Feb','Mär','Apr','Mai','Jun','Jul','Aug','Sep','Okt','Nov','Dez']"


def _fmt_date_js():
    """JS method for German date formatting (inside Alpine object)."""
    return """
    fmtDate(d) {
        if (!d || d.length < 10) return d;
        return d.slice(8,10) + '.' + d.slice(5,7) + '.' + d.slice(0,4);
    },
    """


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


def _stat_row(left_label, left_text, right_label, right_text):
    """Two stats side by side in one card."""
    return div(".card")[
        div(".card-body.py-2.px-3.d-flex.justify-content-between")[
            div[
                small(".text-muted.d-block")[left_label],
                span(".fw-bold", **{"x-text": left_text}),
            ],
            div(".text-end")[
                small(".text-muted.d-block")[right_label],
                span(".fw-bold", **{"x-text": right_text}),
            ],
        ]
    ]


def _sidebar_heading(text):
    """Small section heading for sidebar."""
    return small(".text-muted.d-block.mb-1.mt-2.fw-semibold")[text]


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
            season: localStorage.getItem('db_season') || '{default_season}',
            games: [],
            positions: [],
            availableLeagues: [],
            availablePositions: [],
            filterLeague: localStorage.getItem('db_filterLeague') || '',
            filterPositions: JSON.parse(localStorage.getItem('db_filterPositions') || '[]'),
            loading: true,
            view: localStorage.getItem('db_view') || 'year',
            onlyCompleted: localStorage.getItem('db_onlyCompleted') === 'true',
            showRecentGames: localStorage.getItem('db_showRecentGames') === 'true',
            recentGamesLimit: localStorage.getItem('db_recentGamesLimit') || '10',
            today: new Date().toISOString().slice(0, 10),

            togglePosition(arr, p) {{
                var i = arr.indexOf(p);
                if (i >= 0) arr.splice(i, 1); else arr.push(p);
            }},

            get filtered() {{
                return this.games.filter(g => {{
                    if (this.onlyCompleted && g.date >= this.today) return false;
                    if (this.filterLeague && g.league_id != this.filterLeague) return false;
                    if (this.filterPositions.length
                        && !this.filterPositions.includes(g.position)) return false;
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

            get upcomingGames() {{
                return this.games
                    .filter(g => g.date >= this.today)
                    .sort((a, b) => a.date.localeCompare(b.date)
                        || (a.time || '').localeCompare(b.time || ''));
            }},

            get recentGames() {{
                var all = this.games
                    .filter(g => {{
                        if (g.date >= this.today) return false;
                        if (this.filterLeague && g.league_id != this.filterLeague) return false;
                        if (this.filterPositions.length
                            && !this.filterPositions.includes(g.position)) return false;
                        return true;
                    }})
                    .sort((a, b) => b.date.localeCompare(a.date)
                        || (b.time || '').localeCompare(a.time || ''));
                var limit = parseInt(this.recentGamesLimit);
                return limit > 0 ? all.slice(0, limit) : all;
            }},

            overviewGames: [],
            overviewPositions: [],
            overviewLeagues: [],
            overviewLoaded: false,
            ovFilterLeague: '',
            ovFilterPositions: [],
            ovYearFrom: '',
            ovYearTo: '',

            get allOverviewYears() {{
                var seen = new Set();
                this.overviewGames.forEach(g => seen.add(g.year));
                return [...seen].sort().reverse();
            }},

            get overviewFiltered() {{
                return this.overviewGames.filter(g => {{
                    if (this.onlyCompleted && g.date >= this.today) return false;
                    if (this.ovFilterLeague && g.league_id != this.ovFilterLeague) return false;
                    if (this.ovFilterPositions.length
                        && !this.ovFilterPositions.includes(g.position)) return false;
                    if (this.ovYearFrom && g.year < this.ovYearFrom) return false;
                    if (this.ovYearTo && g.year > this.ovYearTo) return false;
                    return true;
                }});
            }},

            // Position charts: apply position filter only if >1 selected
            get overviewForPositions() {{
                return this.overviewGames.filter(g => {{
                    if (this.onlyCompleted && g.date >= this.today) return false;
                    if (this.ovFilterLeague && g.league_id != this.ovFilterLeague) return false;
                    if (this.ovFilterPositions.length > 1
                        && !this.ovFilterPositions.includes(g.position)) return false;
                    if (this.ovYearFrom && g.year < this.ovYearFrom) return false;
                    if (this.ovYearTo && g.year > this.ovYearTo) return false;
                    return true;
                }});
            }},

            get overviewYears() {{
                var seen = new Set();
                this.overviewFiltered.forEach(g => seen.add(g.year));
                return [...seen].sort();
            }},

            overviewAggByYear(games) {{
                var byYear = {{}};
                games.forEach(g => {{
                    if (!byYear[g.year]) byYear[g.year] = {{
                        count: 0, fee: 0, travel: 0, km: 0,
                        by_position: {{}},
                    }};
                    var y = byYear[g.year];
                    y.count++;
                    y.fee += g.fee;
                    y.travel += g.travel;
                    y.km += g.km;
                    y.by_position[g.position] =
                        (y.by_position[g.position] || 0) + 1;
                }});
                return byYear;
            }},

            get overviewByYear() {{
                return this.overviewAggByYear(this.overviewFiltered);
            }},

            get overviewByYearForPositions() {{
                return this.overviewAggByYear(this.overviewForPositions);
            }},

            get overviewStats() {{
                var f = this.overviewFiltered;
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
                if (this.view === 'overview') {{
                    this.loadOverview();
                }}
                this.$watch('season', (v) => {{
                    localStorage.setItem('db_season', v);
                    this.loadSeason();
                }});
                this.$watch('filtered', () => this.renderCharts());
                this.$watch('filterLeague', (v) => {{
                    localStorage.setItem('db_filterLeague', v);
                    this.renderPositionChart();
                }});
                this.$watch('filterPositions', (v) => {{
                    localStorage.setItem('db_filterPositions', JSON.stringify(v));
                }});
                this.$watch('onlyCompleted', (v) => {{
                    localStorage.setItem('db_onlyCompleted', v);
                    this.renderCharts();
                    if (this.view === 'overview') {{
                        this.$nextTick(() => this.renderOverviewCharts());
                    }}
                }});
                this.$watch('showRecentGames', (v) => {{
                    localStorage.setItem('db_showRecentGames', v);
                }});
                this.$watch('recentGamesLimit', (v) => {{
                    localStorage.setItem('db_recentGamesLimit', v);
                }});
                this.$watch('ovFilterLeague', (v) => {{
                    localStorage.setItem('db_ovFilterLeague', v);
                    if (this.view === 'overview') {{
                        this.$nextTick(() => this.renderOverviewCharts());
                    }}
                }});
                this.$watch('ovFilterPositions', (v) => {{
                    localStorage.setItem('db_ovFilterPositions', JSON.stringify(v));
                    if (this.view === 'overview') {{
                        this.$nextTick(() => this.renderOverviewCharts());
                    }}
                }});
                this.$watch('ovYearFrom', (v) => {{
                    localStorage.setItem('db_ovYearFrom', v);
                    if (this.view === 'overview') {{
                        this.$nextTick(() => this.renderOverviewCharts());
                    }}
                }});
                this.$watch('ovYearTo', (v) => {{
                    localStorage.setItem('db_ovYearTo', v);
                    if (this.view === 'overview') {{
                        this.$nextTick(() => this.renderOverviewCharts());
                    }}
                }});
                this.$watch('view', (v) => {{
                    localStorage.setItem('db_view', v);
                    if (v === 'overview') {{
                        this.loadOverview();
                    }} else {{
                        this.$nextTick(() => this.renderCharts());
                    }}
                }});
                window.addEventListener('theme-changed', () => {{
                    this.$nextTick(() => {{
                        this.renderCharts();
                        if (this.view === 'overview') this.renderOverviewCharts();
                    }});
                }});
            }},

            _seasonLoaded: false,
            async loadSeason() {{
                this.loading = true;
                if (this._seasonLoaded) {{
                    this.filterLeague = '';
                    this.filterPositions = [];
                }}
                this._seasonLoaded = true;
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

            {_fmt_date_js()}
            {_eur_js()}
            {_plotly_layout_js()}

            stackAnnotations(categories, totals, horizontal, fmt, angle) {{
                var fg = getComputedStyle(document.body).color;
                return categories.map((cat, i) => {{
                    var val = totals[i] || 0;
                    if (val === 0) return null;
                    var label = fmt ? fmt(val) : String(val);
                    var a = horizontal ? {{
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
                    if (angle) a.textangle = angle;
                    return a;
                }}).filter(a => a);
            }},

            renderPositionChart() {{
                var colors = {NORD_COLORS_JS};
                var games = this.games.filter(g => {{
                    if (this.onlyCompleted && g.date >= this.today) return false;
                    if (this.filterLeague && g.league_id != this.filterLeague) return false;
                    if (this.filterPositions.length > 1
                        && !this.filterPositions.includes(g.position)) return false;
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
                    legend: {{font: {{size: 10}}, traceorder: 'normal'}},
                    margin: {{t: 20, b: 30, l: 30, r: 10}},
                    annotations: this.stackAnnotations(monthLabels, totals, false),
                }}), {{responsive: true, displayModeBar: false}});
            }},

            renderLeagueChart() {{
                var colors = {NORD_COLORS_JS};
                var games = this.games.filter(g => {{
                    if (this.onlyCompleted && g.date >= this.today) return false;
                    if (this.filterPositions.length
                        && !this.filterPositions.includes(g.position)) return false;
                    return true;
                }});
                var leagueData = {{}};
                var posPresent = new Set();
                games.forEach(g => {{
                    leagueData[g.league] = leagueData[g.league] || {{}};
                    leagueData[g.league][g.position] =
                        (leagueData[g.league][g.position] || 0) + 1;
                    posPresent.add(g.position);
                }});
                var leagues = Object.entries(leagueData)
                    .map(([lg, pos]) => [lg, Object.values(pos).reduce((a, b) => a + b, 0)])
                    .sort((a, b) => a[1] - b[1])
                    .map(e => e[0]);
                var posOrder = this.positions.filter(p => posPresent.has(p));
                var traces = posOrder.map((p, i) => ({{
                    x: leagues.map(lg =>
                        (leagueData[lg] && leagueData[lg][p]) || 0
                    ),
                    y: leagues,
                    type: 'bar', orientation: 'h', name: p,
                    marker: {{color: colors[i % colors.length]}},
                }}));
                var leagueTotals = leagues.map(lg => {{
                    return Object.values(leagueData[lg])
                        .reduce((a, b) => a + b, 0);
                }});
                Plotly.newPlot('chart-leagues', traces, this.baseLayout(350, {{
                    barmode: 'stack',
                    showlegend: true,
                    legend: {{font: {{size: 10}}, traceorder: 'normal'}},
                    yaxis: {{
                        gridcolor: this.baseLayout(0).yaxis.gridcolor,
                        categoryorder: 'array', categoryarray: leagues,
                        ticksuffix: '  ',
                    }},
                    margin: {{t: 10, b: 30, l: 100, r: 30}},
                    annotations: this.stackAnnotations(leagues, leagueTotals, true),
                }}), {{responsive: true, displayModeBar: false}});
            }},

            async loadOverview() {{
                if (this.overviewLoaded) {{
                    this.$nextTick(() => this.renderOverviewCharts());
                    return;
                }}
                var res = await fetch('/dashboard/api/overview');
                var data = await res.json();
                this.overviewGames = data.games;
                this.overviewPositions = data.positions;
                this.overviewLeagues = data.available_leagues;
                this.ovFilterLeague = localStorage.getItem('db_ovFilterLeague') || '';
                this.ovFilterPositions = JSON.parse(
                    localStorage.getItem('db_ovFilterPositions') || '[]'
                );
                var allYrs = this.allOverviewYears;
                var maxY = allYrs[0] || '';
                var minDefault = maxY ? '' + (parseInt(maxY) - 9) : '';
                this.ovYearFrom = localStorage.getItem('db_ovYearFrom') || minDefault;
                this.ovYearTo = localStorage.getItem('db_ovYearTo') || maxY;
                this.overviewLoaded = true;
                this.$nextTick(() => this.renderOverviewCharts());
            }},

            // Year labels for Plotly: zero-width space forces category detection
            yearLabels(years) {{
                return years.map(y => '\\u200b' + y);
            }},

            // Tick values for overview x-axis: all if <=10, else multiples of 5
            yearTickVals(xl, years) {{
                if (years.length <= 10) return xl;
                return xl.filter((_, i) => parseInt(years[i]) % 5 === 0);
            }},

            renderOverviewCharts() {{
                if (!this.overviewLoaded) return;
                this.renderOverviewGamesPerYear();
                this.renderOverviewPositionTrend();
                this.renderOverviewPositionPie();
                this.renderOverviewFeePerYear();
                this.renderOverviewAvgPerGame();
                this.renderOverviewKmPerYear();
                this.renderOverviewSankey();
                this.renderOverviewLeagues();
            }},

            renderOverviewGamesPerYear() {{
                var colors = {NORD_COLORS_JS};
                var byYear = this.overviewByYear;
                var years = this.overviewYears;
                var xl = this.yearLabels(years);
                var traces = this.overviewPositions
                    .filter(p => years.some(y =>
                        (byYear[y].by_position[p] || 0) > 0
                    ))
                    .map((p, i) => ({{
                        x: xl,
                        y: years.map(y =>
                            byYear[y].by_position[p] || 0
                        ),
                        type: 'bar', name: p,
                        marker: {{color: colors[i % colors.length]}},
                    }}));
                var totals = years.map(y => byYear[y].count);

                Plotly.newPlot('chart-overview-games', traces,
                    this.baseLayout(350, {{
                        barmode: 'stack',
                        showlegend: true,
                        legend: {{orientation: 'h', font: {{size: 10}},
                            y: -0.15, x: 0.5, xanchor: 'center',
                            traceorder: 'normal'}},
                        margin: {{t: 20, b: 60, l: 30, r: 10}},
                        xaxis: {{tickvals: this.yearTickVals(xl, years)}},
                        annotations: this.stackAnnotations(
                            xl, totals, false
                        ),
                    }}),
                    {{responsive: true, displayModeBar: false}});
            }},

            renderOverviewPositionTrend() {{
                var colors = {NORD_COLORS_JS};
                var byYear = this.overviewByYear;
                var years = this.overviewYears;
                var xl = this.yearLabels(years);
                var traces = this.overviewPositions
                    .filter(p => years.some(y =>
                        (byYear[y].by_position[p] || 0) > 0
                    ))
                    .map((p, i) => ({{
                        x: xl,
                        y: years.map(y =>
                            byYear[y].by_position[p] || 0
                        ),
                        type: 'scatter', mode: 'lines+markers',
                        name: p,
                        line: {{
                            color: colors[i % colors.length], width: 2,
                        }},
                        marker: {{size: 5}},
                    }}));

                Plotly.newPlot('chart-overview-trend', traces,
                    this.baseLayout(350, {{
                        showlegend: true,
                        legend: {{orientation: 'h', font: {{size: 10}},
                            y: -0.15, x: 0.5, xanchor: 'center',
                            traceorder: 'normal'}},
                        margin: {{t: 20, b: 60, l: 30, r: 10}},
                        xaxis: {{tickvals: this.yearTickVals(xl, years)}},
                    }}),
                    {{responsive: true, displayModeBar: false}});
            }},

            renderOverviewPositionPie() {{
                var colors = {NORD_COLORS_JS};
                var byYear = this.overviewByYearForPositions;
                var totals = {{}};
                Object.values(byYear).forEach(y => {{
                    Object.entries(y.by_position).forEach(([p, c]) => {{
                        totals[p] = (totals[p] || 0) + c;
                    }});
                }});
                var sorted = Object.entries(totals)
                    .sort((a, b) => b[1] - a[1]);
                Plotly.newPlot('chart-overview-pie', [{{
                    labels: sorted.map(e => e[0]),
                    values: sorted.map(e => e[1]),
                    type: 'pie', hole: 0.4,
                    marker: {{colors: colors}},
                    textinfo: 'label+percent',
                    textposition: 'outside',
                    textfont: {{size: 11}},
                    domain: {{x: [0.1, 0.9], y: [0.1, 0.9]}},
                }}], this.baseLayout(350, {{
                    showlegend: false,
                    margin: {{t: 30, b: 30, l: 30, r: 30}},
                }}), {{responsive: true, displayModeBar: false}});
            }},

            renderOverviewFeePerYear() {{
                var years = this.overviewYears;
                var xl = this.yearLabels(years);
                var byYear = this.overviewByYear;
                var feeTrace = {{
                    x: xl,
                    y: years.map(y =>
                        byYear[y] ? byYear[y].fee : 0
                    ),
                    type: 'bar', name: 'Pauschale',
                    marker: {{color: '#5E81AC'}},
                }};
                var travelTrace = {{
                    x: xl,
                    y: years.map(y =>
                        byYear[y] ? byYear[y].travel : 0
                    ),
                    type: 'bar', name: 'Fahrtkosten',
                    marker: {{color: '#88C0D0'}},
                }};
                var totals = years.map(y => {{
                    var d = byYear[y];
                    return d ? d.fee + d.travel : 0;
                }});
                var fmtEur = v => Math.round(v) + ' €';
                var traces = [feeTrace, travelTrace];

                Plotly.newPlot('chart-overview-fee', traces,
                    this.baseLayout(350, {{
                        barmode: 'stack',
                        showlegend: true,
                        legend: {{orientation: 'h', font: {{size: 10}},
                            y: -0.15, x: 0.5, xanchor: 'center',
                            traceorder: 'normal'}},
                        margin: {{t: 20, b: 60, l: 50, r: 10}},
                        xaxis: {{tickvals: this.yearTickVals(xl, years)}},
                        annotations: this.stackAnnotations(
                            xl, totals, false, fmtEur, -45
                        ),
                    }}),
                    {{responsive: true, displayModeBar: false}});
            }},

            renderOverviewAvgPerGame() {{
                var years = this.overviewYears;
                var xl = this.yearLabels(years);
                var byYear = this.overviewByYear;
                var avgs = years.map(y => {{
                    var d = byYear[y];
                    if (!d || d.count === 0) return 0;
                    return (d.fee + d.travel) / d.count;
                }});
                var fmtEur = v => v.toFixed(0) + ' €';
                Plotly.newPlot('chart-overview-avg', [{{
                    x: xl, y: avgs, type: 'bar',
                    marker: {{color: '#A3BE8C'}},
                    text: avgs.map(fmtEur), textposition: 'auto',
                }}], this.baseLayout(350, {{
                    margin: {{t: 20, b: 30, l: 50, r: 10}},
                    xaxis: {{tickvals: this.yearTickVals(xl, years)}},
                }}), {{responsive: true, displayModeBar: false}});
            }},

            renderOverviewKmPerYear() {{
                var years = this.overviewYears;
                var xl = this.yearLabels(years);
                var byYear = this.overviewByYear;
                var kms = years.map(y =>
                    byYear[y] ? byYear[y].km : 0
                );
                Plotly.newPlot('chart-overview-km', [{{
                    x: xl, y: kms, type: 'bar',
                    marker: {{color: '#81A1C1'}},
                    text: kms.map(v => v.toLocaleString('de-DE')),
                    textposition: 'auto',
                }}], this.baseLayout(350, {{
                    margin: {{t: 20, b: 30, l: 50, r: 10}},
                    xaxis: {{tickvals: this.yearTickVals(xl, years)}},
                }}), {{responsive: true, displayModeBar: false}});
            }},

            renderOverviewSankey() {{
                var colors = {NORD_COLORS_JS};
                var games = this.overviewFiltered;
                if (!games.length) return;

                var years = this.overviewYears;
                var xl = this.yearLabels(years);
                var positions = this.overviewPositions.filter(
                    p => games.some(g => g.position === p)
                );

                // Count per position per year
                var counts = {{}};
                games.forEach(g => {{
                    var key = g.position + '|' + g.year;
                    counts[key] = (counts[key] || 0) + 1;
                }});

                // Heatmap: years on X, positions on Y, color = game count
                var z = positions.map(p =>
                    years.map(y => counts[p + '|' + y] || 0)
                );
                var annotations = [];
                positions.forEach((p, pi) => {{
                    years.forEach((y, yi) => {{
                        var val = counts[p + '|' + y] || 0;
                        if (val > 0) {{
                            annotations.push({{
                                x: xl[yi], y: p,
                                text: '' + val,
                                showarrow: false,
                                font: {{color: val > 8 ? '#2E3440' : '#ECEFF4', size: 11}},
                            }});
                        }}
                    }});
                }});

                Plotly.newPlot('chart-overview-sankey', [{{
                    x: xl, y: positions, z: z,
                    type: 'heatmap',
                    colorscale: [
                        [0, '#3B4252'],
                        [0.3, '#5E81AC'],
                        [0.6, '#88C0D0'],
                        [0.8, '#D08770'],
                        [1, '#BF616A'],
                    ],
                    showscale: false,
                    hoverongaps: false,
                    xgap: 2,
                    ygap: 2,
                }}], this.baseLayout(Math.max(300, positions.length * 45), {{
                    margin: {{t: 10, b: 30, l: 40, r: 10}},
                    xaxis: {{tickvals: xl, side: 'bottom'}},
                    yaxis: {{autorange: 'reversed'}},
                    annotations: annotations,
                }}), {{responsive: true, displayModeBar: false}});
            }},

            renderOverviewLeagues() {{
                var colors = {NORD_COLORS_JS};
                // Ignore league filter for this chart
                var games = this.overviewGames.filter(g => {{
                    if (this.onlyCompleted && g.date >= this.today) return false;
                    if (this.ovFilterPositions.length
                        && !this.ovFilterPositions.includes(g.position)) return false;
                    if (this.ovYearFrom && g.year < this.ovYearFrom) return false;
                    if (this.ovYearTo && g.year > this.ovYearTo) return false;
                    return true;
                }});
                if (!games.length) return;

                var seenYears = new Set();
                games.forEach(g => seenYears.add(g.year));
                var years = [...seenYears].sort();
                var xl = this.yearLabels(years);

                // Get unique leagues, sorted by total count descending
                var leagueTotals = {{}};
                games.forEach(g => {{
                    leagueTotals[g.league] = (leagueTotals[g.league] || 0) + 1;
                }});
                var leagues = Object.keys(leagueTotals)
                    .sort((a, b) => leagueTotals[b] - leagueTotals[a]);

                // Count per league per year
                var counts = {{}};
                games.forEach(g => {{
                    var key = g.league + '|' + g.year;
                    counts[key] = (counts[key] || 0) + 1;
                }});

                var traces = years.map((y, i) => ({{
                    x: leagues,
                    y: leagues.map(lg => counts[lg + '|' + y] || 0),
                    type: 'bar',
                    name: y,
                    marker: {{color: colors[i % colors.length]}},
                }}));

                Plotly.newPlot('chart-overview-leagues', traces,
                    this.baseLayout(350, {{
                    barmode: 'stack',
                    showlegend: true,
                    legend: {{font: {{size: 10}}, traceorder: 'normal'}},
                    margin: {{t: 10, b: 80, l: 40, r: 10}},
                    xaxis: {{tickangle: -45}},
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
                    legend: {{font: {{size: 10}}, traceorder: 'normal'}},
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
                div(".mb-3")[
                    small(".text-muted.d-block.mb-1")["Position"],
                    div(
                        ".d-flex.flex-wrap.gap-1",
                    )[
                        template({"x-for": "p in availablePositions", ":key": "p"})[
                            button(
                                ".btn.btn-sm",
                                type="button",
                                **{
                                    ":class": "filterPositions.includes(p)"
                                    " ? 'btn-primary' : 'btn-outline-secondary'",
                                    "@click": "togglePosition(filterPositions, p)",
                                    "x-text": "p",
                                },
                            ),
                        ],
                    ],
                ],
                _alpine_select(
                    "Liga",
                    "filterLeague",
                    template({"x-for": "lg in availableLeagues", ":key": "lg.id"})[
                        option({":value": "'' + lg.id", "x-text": "lg.name"}),
                    ],
                ),
                _sidebar_heading("Spiele"),
                div(".d-flex.align-items-center.flex-wrap.gap-2.mb-3")[
                    div(".form-check.mb-0")[
                        input(
                            "#only-completed.form-check-input",
                            type="checkbox",
                            **{"x-model": "onlyCompleted"},
                        ),
                        label(
                            ".form-check-label.small",
                            for_="only-completed",
                        )["Ohne offene"],
                    ],
                    div(
                        ".form-check.mb-0",
                        {"x-show": "view === 'year'"},
                    )[
                        input(
                            "#show-recent.form-check-input",
                            type="checkbox",
                            **{"x-model": "showRecentGames"},
                        ),
                        label(
                            ".form-check-label.small",
                            for_="show-recent",
                        )["Absolviert"],
                    ],
                    select(
                        ".form-select.form-select-sm",
                        style="width:auto",
                        **{
                            "x-model": "recentGamesLimit",
                            "x-show": "view === 'year' && showRecentGames",
                        },
                    )[
                        option(value="0")["Alle"],
                        option(value="5")["5"],
                        option(value="10")["10"],
                        option(value="15")["15"],
                        option(value="20")["20"],
                    ],
                ],
                button(
                    ".btn.btn-outline-secondary.btn-sm.w-100.mb-3",
                    type="button",
                    **{
                        "@click": "filterLeague = ''; filterPositions = [];"
                        " onlyCompleted = true;"
                        " showRecentGames = false; recentGamesLimit = '10'",
                        "x-show": "filterLeague || filterPositions.length"
                        " || !onlyCompleted || showRecentGames",
                    },
                )[i(".bi.bi-x-circle.me-1"), "Filter zurücksetzen"],
                div(".d-flex.flex-column.gap-2")[
                    _stat_row("Spiele", "stats.count", "Gesamt", "eur(stats.total)"),
                    _stat_row("Vergütung", "eur(stats.fee)", "Fahrtkosten", "eur(stats.travel)"),
                    _stat_row(
                        "Kilometer",
                        "stats.km.toLocaleString('de-DE')",
                        "ct/km",
                        "stats.km > 0"
                        " ? (stats.travel / stats.km * 100)"
                        ".toFixed(1).replace('.', ',') + ' ct'"
                        " : '–'",
                    ),
                ],
            ],
            # Overview sidebar
            div({"x-show": "view === 'overview'"})[
                div(".mb-3")[
                    small(".text-muted.d-block.mb-1")["Position"],
                    div(
                        ".d-flex.flex-wrap.gap-1",
                    )[
                        template({"x-for": "p in overviewPositions", ":key": "p"})[
                            button(
                                ".btn.btn-sm",
                                type="button",
                                **{
                                    ":class": "ovFilterPositions.includes(p)"
                                    " ? 'btn-primary' : 'btn-outline-secondary'",
                                    "@click": "togglePosition(ovFilterPositions, p)",
                                    "x-text": "p",
                                },
                            ),
                        ],
                    ],
                ],
                _alpine_select(
                    "Liga",
                    "ovFilterLeague",
                    template({"x-for": "lg in overviewLeagues", ":key": "lg.id"})[
                        option({":value": "'' + lg.id", "x-text": "lg.name"})
                    ],
                ),
                div(".mb-3")[
                    small(".text-muted.d-block.mb-1")["Zeitraum"],
                    div(".d-flex.gap-1.align-items-center")[
                        select(
                            ".form-select.form-select-sm",
                            **{"x-model": "ovYearFrom"},
                        )[
                            template({"x-for": "y in allOverviewYears", ":key": "'from'+y"})[
                                option({":value": "y", "x-text": "y"}),
                            ],
                        ],
                        small(".text-muted")["–"],
                        select(
                            ".form-select.form-select-sm",
                            **{"x-model": "ovYearTo"},
                        )[
                            template({"x-for": "y in allOverviewYears", ":key": "'to'+y"})[
                                option({":value": "y", "x-text": "y"}),
                            ],
                        ],
                    ],
                ],
                _sidebar_heading("Spiele"),
                div(".form-check.mb-3")[
                    input(
                        "#only-completed-overview.form-check-input",
                        type="checkbox",
                        **{"x-model": "onlyCompleted"},
                    ),
                    label(
                        ".form-check-label.small",
                        for_="only-completed-overview",
                    )["Ohne offene"],
                ],
                button(
                    ".btn.btn-outline-secondary.btn-sm.w-100.mb-3",
                    type="button",
                    **{
                        "@click": "ovFilterLeague = ''; ovFilterPositions = [];"
                        " ovYearTo = allOverviewYears[0] || '';"
                        " ovYearFrom = ovYearTo ? '' + (parseInt(ovYearTo) - 9) : '';"
                        " onlyCompleted = true",
                        "x-show": "ovFilterLeague || ovFilterPositions.length"
                        " || ovYearFrom || ovYearTo || !onlyCompleted",
                    },
                )[i(".bi.bi-x-circle.me-1"), "Filter zurücksetzen"],
                div(".d-flex.flex-column.gap-2")[
                    _stat_row(
                        "Spiele",
                        "overviewStats.count",
                        "Gesamt",
                        "eur(overviewStats.total)",
                    ),
                    _stat_row(
                        "Vergütung",
                        "eur(overviewStats.fee)",
                        "Fahrtkosten",
                        "eur(overviewStats.travel)",
                    ),
                    _stat_row(
                        "Kilometer",
                        "overviewStats.km.toLocaleString('de-DE')",
                        "ct/km",
                        "overviewStats.km > 0"
                        " ? (overviewStats.travel / overviewStats.km * 100)"
                        ".toFixed(1).replace('.', ',') + ' ct'"
                        " : '–'",
                    ),
                ],
            ],
        ],
    ]

    def _game_table_card(title, icon, x_show, x_for, count_expr=None):
        """Reusable game table card with Alpine.js bindings."""
        header_content = [i(f".bi.{icon}.me-1"), title]
        if count_expr:
            header_content.append(
                small(".ms-2.text-muted", {"x-text": f"'(' + {count_expr} + ')'"})
            )
        return div(".card.mt-3", {"x-show": x_show})[
            div(".card-header.py-2")[h6(".mb-0.text-muted")[header_content]],
            div(".card-body.p-0")[
                div(".table-responsive")[
                    table(".table.table-sm.table-striped.table-hover.mb-0")[
                        thead[
                            tr[
                                th(".text-nowrap.ps-3")["Datum"],
                                th(".text-nowrap")["Zeit"],
                                th(".text-nowrap")["Pos"],
                                th(".text-nowrap")["Liga"],
                                th(".text-nowrap")["Heim"],
                                th(".text-nowrap")["Gast"],
                                th(".text-nowrap.pe-3")["Spielort"],
                            ],
                        ],
                        tbody[
                            template({"x-for": x_for, ":key": "g.date+g.home+g.away"})[
                                tr[
                                    td(".ps-3", {"x-text": "fmtDate(g.date)"}),
                                    td(".text-muted", {"x-text": "g.time"}),
                                    td[
                                        span(
                                            ".badge.bg-secondary",
                                            {"x-text": "g.position"},
                                        )
                                    ],
                                    td({"x-text": "g.league_long || g.league"}),
                                    td(".fw-semibold", {"x-text": "g.home"}),
                                    td(".fw-semibold", {"x-text": "g.away"}),
                                    td(".text-muted.pe-3", {"x-text": "g.venue"}),
                                ],
                            ],
                        ],
                    ],
                ],
            ],
        ]

    upcoming_section = _game_table_card(
        "Anstehende Spiele",
        "bi-calendar-event",
        "view === 'year' && upcomingGames.length > 0",
        "g in upcomingGames",
    )

    recent_section = _game_table_card(
        "Absolvierte Spiele",
        "bi-calendar-check",
        "view === 'year' && showRecentGames && recentGames.length > 0",
        "g in recentGames",
        count_expr="recentGames.length",
    )

    # Charts area (year view only)
    charts = div(".col-md-10", {"x-show": "view === 'year'"})[
        upcoming_section,
        recent_section,
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

    # Charts area (overview)
    overview_charts = div(".col-md-10", {"x-show": "view === 'overview'"})[
        _collapsible_section(
            "overview-games-body",
            "bi.bi-bar-chart-fill",
            "Einsätze",
            div(".row.g-3.mb-3")[
                div(".col-md-6")[_widget_card("Spiele pro Jahr", "chart-overview-games")],
                div(".col-md-6")[_widget_card("Positionstrend", "chart-overview-trend")],
            ],
            div(".row.g-3")[
                div(".col-md-4")[_widget_card("Positionsverteilung", "chart-overview-pie")],
                div(".col-md-8")[_widget_card("Spiele pro Liga", "chart-overview-leagues")],
            ],
        ),
        _collapsible_section(
            "overview-fees-body",
            "bi.bi-currency-euro",
            "Vergütung",
            div(".row.g-3")[
                div(".col-md-4")[_widget_card("Vergütung pro Jahr", "chart-overview-fee")],
                div(".col-md-4")[_widget_card("Durchschnitt pro Spiel", "chart-overview-avg")],
                div(".col-md-4")[_widget_card("Kilometer pro Jahr", "chart-overview-km")],
            ],
        ),
        _collapsible_section(
            "overview-flow-body",
            "bi.bi-diagram-3",
            "Verteilung",
            div(".row.g-3")[
                div(".col-12")[_widget_card("Positionen pro Jahr", "chart-overview-sankey")],
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
            div({"x-show": "!loading", "x-cloak": ""})[
                div(".row.g-4")[sidebar, charts, overview_charts],
            ],
        ],
        alpine_script,
    ]

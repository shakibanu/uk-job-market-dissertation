"""
tabs.py

This file creates the layout for each dashboard tab.

The charts and tables are updated later by the callbacks, while this
file is only responsible for organising the page structure.
"""

from dash import dcc, html
from data_loader import (
    SECTORS, COUNTRIES, TEXT, TEXT_SECONDARY, BLUE, TEAL, AMBER, DANGER,
    latest_year, total_sponsors, total_vacancies_latest, n_sectors,
    national_trend, master_df,
)
from dashboard_components import stat_card, pct_change

# Create the layout for the Overview tab
overview_tab = html.Div(
    [   # Display the main dashboard summary cards
        html.Div(
            [
                stat_card("Sectors covered", str(n_sectors), BLUE, icon="layout"),
                stat_card("Licensed sponsors", f"{total_sponsors:,}", TEAL, icon="briefcase"),
                stat_card("2025 salary threshold", "£41,700", AMBER, icon="trending-up"),
                stat_card(
                    f"Vacancies ({latest_year})", f"{total_vacancies_latest:,}", BLUE, national_trend,
                    trend_pct=pct_change(national_trend), trend_caption="vs Q1 2021", icon="bar-chart-2",
                ),
            ],
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fit, minmax(200px, 1fr))",
                "gap": "14px",
                "marginBottom": "14px",
            },
        ),
        html.Div(
            [
                html.Div(
                    "Full sector, company and salary views load on the tabs above. "
                    "SARIMA forecasts and the regional heatmap are being built next.",
                    style={"fontSize": "13px", "color": TEXT_SECONDARY},
                ),
                html.Div(
                    [html.Span(className="status-dot"), "Data current to 2026"],
                    className="status-pill",
                ),
            ],
            className="panel",
            style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"},
        ),
    ],
    className="tab-body",
)

sectors_tab = html.Div(
    [
        html.Label("Sector"),
        dcc.Dropdown(
            id="sector-dropdown",
            options=[{"label": s, "value": s} for s in SECTORS],
            value=SECTORS[0],
            clearable=False,
            style={"maxWidth": "280px", "marginBottom": "20px"},
        ),
        html.Div(dcc.Graph(id="sector-vacancy-chart", config={"displayModeBar": False}), className="panel", style={"marginBottom": "20px"}),
        html.Div(id="sarima-diagnostics", className="panel", style={"marginBottom": "20px"}),
        html.Div(
            [
                html.Div("Sector sponsorship comparison", style={
                    "fontFamily": "Inter, sans-serif", "fontSize": "14px",
                    "fontWeight": "700", "color": TEXT, "marginBottom": "4px",
                }),
                html.Div(
                    "Skilled Worker visa grants by sector, 2021-2025. Drag the slider or press play.",
                    style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginBottom": "10px"},
                ),
                dcc.Graph(id="sponsorship-comparison-chart", config={"displayModeBar": False}),
            ],
            className="panel",
            style={"marginBottom": "20px"},
        ),
        html.Div(
            [
                html.Div("Top skills mentioned in job postings", style={
                    "fontFamily": "Inter, sans-serif", "fontSize": "14px",
                    "fontWeight": "700", "color": TEXT, "marginBottom": "4px",
                }),
                html.Div(
                    "Indicative only - based on a snapshot of Adzuna job postings collected in June "
                    "2026 (around 250 postings per sector), matched against a curated list of common "
                    "skills, not a live or exhaustive analysis.",
                    style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginBottom": "10px"},
                ),
                dcc.Graph(id="skills-chart", config={"displayModeBar": False}),
            ],
            className="panel",
        ),
    ],
    className="tab-body",
)

companies_tab = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        html.Label("Search by city"),
                        dcc.Input(
                            id="city-search",
                            type="text",
                            placeholder="e.g. London",
                            debounce=True,
                            style={"maxWidth": "280px", "display": "block"},
                        ),
                    ],
                    style={"marginRight": "24px"},
                ),
                html.Div(
                    [
                        html.Label("Filter by sector"),
                        dcc.Dropdown(
                            id="company-sector-filter",
                            options=[{"label": s, "value": s} for s in SECTORS],
                            placeholder="All sectors",
                            clearable=True,
                            style={"minWidth": "220px"},
                        ),
                    ]
                ),
            ],
            style={"display": "flex", "marginBottom": "20px"},
        ),
        html.Div(id="company-table-container", className="panel"),
        html.Div(
            "Active job count is matched by company name against Adzuna postings, "
            "so it's only available for a small number of companies. Sector is "
            "matched against Companies House data - about 25% of sponsors have a "
            "sector, since most licensed sponsors aren't in these 5 sectors at "
            "all. Region filter is still coming, once regional data is sourced.",
            style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginTop": "10px"},
        ),
    ],
    className="tab-body",
)

salary_tab = html.Div(
    [
        html.Label("Year"),
        dcc.Dropdown(
            id="salary-year-dropdown",
            options=[{"label": str(y), "value": y} for y in sorted(master_df["Year"].unique())],
            value=int(master_df["Year"].max()),
            clearable=False,
            style={"maxWidth": "200px", "marginBottom": "20px"},
        ),
        html.Div(dcc.Graph(id="salary-chart", config={"displayModeBar": False}), className="panel"),
        html.Div(
            [
                html.Span("● ", style={"color": DANGER}),
                "Below visa salary threshold for the selected year — role would not qualify for Skilled Worker sponsorship at that salary.",
            ],
            style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginTop": "10px"},
        ),
    ],
    className="tab-body",
)

roi_tab = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        html.Label("Home country"),
                        dcc.Dropdown(
                            id="roi-country-dropdown",
                            options=[{"label": c, "value": c} for c in COUNTRIES],
                            value="India",
                            clearable=False,
                            style={"minWidth": "220px"},
                        ),
                    ],
                    style={"marginRight": "24px"},
                ),
                html.Div(
                    [
                        html.Label("Target sector"),
                        dcc.Dropdown(
                            id="roi-sector-dropdown",
                            options=[{"label": s, "value": s} for s in SECTORS],
                            value=SECTORS[0],
                            clearable=False,
                            style={"minWidth": "200px"},
                        ),
                    ],
                    style={"marginRight": "24px"},
                ),
                html.Div(
                    [
                        html.Label("Study location"),
                        dcc.Dropdown(
                            id="roi-region-dropdown",
                            options=[{"label": "Outside London", "value": "Outside London"}, {"label": "London", "value": "London"}],
                            value="Outside London",
                            clearable=False,
                            style={"minWidth": "180px"},
                        ),
                    ]
                ),
            ],
            style={"display": "flex", "marginBottom": "20px", "flexWrap": "wrap", "gap": "10px"},
        ),
        html.Div(id="roi-results-container", className="panel", style={"marginBottom": "20px"}),
        html.Div(dcc.Graph(id="roi-chart", config={"displayModeBar": False}), className="panel", style={"marginBottom": "20px"}),
        html.Div(
            "This compares the total cost of studying and living in the UK against the salary "
            "advantage of a UK sector salary over your home country's average income (GDP per "
            "capita), to estimate a break-even point. GDP per capita is a national average, not "
            "specific to your profession, so this is a rough guide, not a financial prediction. "
            "Sponsorship activity is a sector-level relative ranking based on visa grants versus "
            "vacancies - a more precise, company-level prediction is planned once the Sponsorship "
            "Fit Calculator is built.",
            style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginTop": "10px"},
        ),
    ],
    className="tab-body",
)

fit_calculator_tab = html.Div(
    [
        html.Label("Target sector"),
        dcc.Dropdown(
            id="fit-sector-dropdown",
            options=[{"label": s, "value": s} for s in SECTORS],
            value=SECTORS[0],
            clearable=False,
            style={"maxWidth": "280px", "marginBottom": "20px"},
        ),
        html.Div(id="fit-results-container", className="panel", style={"marginBottom": "20px"}),
        html.Div(
            [
                html.Div("Model card", style={"fontWeight": "700", "marginBottom": "8px"}),
                html.Div(id="fit-model-card"),
            ],
            className="panel",
        ),
    ],
    className="tab-body",
)

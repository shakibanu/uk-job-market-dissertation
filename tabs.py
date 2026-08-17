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
    national_trend, national_trend_annual, master_df, LAST_REFRESHED, get_last_refreshed_display,
    sponsors_df, mac_stay_rate_df, REGION_MAPPED_COUNT, REGION_TOTAL_COUNT,
    nationality_df,
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
                    # comparing annual total to annual total here, matching
                    # the annual figure shown above - a quarter-to-quarter
                    # comparison was being shown next to an annual number,
                    # which gave a misleading +4.5% when the real year-on-
                    # year change is a decline
                    trend_pct=pct_change(national_trend_annual), trend_caption="vs 2021 (annual total)", icon="bar-chart-2",
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
                    "Explore forecasts on the Sectors tab, regional sponsor data and "
                    "MAC stay rates on the Regional tab, and the full story behind "
                    "these numbers under \"The Story\" above.",
                    style={"fontSize": "13px", "color": TEXT_SECONDARY},
                ),
                html.Div(
                    [html.Span(className="status-dot"), get_last_refreshed_display()],
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
        dcc.Loading(
            html.Div(id="roi-results-container", className="panel", style={"marginBottom": "20px"}),
            type="circle", color=BLUE,
        ),
        dcc.Loading(
            html.Div(dcc.Graph(id="roi-chart", config={"displayModeBar": False}), className="panel", style={"marginBottom": "20px"}),
            type="circle", color=BLUE,
        ),
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

regional_tab = html.Div(
    [
        html.Div(
            [
                html.Div("Licensed sponsors by region", style={
                    "fontFamily": "Inter, sans-serif", "fontSize": "14px",
                    "fontWeight": "700", "color": TEXT, "marginBottom": "4px",
                }),
                html.Div(
                    "This shows where licensed sponsor organisations are registered, "
                    "not how many Skilled Worker visas were granted in each region - "
                    "the Home Office does not publish visa grants by region, so this "
                    "is the closest genuine regional measure available.",
                    style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginBottom": "10px"},
                ),
                html.Label("Filter by sector"),
                dcc.Dropdown(
                    id="regional-sector-filter",
                    options=[{"label": s, "value": s} for s in SECTORS],
                    placeholder="All sectors",
                    clearable=True,
                    style={"maxWidth": "280px", "marginBottom": "16px"},
                ),
                dcc.Graph(id="regional-heatmap-chart", config={"displayModeBar": False}),
                html.Div(
                    id="regional-coverage-note",
                    style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginTop": "10px"},
                ),
            ],
            className="panel",
            style={"marginBottom": "20px"},
        ),
        html.Div(
            [
                html.Div("Skilled Worker 5-year stay rate by region", style={
                    "fontFamily": "Inter, sans-serif", "fontSize": "14px",
                    "fontWeight": "700", "color": TEXT, "marginBottom": "4px",
                }),
                html.Div(
                    "This is a completely different measure from the chart above - it "
                    "shows what percentage of people first sponsored on a Skilled Worker "
                    "visa in that region still held valid UK immigration status 5 years "
                    "later. It is a retention rate, not a count of sponsors and not a "
                    "count of visas granted. Source: Migration Advisory Committee, "
                    "\"Who Stays, Who Leaves?\" (2026).",
                    style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginBottom": "10px"},
                ),
                dcc.Graph(id="mac-stay-rate-chart", config={"displayModeBar": False}),
            ],
            className="panel",
        ),
    ],
    className="tab-body",
)

sources_tab = html.Div(
    [
        html.Div("Data sources", style={
            "fontFamily": "Inter, sans-serif", "fontSize": "18px",
            "fontWeight": "700", "color": TEXT, "marginBottom": "16px",
        }),
        html.Div(
            [
                html.Div([html.B("ONS VACS02 (Vacancy Survey) "), "- vacancy counts by industry, seasonally adjusted"], style={"marginBottom": "8px"}),
                html.Div([html.B("Home Office Sponsors Register "), "- licensed sponsor companies, city, route"], style={"marginBottom": "8px"}),
                html.Div([html.B("Companies House "), "- bulk company data used to match sponsors to a sector"], style={"marginBottom": "8px"}),
                html.Div([html.B("Home Office Immigration System Statistics "), "- Skilled Worker visa grants by sector and year"], style={"marginBottom": "8px"}),
                html.Div([html.B("ONS ASHE "), "- median salary by sector and year"], style={"marginBottom": "8px"}),
                html.Div([html.B("Adzuna API "), "- job postings, used for active job counts and classifier training"], style={"marginBottom": "8px"}),
                html.Div([html.B("Migration Advisory Committee "), "- \"Who Stays, Who Leaves?\" (2026), Skilled Worker 5-year stay rate by region"], style={"marginBottom": "8px"}),
                html.Div([html.B("World Bank "), "- GDP per capita by country, used in the ROI calculator"], style={"marginBottom": "8px"}),
                html.Div([html.B("UKCISA / gov.uk "), "- living cost estimates, used in the ROI calculator"], style={"marginBottom": "8px"}),
            ],
            className="panel",
        ),
    ],
    className="tab-body",
)

nationality_tab = html.Div(
    [
        html.Div(
            [
                html.Div("Sponsored work visa grants by nationality", style={
                    "fontFamily": "Inter, sans-serif", "fontSize": "14px",
                    "fontWeight": "700", "color": TEXT, "marginBottom": "4px",
                }),
                html.Div(
                    "Source: Home Office, Immigration System Statistics - Sponsored work "
                    "entry clearance visas by occupation and industry. Two official "
                    "datasets are combined here: the SOC 2010 edition (2021 Q1-2024 Q1) "
                    "and the SOC 2020 edition (2024 Q4-2026 Q1). 2024 Q2 and 2024 Q3 are "
                    "not published with nationality data in either official dataset, so "
                    "they are genuinely missing here too - not shown as zero, not "
                    "estimated. The gap in the chart below is real, not a rendering error.",
                    style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginBottom": "10px"},
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label("Sector"),
                                dcc.Dropdown(
                                    id="nationality-sector-dropdown",
                                    options=[{"label": s, "value": s} for s in SECTORS],
                                    value=SECTORS[0],
                                    clearable=False,
                                    style={"minWidth": "220px"},
                                ),
                            ],
                            style={"marginRight": "24px"},
                        ),
                        html.Div(
                            [
                                html.Label("Highlight one nationality (optional)"),
                                dcc.Dropdown(
                                    id="nationality-filter-dropdown",
                                    options=[],  # populated by callback based on sector
                                    placeholder="All nationalities combined",
                                    clearable=True,
                                    style={"minWidth": "220px"},
                                ),
                            ],
                        ),
                    ],
                    style={"display": "flex", "marginBottom": "16px"},
                ),
                dcc.Graph(id="nationality-ranking-chart", config={"displayModeBar": False}),
            ],
            className="panel",
            style={"marginBottom": "20px"},
        ),
        html.Div(
            [
                html.Div("Grants over time, by quarter", style={
                    "fontFamily": "Inter, sans-serif", "fontSize": "14px",
                    "fontWeight": "700", "color": TEXT, "marginBottom": "4px",
                }),
                html.Div(
                    "The dashed vertical line marks where the underlying Home Office "
                    "dataset changes from the SOC 2010 to the SOC 2020 occupation "
                    "classification. The Industry field used for sector mapping is the "
                    "same in both, but the two are still separate published datasets, "
                    "extracted at different times - so the change from Q1 2024 to Q4 "
                    "2024 should be read as a comparison between two data sources, not "
                    "as a smooth trend through the missing quarters.",
                    style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginBottom": "10px"},
                ),
                dcc.Graph(id="nationality-trend-chart", config={"displayModeBar": False}),
                # this doesn't show anything on screen - it exists to stop a
                # slow, older server response from overwriting a newer one
                # when the nationality dropdown is changed rapidly (confirmed
                # this was happening: the server can take slightly different
                # amounts of time to respond to each request, and without
                # this, whichever response happens to arrive last wins, even
                # if it's not the most recent selection)
                dcc.Store(id="nationality-trend-raw", data=None),
            ],
            className="panel",
        ),
    ],
    className="tab-body",
)

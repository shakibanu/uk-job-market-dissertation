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
                    "The story above covered the national picture. The tabs below break "
                    "that same picture down by sector, salary, employer, and region.",
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
        html.Div(
            [
                html.Div("How does every sector compare at once?", style={
                    "fontFamily": "Inter, sans-serif", "fontSize": "14px",
                    "fontWeight": "700", "color": TEXT, "marginBottom": "4px",
                }),
                dcc.Loading(dcc.Graph(id="small-multiples-chart", config={"displayModeBar": False}), type="circle", color=BLUE),
            ],
            className="panel",
            style={"marginTop": "14px"},
        ),
    ],
    className="tab-body",
)

sectors_tab = html.Div(
    [
        html.Div(
            "This tab shows how each sector's vacancies and visa sponsorship actually "
            "changed between 2021 and 2025. The national trend in the story above did "
            "not happen the same way in every sector.",
            style={"fontSize": "13px", "color": TEXT_SECONDARY, "marginBottom": "14px"},
        ),
        html.Label("Sector"),
        dcc.Dropdown(
            id="sector-dropdown",
            options=[{"label": s, "value": s} for s in SECTORS],
            value=SECTORS[0],
            clearable=False,
            style={"maxWidth": "280px", "marginBottom": "20px"},
        ),
        dcc.Loading(html.Div(dcc.Graph(id="sector-vacancy-chart", config={"displayModeBar": False}), className="panel", style={"marginBottom": "20px"}), type="circle", color=BLUE),
        html.Div(
            [
                html.Button("Export this chart as PNG", id="sector-chart-export-button", className="export-button"),
                dcc.Download(id="sector-chart-export-download"),
            ],
            style={"marginBottom": "20px", "marginTop": "-10px"},
        ),
        html.Div(id="sarima-diagnostics", className="panel", style={"marginBottom": "20px"}),
        html.Div(
            [
                html.Div("Sector sponsorship comparison", style={
                    "fontFamily": "Inter, sans-serif", "fontSize": "14px",
                    "fontWeight": "700", "color": TEXT, "marginBottom": "4px",
                }),
                html.Div(
                    "Skilled Worker visa grants by sector, 2021 to 2025. Use the slider "
                    "or play control to see the change year by year.",
                    style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginBottom": "10px"},
                ),
                dcc.Loading(dcc.Graph(id="sponsorship-comparison-chart", config={"displayModeBar": False}), type="circle", color=BLUE),
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
                    "Skills most frequently mentioned in job postings for this sector. "
                    "Based on a snapshot of around 250 Adzuna job postings per sector, "
                    "collected in June 2026, matched against a curated list of common "
                    "skills. This is indicative, not a live or exhaustive analysis.",
                    style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginBottom": "10px"},
                ),
                dcc.Loading(dcc.Graph(id="skills-chart", config={"displayModeBar": False}), type="circle", color=BLUE),
            ],
            className="panel",
        ),
    ],
    className="tab-body",
)

companies_tab = html.Div(
    [
        dcc.Store(id="bookmarked-companies", storage_type="session"),
        html.Div(
            "These are real, currently licensed UK sponsor companies from the "
            "Home Office register. Search by city or filter by sector.",
            style={"fontSize": "13px", "color": TEXT_SECONDARY, "marginBottom": "14px"},
        ),
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
                html.Div(
                    [
                        html.Label(" "),
                        dcc.Checklist(
                            id="favourites-only-toggle",
                            options=[{"label": " Show bookmarked only", "value": "favourites"}],
                            value=[],
                            style={"marginTop": "8px"},
                        ),
                    ],
                    style={"marginLeft": "24px"},
                ),
            ],
            style={"display": "flex", "marginBottom": "20px"},
        ),
        html.Div(id="company-table-container", className="panel"),
        html.Div(
            [
                html.Button("Export current results as CSV", id="company-export-button", className="export-button"),
                dcc.Download(id="company-export-download"),
            ],
            style={"marginTop": "10px"},
        ),
        html.Div(
            "Not every company shown here has a listed sector or job count. This "
            "reflects genuine limits in how sponsor companies could be matched to "
            "outside data, not missing entries.",
            style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginTop": "10px"},
        ),
        html.Div(
            "Active job count is matched by company name against Adzuna postings, "
            "so it's only available for a small number of companies. Sector is "
            "matched against Companies House data - about 25% of sponsors have a "
            "sector, since most licensed sponsors aren't in these 5 sectors at all.",
            style={"fontSize": "11px", "color": TEXT_SECONDARY, "marginTop": "4px"},
        ),
    ],
    className="tab-body",
)

salary_tab = html.Div(
    [
        html.Div(
            "A job offer is only part of the picture. The salary also has to meet "
            "the government's minimum threshold for sponsorship.",
            style={"fontSize": "13px", "color": TEXT_SECONDARY, "marginBottom": "14px"},
        ),
        html.Label("Year"),
        dcc.Dropdown(
            id="salary-year-dropdown",
            options=[{"label": str(y), "value": y} for y in sorted(master_df["Year"].unique())],
            value=int(master_df["Year"].max()),
            clearable=False,
            style={"maxWidth": "200px", "marginBottom": "20px"},
        ),
        dcc.Loading(html.Div(dcc.Graph(id="salary-chart", config={"displayModeBar": False}), className="panel"), type="circle", color=BLUE),
        html.Div(
            [
                html.Span("● ", style={"color": DANGER}),
                "Red bars show a sector's median salary falling below that year's visa threshold. A role at this level would not qualify for Skilled Worker sponsorship, regardless of employer interest.",
            ],
            style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginTop": "10px"},
        ),
        html.Div(
            [
                html.Div("Which sector's salary grew fastest? 2021 vs 2025", style={
                    "fontFamily": "Inter, sans-serif", "fontSize": "14px",
                    "fontWeight": "700", "color": TEXT, "marginBottom": "4px",
                }),
                html.Div(
                    "Technology's median salary grew faster than any other tracked sector "
                    "between 2021 and 2025.",
                    style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginBottom": "10px"},
                ),
                dcc.Loading(dcc.Graph(id="salary-slope-chart", config={"displayModeBar": False}), type="circle", color=BLUE),
            ],
            className="panel",
            style={"marginTop": "20px"},
        ),
        html.Div(
            [
                html.Div("Salary across sector and year, all at once", style={
                    "fontFamily": "Inter, sans-serif", "fontSize": "14px",
                    "fontWeight": "700", "color": TEXT, "marginBottom": "4px",
                }),
                html.Div(
                    "Drag to rotate. Height and colour both show median salary, so "
                    "the shape of the surface itself shows which sectors and years "
                    "paid more, on top of the exact figures on hover.",
                    style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginBottom": "10px"},
                ),
                dcc.Loading(dcc.Graph(id="salary-surface-chart", config={"displayModeBar": False}), type="circle", color=BLUE),
            ],
            className="panel",
            style={"marginTop": "20px"},
        ),
    ],
    className="tab-body",
)

roi_tab = html.Div(
    [
        html.Div(
            "This section estimates whether studying and working in the UK is "
            "likely to be worth the cost, based on your home country and target "
            "sector.",
            style={"fontSize": "13px", "color": TEXT_SECONDARY, "marginBottom": "14px"},
        ),
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
            "This compares the total cost of studying and living in the UK "
            "against the salary difference between a UK sector salary and your "
            "home country's average income, to estimate a break-even point.",
            style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginTop": "10px"},
        ),
        html.Div(
            "Home country income is based on GDP per capita, since profession-"
            "specific income data is not available for every country. This is a "
            "general estimate, not a personal financial forecast. Sponsorship "
            "activity is a sector-level relative ranking based on visa grants "
            "versus vacancies - for a company-level estimate, see the "
            "Sponsorship Fit tab.",
            style={"fontSize": "11px", "color": TEXT_SECONDARY, "marginTop": "4px"},
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
            "This tab shows two separate things: where licensed sponsor companies "
            "are based, and how many people who are sponsored in each region are "
            "still in the UK five years later.",
            style={"fontSize": "13px", "color": TEXT_SECONDARY, "marginBottom": "14px"},
        ),
        html.Div(
            [
                html.Div("Licensed sponsors by region", style={
                    "fontFamily": "Inter, sans-serif", "fontSize": "14px",
                    "fontWeight": "700", "color": TEXT, "marginBottom": "4px",
                }),
                html.Div(
                    "This map shows where licensed sponsor companies are registered "
                    "across the UK. It does not show how many visas were granted in "
                    "each region - the government does not publish that figure, so "
                    "this is the closest available regional measure.",
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
                dcc.Loading(dcc.Graph(id="regional-heatmap-chart", config={"displayModeBar": False}), type="circle", color=BLUE),
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
                html.Div("Where are these sponsor companies registered?", style={
                    "fontFamily": "Inter, sans-serif", "fontSize": "14px",
                    "fontWeight": "700", "color": TEXT, "marginBottom": "4px",
                }),
                html.Div(
                    "The Companies tab showed you which employers hold a sponsor "
                    "licence. This globe shows where those employers are "
                    "registered, region by region. Darker blue means more "
                    "sponsors. Rotate it by dragging with your mouse, and zoom "
                    "with your scroll wheel - hover or click a region for its "
                    "exact number. It uses the same sector filter as the chart "
                    "above, and the same sponsor counts - it does not show visa "
                    "numbers.",
                    style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginBottom": "6px"},
                ),
                html.Div(
                    "Region boundaries: Office for National Statistics, Open "
                    "Geography Portal, December 2024 (Open Government Licence v3.0). "
                    "Source: Office for National Statistics licensed under the Open "
                    "Government Licence v.3.0.",
                    style={"fontSize": "11px", "color": TEXT_SECONDARY, "marginBottom": "10px"},
                ),
                dcc.Loading(
                    dcc.Graph(
                        id="regional-globe-chart",
                        config={"displayModeBar": False, "topojsonURL": "/assets/topojson/"},
                    ),
                    type="circle", color=BLUE,
                ),
                html.Div(
                    "The same numbers shown on the globe, listed by region:",
                    style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginTop": "12px", "marginBottom": "6px"},
                ),
                html.Div(id="regional-globe-accessible-list"),
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
                    "This is a different measure from the map above: the percentage "
                    "of people first sponsored in a region who still held valid UK "
                    "immigration status five years later. It reflects long-term "
                    "retention, not the number of sponsor companies.",
                    style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginBottom": "6px"},
                ),
                html.Div(
                    "Source: Migration Advisory Committee, \"Who Stays, Who Leaves?\" (2026).",
                    style={"fontSize": "11px", "color": TEXT_SECONDARY, "marginBottom": "10px"},
                ),
                dcc.Loading(dcc.Graph(id="mac-stay-rate-chart", config={"displayModeBar": False}), type="circle", color=BLUE),
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
            "This tab shows which nationalities were most commonly sponsored, by "
            "sector, using combined Home Office data.",
            style={"fontSize": "13px", "color": TEXT_SECONDARY, "marginBottom": "14px"},
        ),
        html.Div(
            [
                html.Div("Sponsored work visa grants by nationality", style={
                    "fontFamily": "Inter, sans-serif", "fontSize": "14px",
                    "fontWeight": "700", "color": TEXT, "marginBottom": "4px",
                }),
                html.Div(
                    "This combines two official Home Office datasets published in "
                    "different years. There is a genuine gap in the data from April "
                    "to September 2024. These months are not estimated or filled in "
                    "- the gap is shown as missing, consistent with the actual "
                    "published data.",
                    style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginBottom": "6px"},
                ),
                html.Div(
                    "Source datasets: Home Office, Immigration System Statistics - "
                    "Sponsored work entry clearance visas by occupation and industry. "
                    "SOC 2010 edition (2021 Q1-2024 Q1) and SOC 2020 edition "
                    "(2024 Q4-2026 Q1).",
                    style={"fontSize": "11px", "color": TEXT_SECONDARY, "marginBottom": "10px"},
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
                dcc.Loading(dcc.Graph(id="nationality-ranking-chart", config={"displayModeBar": False}), type="circle", color=BLUE),
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
                    "The dashed line marks where the underlying dataset changes from "
                    "the SOC 2010 to the SOC 2020 release. The two sides should be "
                    "read as separate snapshots, not as one continuous trend.",
                    style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginBottom": "6px"},
                ),
                html.Div(
                    "The Industry field used for sector mapping is the same in both "
                    "datasets, but they are still separate published releases, "
                    "extracted at different times.",
                    style={"fontSize": "11px", "color": TEXT_SECONDARY, "marginBottom": "10px"},
                ),
                dcc.Loading(dcc.Graph(id="nationality-trend-chart", config={"displayModeBar": False}), type="circle", color=BLUE),
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

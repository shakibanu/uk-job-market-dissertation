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
                    "The story above covered the national picture. The tabs above break "
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
                html.H3("How do vacancies compare across every sector at once?", style={
                    "fontFamily": "Inter, sans-serif", "fontSize": "14px",
                    "fontWeight": "700", "color": TEXT, "margin": "0 0 4px 0",
                }),
                html.Div(
                    dcc.Loading(dcc.Graph(id="small-multiples-chart", config={"displayModeBar": False}), type="circle", color=BLUE),
                    role="img", **{"aria-label": "Five small line charts comparing vacancy trends across all sectors on the same scale"},
                ),
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
        dcc.Loading(
            html.Div(
                dcc.Graph(id="sector-vacancy-chart", config={"displayModeBar": False}),
                className="panel", style={"marginBottom": "20px"},
                role="img", **{"aria-label": "Line chart of quarterly vacancies for the selected sector from 2021 to 2025, including a forecast"},
            ),
            type="circle", color=BLUE,
        ),
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
                html.H3("Sector sponsorship comparison", style={
                    "fontFamily": "Inter, sans-serif", "fontSize": "14px",
                    "fontWeight": "700", "color": TEXT, "margin": "0 0 4px 0",
                }),
                html.Div(
                    "Skilled Worker visa grants by sector, 2021 to 2025. Use the slider "
                    "or play control to see the change year by year.",
                    style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginBottom": "10px"},
                ),
                html.Div(
                    dcc.Loading(dcc.Graph(id="sponsorship-comparison-chart", config={"displayModeBar": False}), type="circle", color=BLUE),
                    role="img", **{"aria-label": "Animated bar chart of Skilled Worker visa grants by sector, 2021 to 2025"},
                ),
            ],
            className="panel",
            style={"marginBottom": "20px"},
        ),
        html.Div(
            [
                html.H3("Top skills mentioned in job postings", style={
                    "fontFamily": "Inter, sans-serif", "fontSize": "14px",
                    "fontWeight": "700", "color": TEXT, "margin": "0 0 4px 0",
                }),
                html.Div(
                    "Skills most frequently mentioned in job postings for this sector. "
                    "Based on a snapshot of around 250 Adzuna job postings per sector, "
                    "collected in June 2026, matched against a curated list of common "
                    "skills. This is indicative, not a live or exhaustive analysis.",
                    style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginBottom": "10px"},
                ),
                html.Div(
                    dcc.Loading(dcc.Graph(id="skills-chart", config={"displayModeBar": False}), type="circle", color=BLUE),
                    role="img", **{"aria-label": "Bar chart of the most frequently mentioned skills in job postings for the selected sector"},
                ),
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
        dcc.Store(id="company-table-page", data=0),
        html.Div(id="company-results-summary", style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginBottom": "8px"}),
        html.Div(id="company-table-container", className="panel"),
        html.Div(
            [
                html.Button("← Previous", id="company-prev-page", n_clicks=0, className="export-button"),
                html.Span(id="company-page-indicator", style={"margin": "0 12px", "fontSize": "13px", "color": TEXT_SECONDARY}),
                html.Button("Next →", id="company-next-page", n_clicks=0, className="export-button"),
            ],
            style={"display": "flex", "alignItems": "center", "marginTop": "10px"},
        ),
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
        dcc.Loading(
            html.Div(
                dcc.Graph(id="salary-chart", config={"displayModeBar": False}),
                className="panel",
                role="img", **{"aria-label": "Bar chart of median salary by sector for the selected year, with sectors below the visa salary threshold highlighted"},
            ),
            type="circle", color=BLUE,
        ),
        html.Div(
            [
                html.Span("● ", style={"color": DANGER}),
                "Red bars show a sector's median salary falling below that year's visa threshold. A role at this level would not qualify for Skilled Worker sponsorship, regardless of employer interest.",
            ],
            style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginTop": "10px"},
        ),
        html.Div(
            [
                html.H3("Which sector's salary grew fastest? 2021 vs 2025", style={
                    "fontFamily": "Inter, sans-serif", "fontSize": "14px",
                    "fontWeight": "700", "color": TEXT, "margin": "0 0 4px 0",
                }),
                html.Div(
                    "Technology's median salary grew faster than any other tracked sector "
                    "between 2021 and 2025.",
                    style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginBottom": "10px"},
                ),
                html.Div(
                    dcc.Loading(dcc.Graph(id="salary-slope-chart", config={"displayModeBar": False}), type="circle", color=BLUE),
                    role="img", **{"aria-label": "Line chart comparing each sector's median salary in 2021 versus 2025"},
                ),
            ],
            className="panel",
            style={"marginTop": "20px"},
        ),
        html.Div(
            [
                html.H3("Vacancies, salary, and visa grants together", style={
                    "fontFamily": "Inter, sans-serif", "fontSize": "14px",
                    "fontWeight": "700", "color": TEXT, "margin": "0 0 4px 0",
                }),
                html.Div(
                    "Drag to rotate. Each point is one sector-quarter, plotting three "
                    "real measures against each other - vacancy count, median salary, "
                    "and visa grants - coloured by sector, so you can see whether "
                    "higher vacancies or salary line up with more sponsorship in "
                    "practice.",
                    style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginBottom": "10px"},
                ),
                html.Div(
                    dcc.Loading(dcc.Graph(id="salary-surface-chart", config={"displayModeBar": False}), type="circle", color=BLUE),
                    role="img", **{"aria-label": "3D scatter chart plotting vacancy count, median salary and visa grants for each sector and quarter"},
                ),
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
        # Moved here, above the inputs/results/graph, so a general reader
        # sees what's being calculated and the actual equations used
        # before they start picking options or reading the graph -
        # supervisor feedback was that this was previously easy to miss
        # further down the page. Same five underlying steps as before,
        # just reordered/reworded for clarity and with the cumulative
        # salary advantage step (point 5) made explicit - this doesn't
        # change calculate_roi() or any of the numbers it returns, only
        # how they're explained.
        html.Div(
            [
                html.H3("How this is calculated", style={"fontWeight": "700", "margin": "0 0 6px 0", "fontSize": "13px"}),
                html.Div([
                    html.Div("1. Total cost = tuition (typical fee for your target sector) + monthly living cost × course length in months. This is the one-off cost of a one-year taught Master's. Tuition comes from published typical ranges per sector; living cost comes from UKCISA/gov.uk estimates for your chosen study location.", style={"marginBottom": "4px"}),
                    html.Div("2. Salary comparison = your target sector's UK median salary (ONS ASHE, most recent year) versus your home country's GDP per capita (World Bank), converted to pounds - a national average income figure, not a personal or profession-specific salary.", style={"marginBottom": "4px"}),
                    html.Div("3. Annual advantage = UK salary minus home-country income.", style={"marginBottom": "4px"}),
                    html.Div("4. Cumulative salary advantage (the rising line on the graph below) = annual advantage × number of years since graduating. It's the running total of extra earnings the UK figure gives you over the home-country figure, year by year.", style={"marginBottom": "4px"}),
                    html.Div("5. Break-even point = total cost ÷ annual advantage. This is the number of years it would take the cumulative salary advantage to cover the total cost - the point where the two lines on the graph below cross.", style={"marginBottom": "4px"}),
                ], style={"fontSize": "12px", "color": TEXT_SECONDARY}),
            ],
            style={"marginTop": "10px", "padding": "10px", "marginBottom": "20px"},
            className="panel",
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
            html.Div(
                dcc.Graph(id="roi-chart", config={"displayModeBar": False}),
                className="panel", style={"marginBottom": "20px"},
                role="img", **{"aria-label": "Line chart comparing cumulative salary advantage against total study cost over ten years"},
            ),
            type="circle", color=BLUE,
        ),
        html.Div(
            "What this does and doesn't mean: it's a rough financial estimate based on national averages, not "
            "a personal forecast - it doesn't know your actual salary offer, your personal spending habits, "
            "tax, or career progression. Home country income is GDP per capita since profession-specific "
            "income data isn't available for every country. Sponsorship activity here is a sector-level "
            "relative ranking based on visa grants versus vacancies, not a company-level estimate.",
            style={"fontSize": "11px", "color": TEXT_SECONDARY, "marginTop": "8px"},
        ),
    ],
    className="tab-body",
)

# The Sponsorship Fit tab (fit_calculator_tab) was removed from the
# dashboard UI here - supervisor feedback was that the Random Forest
# classifier's F1 score (0.488) did not meet the 0.65 reliability bar the
# project set, so the resulting company ranking wasn't reliable enough to
# present to users. The underlying experiment (sponsorship_classifier.py)
# and its evaluation are untouched; only this tab's layout, and its
# routing/callback in callbacks.py and its nav entry in app.py, were
# removed. See the dissertation for the full evaluation writeup.

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
                html.H3("Licensed sponsors by region", style={
                    "fontFamily": "Inter, sans-serif", "fontSize": "14px",
                    "fontWeight": "700", "color": TEXT, "margin": "0 0 4px 0",
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
                html.Div(
                    dcc.Loading(dcc.Graph(id="regional-heatmap-chart", config={"displayModeBar": False}), type="circle", color=BLUE),
                    role="img", **{"aria-label": "Horizontal bar chart of licensed sponsor organisations by UK region"},
                ),
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
                html.H3("Where are these sponsor companies registered?", style={
                    "fontFamily": "Inter, sans-serif", "fontSize": "14px",
                    "fontWeight": "700", "color": TEXT, "margin": "0 0 4px 0",
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
                html.Div(
                    dcc.Loading(
                        dcc.Graph(
                            id="regional-globe-chart",
                            config={"displayModeBar": False, "topojsonURL": "/assets/topojson/"},
                        ),
                        type="circle", color=BLUE,
                    ),
                    role="img",
                    **{"aria-label": "Interactive 3D globe showing licensed sponsor organisations by UK region, darker colour means more sponsors. An accessible table with the same figures follows below."},
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
                html.H3("Skilled Worker 5-year stay rate by region", style={
                    "fontFamily": "Inter, sans-serif", "fontSize": "14px",
                    "fontWeight": "700", "color": TEXT, "margin": "0 0 4px 0",
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
                html.Div(
                    dcc.Loading(dcc.Graph(id="mac-stay-rate-chart", config={"displayModeBar": False}), type="circle", color=BLUE),
                    role="img", **{"aria-label": "Chart of the five-year Skilled Worker visa stay rate by UK region"},
                ),
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
                html.Div([
                    "Office for National Statistics (2026) ",
                    html.I("Vacancies by industry (VACS02)"),
                    ". Available at: ",
                    html.A("https://www.ons.gov.uk/employmentandlabourmarket/peoplenotinwork/unemployment/datasets/vacanciesbyindustryvacs02", href="https://www.ons.gov.uk/employmentandlabourmarket/peoplenotinwork/unemployment/datasets/vacanciesbyindustryvacs02", target="_blank"),
                    " (Accessed: 2026).",
                ], style={"marginBottom": "10px"}),
                html.Div([
                    "Home Office (2026) ",
                    html.I("Register of licensed sponsors: workers"),
                    ". Available at: ",
                    html.A("https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers", href="https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers", target="_blank"),
                    " (Accessed: 2026).",
                ], style={"marginBottom": "10px"}),
                html.Div([
                    "Companies House (2026) ",
                    html.I("Companies House data products"),
                    ". Available at: ",
                    html.A("https://www.gov.uk/government/organisations/companies-house", href="https://www.gov.uk/government/organisations/companies-house", target="_blank"),
                    " (Accessed: 2026). Used to match sponsor organisations to a sector via SIC code.",
                ], style={"marginBottom": "10px"}),
                html.Div([
                    "Home Office (2026) ",
                    html.I("Immigration system statistics quarterly release"),
                    ". Available at: ",
                    html.A("https://www.gov.uk/government/collections/immigration-system-statistics-quarterly-release", href="https://www.gov.uk/government/collections/immigration-system-statistics-quarterly-release", target="_blank"),
                    " (Accessed: 2026). Skilled Worker visa grants by occupation, industry and nationality.",
                ], style={"marginBottom": "10px"}),
                html.Div([
                    "Office for National Statistics (2026) ",
                    html.I("Annual Survey of Hours and Earnings (ASHE)"),
                    ". Available at: ",
                    html.A("https://www.ons.gov.uk/ashe", href="https://www.ons.gov.uk/ashe", target="_blank"),
                    " (Accessed: 2026). Median salary by sector and year.",
                ], style={"marginBottom": "10px"}),
                html.Div([
                    "Adzuna (2026) ",
                    html.I("Adzuna API"),
                    ". Available at: ",
                    html.A("https://developer.adzuna.com/", href="https://developer.adzuna.com/", target="_blank"),
                    " (Accessed: June 2026). Job postings snapshot, used for active job counts and classifier training.",
                ], style={"marginBottom": "10px"}),
                html.Div([
                    "Migration Advisory Committee (2026) ",
                    html.I("Who Stays, Who Leaves?"),
                    ". Available at: ",
                    html.A("https://www.gov.uk/government/organisations/migration-advisory-committee", href="https://www.gov.uk/government/organisations/migration-advisory-committee", target="_blank"),
                    " (Accessed: 2026). Skilled Worker 5-year stay rate by region.",
                ], style={"marginBottom": "10px"}),
                html.Div([
                    "World Bank (2026) ",
                    html.I("GDP per capita (current US$)"),
                    ". Available at: ",
                    html.A("https://data.worldbank.org/indicator/NY.GDP.PCAP.CD", href="https://data.worldbank.org/indicator/NY.GDP.PCAP.CD", target="_blank"),
                    " (Accessed: 2026). Used as the home-country income comparison in the ROI calculator.",
                ], style={"marginBottom": "10px"}),
                html.Div([
                    "UK Council for International Student Affairs (2026) ",
                    html.I("Living costs for international students"),
                    ". Available at: ",
                    html.A("https://www.ukcisa.org.uk/", href="https://www.ukcisa.org.uk/", target="_blank"),
                    " (Accessed: 2026). Used for the monthly living-cost estimates in the ROI calculator.",
                ], style={"marginBottom": "10px"}),
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
                html.Div("What this chart is actually measuring", style={"fontWeight": "700", "marginBottom": "4px", "fontSize": "13px"}),
                html.Div(
                    "\"SOC\" stands for Standard Occupational Classification - the UK "
                    "government's system for grouping jobs into categories. The Home "
                    "Office updated this system in 2020, so older and newer figures "
                    "are published under two different editions (more on that below).",
                    style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginBottom": "6px"},
                ),
                html.Div(
                    "\"Visa grants\" means the number of Skilled Worker sponsored "
                    "work visas actually issued to people of that nationality in "
                    "that sector and quarter. A grant means the visa was approved "
                    "and issued - it doesn't mean a specific employer offered that "
                    "specific individual a job; it's a national count, not a record "
                    "of any single company's decision.",
                    style={"fontSize": "12px", "color": TEXT_SECONDARY, "marginBottom": "10px"},
                ),
            ],
            className="panel",
            style={"marginBottom": "14px"},
        ),
        html.Div(
            [
                html.H3("Sponsored work visa grants by nationality", style={
                    "fontFamily": "Inter, sans-serif", "fontSize": "14px",
                    "fontWeight": "700", "color": TEXT, "margin": "0 0 4px 0",
                }),
                html.Div(
                    "This combines two official Home Office datasets published in "
                    "different years. There is a genuine gap in the data from April "
                    "to September 2024. These months are not estimated or filled in "
                    "- the gap is shown as missing, consistent with the actual "
                    "published data.",
                    # genuinely explanatory (tells the reader how to read the
                    # chart), not a source citation - darkened from the
                    # secondary grey so it doesn't read as a skippable
                    # footnote (supervisor feedback); size unchanged
                    style={"fontSize": "12px", "color": TEXT, "marginBottom": "6px"},
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
                html.Div(
                    dcc.Loading(dcc.Graph(id="nationality-ranking-chart", config={"displayModeBar": False}), type="circle", color=BLUE),
                    role="img", **{"aria-label": "Horizontal bar chart of the top nationalities sponsored in the selected sector"},
                ),
            ],
            className="panel",
            style={"marginBottom": "20px"},
        ),
        html.Div(
            [
                html.H3("Grants over time, by quarter", style={
                    "fontFamily": "Inter, sans-serif", "fontSize": "14px",
                    "fontWeight": "700", "color": TEXT, "margin": "0 0 4px 0",
                }),
                html.Div(
                    "The dashed line marks where the underlying dataset changes from "
                    "the SOC 2010 to the SOC 2020 release. The two sides should be "
                    "read as separate snapshots, not as one continuous trend.",
                    # genuinely explanatory (tells the reader how to read the
                    # chart), not a source citation - same darkening as the
                    # panel above, size unchanged
                    style={"fontSize": "12px", "color": TEXT, "marginBottom": "6px"},
                ),
                html.Div(
                    "The Industry field used for sector mapping is the same in both "
                    "datasets, but they are still separate published releases, "
                    "extracted at different times.",
                    style={"fontSize": "11px", "color": TEXT_SECONDARY, "marginBottom": "10px"},
                ),
                html.Div(
                    dcc.Loading(dcc.Graph(id="nationality-trend-chart", config={"displayModeBar": False}), type="circle", color=BLUE),
                    role="img", **{"aria-label": "Line chart of visa grants by quarter and nationality, split by SOC dataset edition"},
                ),
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

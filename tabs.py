"""
tabs.py

This file builds the layout for each of the 4 tabs (Overview, Sectors,
Companies, Salary). The actual chart data gets filled in by the callbacks
in callbacks.py - this file just lays out the page structure.
"""

from dash import dcc, html
from data_loader import (
    SECTORS, TEXT, TEXT_SECONDARY, BLUE, TEAL, AMBER, DANGER,
    latest_year, total_sponsors, total_vacancies_latest, n_sectors,
    national_trend, master_df,
)
from dashboard_components import stat_card, pct_change

# Create the layout for the Overview tab
overview_tab = html.Div(
    [
        html.Div(
            [
                stat_card("Sectors covered", str(n_sectors), BLUE),
                stat_card("Licensed sponsors", f"{total_sponsors:,}", TEAL),
                stat_card("2025 salary threshold", "£41,700", AMBER),
                stat_card(
                    f"Vacancies ({latest_year})", f"{total_vacancies_latest:,}", BLUE, national_trend,
                    trend_pct=pct_change(national_trend), trend_caption="vs Q1 2021",
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

# Create the layout for the Sectors tab
sectors_tab = html.Div(
    [
        html.Label("Sector"),
        # Let the user choose a sector to explore
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
        ),
    ],
    className="tab-body",
)

companies_tab = html.Div(
    [
        html.Label("Search by city"),
        dcc.Input(
            id="city-search",
            type="text",
            placeholder="e.g. London",
            debounce=True,
            style={"maxWidth": "280px", "display": "block", "marginBottom": "20px"},
        ),
        html.Div(id="company-table-container", className="panel"),
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

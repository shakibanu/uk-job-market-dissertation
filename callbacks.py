"""
callbacks.py

This file has every callback that makes the dashboard interactive -
switching tabs, updating charts when a dropdown changes, and so on.

It also has style_fig(), which applies the same look to every chart so
they all match the rest of the dashboard instead of using Plotly's
default styling.
"""

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, html

from app_instance import app
from data_loader import (
    master_df, sponsors_df, SECTORS, SALARY_THRESHOLDS,
    SURFACE, BORDER, TEXT, TEXT_SECONDARY, BLUE, TEAL, AMBER, DANGER,
    gdp_df, tuition_df, living_cost_df,
)
from sarima_forecast import SARIMA_RESULTS
from roi_calculator import calculate_roi, get_sponsorship_activity_ranking
from sponsorship_classifier import SPONSORS_WITH_SECTOR, FIT_F1_SCORE, FIT_FEATURE_IMPORTANCE, rank_companies_by_sector
from skills_extraction import TOP_SKILLS_BY_SECTOR
from tabs import overview_tab, sectors_tab, companies_tab, salary_tab, roi_tab, fit_calculator_tab


# Apply the same layout and styling to every chart
def style_fig(fig):
    fig.update_layout(
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(family="Inter, sans-serif", color=TEXT_SECONDARY, size=12),
        title_font=dict(family="Inter, sans-serif", color=TEXT, size=18, weight="bold"),
        margin=dict(l=40, r=20, t=50, b=40),
        xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, linecolor=BORDER),
        yaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, linecolor=BORDER),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        # Add a smooth animation when the chart updates
        transition={"duration": 400, "easing": "cubic-in-out"},
    )
    return fig


# Now the callbacks that make the dashboard interactive

@app.callback(Output("tab-content", "children"), Input("main-tabs", "value"))
def render_tab(tab):
    return {
        "tab-overview": overview_tab,
        "tab-sectors": sectors_tab,
        "tab-companies": companies_tab,
        "tab-salary": salary_tab,
        "tab-roi": roi_tab,
        "tab-fit": fit_calculator_tab,
    }.get(tab, overview_tab)


@app.callback(Output("sector-vacancy-chart", "figure"), Input("sector-dropdown", "value"))
def update_sector_chart(sector):
    filtered = master_df[master_df["Sector"] == sector]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=filtered["Quarter"],
            y=filtered["Vacancy_Count"],
            mode="lines+markers",
            line=dict(color=BLUE, width=2),
            marker=dict(size=5, color=BLUE),
            fill="tozeroy",
            fillcolor="rgba(79, 124, 255, 0.08)",
        )
    )
    fig.update_layout(title=f"{sector} — vacancy count by quarter, with 4-quarter forecast")

    # Adding the SARIMA forecast on after the historical line, so it reads
    # as a continuation of the chart rather than a separate graph
    sarima_info = SARIMA_RESULTS[sector]
    future_quarters = sarima_info["future_quarters"]
    last_actual_quarter = filtered["Quarter"].iloc[-1]
    last_actual_vacancy_count = filtered["Vacancy_Count"].iloc[-1]

    # Start the forecast from the last recorded value
    forecast_dates = [last_actual_quarter] + future_quarters
    forecast_values = [last_actual_vacancy_count] + sarima_info["forecast"]
    forecast_ci95_lower = [last_actual_vacancy_count] + sarima_info["ci95_lower"]
    forecast_ci95_upper = [last_actual_vacancy_count] + sarima_info["ci95_upper"]
    forecast_ci80_lower = [last_actual_vacancy_count] + sarima_info["ci80_lower"]
    forecast_ci80_upper = [last_actual_vacancy_count] + sarima_info["ci80_upper"]

    # 95% band (wider, lighter)
    fig.add_trace(go.Scatter(
        x=forecast_dates + forecast_dates[::-1], y=forecast_ci95_upper + forecast_ci95_lower[::-1],
        fill="toself", fillcolor="rgba(242,169,59,0.12)", line=dict(width=0),
        showlegend=False, hoverinfo="skip",
    ))
    # 80% band (narrower, darker)
    fig.add_trace(go.Scatter(
        x=forecast_dates + forecast_dates[::-1], y=forecast_ci80_upper + forecast_ci80_lower[::-1],
        fill="toself", fillcolor="rgba(242,169,59,0.22)", line=dict(width=0),
        showlegend=False, hoverinfo="skip",
    ))
    # forecast line
    fig.add_trace(go.Scatter(
        x=forecast_dates, y=forecast_values, mode="lines+markers",
        line=dict(color=AMBER, width=2, dash="dash"),
        marker=dict(size=5, color=AMBER),
        name="Forecast (4Q)",
        hovertemplate="%{x}: %{y:,.0f} (forecast)<extra></extra>",
    ))

    # Mark the important events on the vacancy trend
    annotations = [
        ("2021-Q1", "Brexit\n(Jan 2021)", TEXT_SECONDARY),
        ("2022-Q2", "Vacancy peak\n(Apr 2022)", TEAL),
        ("2024-Q2", "Threshold rise\n(Apr 2024)", AMBER),
        ("2025-Q2", "Threshold rise\n(Apr 2025)", AMBER),
    ]
    for quarter, label, colour in annotations:
        if quarter in filtered["Quarter"].values:
            fig.add_vline(x=quarter, line_width=1, line_dash="dot", line_color=colour, opacity=0.6)
            fig.add_annotation(
                x=quarter, y=filtered["Vacancy_Count"].max(),
                text=label, showarrow=False, yshift=18,
                font=dict(size=9, color=colour), align="center",
            )
    y_max = max(filtered["Vacancy_Count"].max(), max(sarima_info["ci95_upper"]))
    fig.update_yaxes(range=[0, y_max * 1.3])
    return style_fig(fig)


@app.callback(Output("sarima-diagnostics", "children"), Input("sector-dropdown", "value"))
def update_sarima_diagnostics(sector):
    sarima_info = SARIMA_RESULTS[sector]
    p, d, q = sarima_info["order"]
    P, D, Q, m = sarima_info["seasonal_order"]
    is_flat = len(set(sarima_info["forecast"])) == 1

    rows = [
        html.Div([
            html.Span("Model: ", style={"color": TEXT_SECONDARY}),
            html.Span(f"SARIMA({p},{d},{q})({P},{D},{Q})[{m}]", style={"fontWeight": "600"}),
        ], style={"fontSize": "13px", "marginBottom": "4px"}),
        html.Div([
            html.Span("AIC: ", style={"color": TEXT_SECONDARY}),
            html.Span(f"{sarima_info['aic']}", style={"fontWeight": "600"}),
            html.Span("   BIC: ", style={"color": TEXT_SECONDARY, "marginLeft": "16px"}),
            html.Span(f"{sarima_info['bic']}", style={"fontWeight": "600"}),
        ], style={"fontSize": "13px", "marginBottom": "8px"}),
    ]
    if is_flat:
        rows.append(html.Div(
            "⚠ auto_arima did not detect a seasonal pattern for this sector with only "
            "20 quarters of data — the forecast is effectively flat (a simple trend "
            "projection, not a seasonal model). This is a genuine result, not an error; "
            "see the Methodology's limitations for why short series constrain SARIMA fitting.",
            style={"fontSize": "12px", "color": AMBER, "background": "rgba(217,119,6,0.08)",
                   "padding": "10px", "borderRadius": "8px"},
        ))
    else:
        rows.append(html.Div(
            "Seasonal pattern detected. Shaded bands show the 80% (darker) and 95% "
            "(lighter) confidence intervals — forecasts get less certain further out.",
            style={"fontSize": "12px", "color": TEXT_SECONDARY},
        ))
    return rows


@app.callback(Output("skills-chart", "figure"), Input("sector-dropdown", "value"))
def update_skills_chart(sector):
    skills_df = TOP_SKILLS_BY_SECTOR.get(sector)

    fig = go.Figure()
    if skills_df is None or skills_df.empty:
        fig.update_layout(title=f"No skills data available for {sector}")
        return style_fig(fig)

    # sorting ascending so the horizontal bar chart shows the top skill
    # at the top, not the bottom
    skills_df = skills_df.sort_values("Postings_Mentioning", ascending=True)

    fig.add_trace(go.Bar(
        x=skills_df["Postings_Mentioning"],
        y=skills_df["Skill"],
        orientation="h",
        marker_color=BLUE,
        text=skills_df["Postings_Mentioning"],
        textposition="outside",
        hovertemplate="%{y}: mentioned in %{x} postings<extra></extra>",
    ))
    fig.update_layout(
        title=f"Top skills mentioned in {sector} job postings",
        xaxis_title="Number of postings mentioning this skill",
    )
    return style_fig(fig)


@app.callback(Output("sponsorship-comparison-chart", "figure"), Input("main-tabs", "value"))
def update_sponsorship_comparison(_):
    # Keep one record for each sector and year before creating the animation
    yearly = master_df.groupby(["Year", "Sector"])["Visa_Grants"].first().reset_index()
    years = sorted(yearly["Year"].unique())
    sector_colours = {SECTORS[i]: [BLUE, TEAL, AMBER, BLUE, TEAL][i % 5] for i in range(len(SECTORS))}

    y_max = yearly["Visa_Grants"].max() * 1.15

    frames = []
    for year in years:
        frame_data = yearly[yearly["Year"] == year].sort_values("Sector")
        frames.append(
            go.Frame(
                data=[
                    go.Bar(
                        x=frame_data["Sector"],
                        y=frame_data["Visa_Grants"],
                        marker_color=[sector_colours[s] for s in frame_data["Sector"]],
                        text=frame_data["Visa_Grants"].apply(lambda v: f"{v:,}"),
                        textposition="outside",
                        hovertemplate="%{x}: %{y:,} visa grants<extra></extra>",
                    )
                ],
                # Big year label so it's obvious which year is showing while
                # the animation is playing, not just the small slider text
                layout=go.Layout(
                    annotations=[dict(
                        text=str(year), x=0.98, y=0.95, xref="paper", yref="paper",
                        showarrow=False, font=dict(size=36, color=TEXT_SECONDARY), xanchor="right",
                    )]
                ),
                name=str(year),
            )
        )

    first_year_data = yearly[yearly["Year"] == years[0]].sort_values("Sector")
    fig = go.Figure(
        data=[
            go.Bar(
                x=first_year_data["Sector"],
                y=first_year_data["Visa_Grants"],
                marker_color=[sector_colours[s] for s in first_year_data["Sector"]],
                text=first_year_data["Visa_Grants"].apply(lambda v: f"{v:,}"),
                textposition="outside",
                hovertemplate="%{x}: %{y:,} visa grants<extra></extra>",
            )
        ],
        frames=frames,
    )

    fig.update_layout(
        yaxis=dict(range=[0, y_max]),
        # Same big year label needs to be on the starting view too, not
        # just inside the frames, otherwise it's missing before Play is pressed
        annotations=[dict(
            text=str(years[0]), x=0.98, y=0.95, xref="paper", yref="paper",
            showarrow=False, font=dict(size=36, color=TEXT_SECONDARY), xanchor="right",
        )],
        updatemenus=[
            {
                "type": "buttons",
                "showactive": False,
                "x": 0, "y": 1.15, "xanchor": "left",
                "buttons": [
                    {
                        "label": "▶ Play",
                        "method": "animate",
                        "args": [None, {"frame": {"duration": 900, "redraw": True}, "fromcurrent": True, "transition": {"duration": 300}}],
                    },
                    {
                        "label": "⏸ Pause",
                        "method": "animate",
                        "args": [[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}],
                    },
                ],
            }
        ],
        sliders=[
            {
                "active": 0,
                "x": 0.08, "y": -0.02, "len": 0.9,
                "currentvalue": {"prefix": "Year: ", "font": {"size": 12}},
                "steps": [
                    {
                        "label": str(year),
                        "method": "animate",
                        "args": [[str(year)], {"frame": {"duration": 300, "redraw": True}, "mode": "immediate"}],
                    }
                    for year in years
                ],
            }
        ],
    )
    fig.update_layout(title="Skilled Worker visa grants by sector")
    return style_fig(fig)


@app.callback(
    Output("company-table-container", "children"),
    Input("city-search", "value"),
    Input("company-sector-filter", "value"),
)
def update_company_table(search_value, sector_value):
    results = sponsors_df

    # Filter by sector first, if one is selected
    if sector_value:
        results = results[results["Sector"] == sector_value]

    # Show the first few companies when no city has been searched yet -
    # sorting by sector first, so the default view actually shows some
    # enriched rows instead of a random alphabetical slice that's mostly
    # blank (only about 18% of sponsors have a matched sector)
    if not search_value:
        results = results.sort_values("Sector", na_position="last").head(10)
    # Search for companies that match the selected city
    else:
        results = results[results["City"].str.contains(search_value, case=False, na=False)]
        # Sort the matching companies by the number of active job postings
        results = results.sort_values("Active_Job_Count", ascending=False, na_position="last").head(50)

    # showing a dash instead of a blank cell for companies with no Adzuna
    # match or no matched sector, so it's clear this is expected, not
    # missing/broken data
    results = results.copy()
    results["Active_Job_Count"] = results["Active_Job_Count"].apply(
        lambda v: str(int(v)) if pd.notna(v) else "—"
    )
    results["Sector"] = results["Sector"].fillna("—")

    if results.empty:
        return html.P("No sponsors found matching that search.", style={"color": TEXT_SECONDARY})

    return dbc.Table.from_dataframe(results, striped=True, bordered=False, hover=True, size="sm")


@app.callback(Output("salary-chart", "figure"), Input("salary-year-dropdown", "value"))
def update_salary_chart(year):
    year_data = master_df[master_df["Year"] == year].groupby("Sector")["Median_Salary"].first().reset_index()
    threshold = SALARY_THRESHOLDS[year]

    # Compare each sector's salary with the visa salary threshold
    bar_colours = [DANGER if salary < threshold else BLUE for salary in year_data["Median_Salary"]]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=year_data["Sector"],
            y=year_data["Median_Salary"],
            marker_color=bar_colours,
            text=year_data["Median_Salary"].apply(lambda v: f"£{v:,}"),
            textposition="inside",
            insidetextfont=dict(color="white", size=12),
            hovertemplate="%{x}: £%{y:,}<extra></extra>",
            name="Median salary",
        )
    )
    # Add the visa salary threshold as a reference line
    fig.add_hline(
        y=threshold,
        line_dash="dash",
        line_color=AMBER,
        annotation_text=f"Visa threshold: £{threshold:,}",
        annotation_position="top left",
        annotation_font=dict(size=11, color=AMBER),
    )
    fig.update_layout(
        title=f"Median salary by sector vs Skilled Worker threshold — {year}",
        yaxis_title="£ per year",
    )
    fig.update_yaxes(range=[0, year_data["Median_Salary"].max() * 1.25])
    return style_fig(fig)


@app.callback(
    Output("roi-results-container", "children"),
    Output("roi-chart", "figure"),
    Input("roi-country-dropdown", "value"),
    Input("roi-sector-dropdown", "value"),
    Input("roi-region-dropdown", "value"),
)
def update_roi_results(country, sector, region):
    result = calculate_roi(country, sector, master_df, gdp_df, tuition_df, living_cost_df, region=region)

    if "error" in result:
        error_message = html.P(result["error"], style={"color": DANGER})
        return error_message, style_fig(go.Figure())

    # showing the sponsorship activity ranking for the selected sector,
    # alongside the cost/salary numbers
    ranking_df = get_sponsorship_activity_ranking(master_df)
    sector_activity = ranking_df[ranking_df["Sector"] == sector]["Activity_Level"].iloc[0]

    results_display = html.Div(
        [
            html.Div(
                [
                    html.Div(f"£{result['total_cost']:,}", className="stat-value"),
                    html.Div("Total cost (tuition + living)", className="stat-label"),
                ],
                style={"marginRight": "40px"},
            ),
            html.Div(
                [
                    html.Div(f"£{result['uk_salary']:,}", className="stat-value"),
                    html.Div(f"Median {sector} salary in the UK", className="stat-label"),
                ],
                style={"marginRight": "40px"},
            ),
            html.Div(
                [
                    html.Div(
                        f"{result['break_even_year']} years" if result["breaks_even"] else "Doesn't break even",
                        className="stat-value",
                        style={"color": TEAL if result["breaks_even"] else DANGER},
                    ),
                    html.Div("Estimated break-even point", className="stat-label"),
                ],
                style={"marginRight": "40px"},
            ),
            html.Div(
                [
                    html.Div(sector_activity, className="stat-value", style={"fontSize": "20px"}),
                    html.Div(f"{sector} sponsorship activity (relative to other sectors)", className="stat-label"),
                ],
            ),
        ],
        style={"display": "flex", "flexWrap": "wrap", "gap": "20px"},
    )

    # building a simple cumulative cost vs cumulative earnings-advantage
    # chart, showing where the two lines cross (the break-even point)
    years = list(range(0, 11))
    cumulative_cost = [result["total_cost"]] * len(years)  # cost is paid up front, stays flat
    cumulative_advantage = [result["annual_advantage"] * y for y in years]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=cumulative_cost, mode="lines", name="Total cost", line=dict(color=DANGER, width=2, dash="dash")))
    fig.add_trace(go.Scatter(x=years, y=cumulative_advantage, mode="lines", name="Cumulative salary advantage", line=dict(color=TEAL, width=2)))
    fig.update_layout(
        title=f"Cumulative salary advantage vs total cost — {sector} in the UK vs {country}",
        xaxis_title="Years after graduating",
        yaxis_title="£",
    )
    return results_display, style_fig(fig)


@app.callback(
    Output("fit-results-container", "children"),
    Output("fit-model-card", "children"),
    Input("fit-sector-dropdown", "value"),
)
def update_fit_calculator(sector):
    ranked_companies = rank_companies_by_sector(sector, SPONSORS_WITH_SECTOR)

    if ranked_companies.empty:
        results_display = html.P(f"No companies found for {sector}.", style={"color": TEXT_SECONDARY})
    else:
        results_display = dbc.Table.from_dataframe(ranked_companies, striped=True, bordered=False, hover=True, size="sm")

    # being upfront in the model card about why this uses the rule-based
    # fallback and not the Random Forest directly - the F1 score wasn't
    # reliable enough to present as a real prediction
    model_card = html.Div(
        [
            html.P(
                f"This ranking uses a rule-based approach, not the Random Forest classifier directly. "
                f"The Random Forest was trained and evaluated with 5-fold cross-validation, but its "
                f"F1 score ({FIT_F1_SCORE:.2f}) came in below the 0.65 reliability bar set for this "
                f"feature, so its predictions aren't trustworthy enough to present as real probabilities.",
                style={"fontSize": "13px", "marginBottom": "8px"},
            ),
            html.P(
                "Why the F1 score is low: the Home Office Sponsors Register only has 4 columns to "
                "begin with, and the training label (whether a company appears in Adzuna job postings) "
                "has a hard ceiling of about 200 possible positive examples out of 122,015 sponsors, "
                "since only 201 companies exist in the Adzuna data at all. That's too little signal "
                "for a reliable prediction, even with SMOTE.",
                style={"fontSize": "13px", "marginBottom": "8px"},
            ),
            html.P(
                f"Random Forest feature importance (diagnostic only, not used for these rankings): "
                f"Sector {FIT_FEATURE_IMPORTANCE.get('Sector_Encoded', 0):.1%}, "
                f"Type Rating {FIT_FEATURE_IMPORTANCE.get('Type_Rating_Encoded', 0):.1%}.",
                style={"fontSize": "13px", "marginBottom": "8px"},
            ),
            html.P(
                "What the ranking above actually uses instead: sector match, sponsor rating tier "
                "(Premium/SME+ sponsors ranked higher), and whether the company has a real Adzuna job "
                "posting - the closest thing to genuine evidence of active hiring in the data.",
                style={"fontSize": "13px", "color": TEXT_SECONDARY},
            ),
        ]
    )

    return results_display, model_card

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
from plotly.subplots import make_subplots
from dash import Input, Output, State, html, dcc, ctx, ALL

from app_instance import app
from data_loader import (
    master_df, sponsors_df, SECTORS, SALARY_THRESHOLDS,
    SURFACE, BORDER, TEXT, TEXT_SECONDARY, BLUE, TEAL, AMBER, DANGER,
    gdp_df, tuition_df, living_cost_df,
    mac_stay_rate_df, REGION_MAPPED_COUNT, REGION_TOTAL_COUNT,
    nationality_df, ALL_POSSIBLE_QUARTERS,
)
from sarima_forecast import SARIMA_RESULTS
from roi_calculator import calculate_roi, get_sponsorship_activity_ranking
from sponsorship_classifier import SPONSORS_WITH_SECTOR, FIT_F1_SCORE, FIT_FEATURE_IMPORTANCE, rank_companies_by_sector
from skills_extraction import TOP_SKILLS_BY_SECTOR
from tabs import overview_tab, sectors_tab, companies_tab, salary_tab, roi_tab, fit_calculator_tab, regional_tab, sources_tab, nationality_tab


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
        "tab-regional": regional_tab,
        "tab-nationality": nationality_tab,
        "tab-sources": sources_tab,
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
    # checking the actual seasonal terms (P, D, Q) rather than whether the
    # forecast happens to be flat - a non-seasonal AR/MA term can still
    # produce a varying forecast (e.g. a trend) with zero real seasonality,
    # so flatness isn't a reliable signal of whether seasonality was found
    has_seasonal_component = P != 0 or D != 0 or Q != 0

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
    if not has_seasonal_component:
        rows.append(html.Div(
            "⚠ No seasonal component detected for this sector with only 20 quarters "
            "of data — auto_arima selected a non-seasonal model, so the forecast is "
            "a trend projection rather than a seasonal one. This is a genuine result, "
            "not an error; see the Methodology's limitations for why short series "
            "constrain SARIMA fitting.",
            style={"fontSize": "12px", "color": AMBER, "background": "rgba(217,119,6,0.08)",
                   "padding": "10px", "borderRadius": "8px"},
        ))
    else:
        rows.append(html.Div(
            "Seasonal component detected. Shaded bands show the 80% (darker) and 95% "
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
    Input("favourites-only-toggle", "value"),
    Input("bookmarked-companies", "data"),
)
def update_company_table(search_value, sector_value, favourites_only, bookmarked):
    results = sponsors_df

    # Filter by sector first, if one is selected
    if sector_value:
        results = results[results["Sector"] == sector_value]

    # bookmarked-companies stores {"bookmarked": [...], "last_clicks": {...}}
    # so the actual list needs pulling out - using the raw dict directly
    # here made every isin() check compare against the dict's keys
    # ("bookmarked", "last_clicks") instead of real company names, so no
    # company could ever match
    bookmarked = (bookmarked or {}).get("bookmarked", [])
    # Favourites-only filter (S4-13) - showing just the bookmarked
    # companies, applied before the usual search/sort logic below
    if favourites_only:
        results = results[results["Organisation"].isin(bookmarked)]

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
        message = "No bookmarked companies yet - use the star to save one." if favourites_only else "No sponsors found matching that search."
        return html.P(message, style={"color": TEXT_SECONDARY})

    # Building the table manually instead of dbc.Table.from_dataframe, so
    # each row can have its own bookmark star button (from_dataframe
    # doesn't support per-row interactive elements)
    header = html.Thead(html.Tr(
        [html.Th("")] + [html.Th(col) for col in results.columns]
    ))
    body_rows = []
    for _, row in results.iterrows():
        company_name = row["Organisation"]
        is_bookmarked = company_name in bookmarked
        star = html.Button(
            "★" if is_bookmarked else "☆",
            id={"type": "bookmark-star", "index": company_name},
            className="bookmark-star bookmark-star--active" if is_bookmarked else "bookmark-star",
        )
        body_rows.append(html.Tr([html.Td(star)] + [html.Td(row[col]) for col in results.columns]))

    return dbc.Table([header, html.Tbody(body_rows)], striped=True, bordered=False, hover=True, size="sm")


@app.callback(
    Output("bookmarked-companies", "data"),
    Input({"type": "bookmark-star", "index": ALL}, "n_clicks"),
    State("bookmarked-companies", "data"),
    prevent_initial_call=True,
)
def toggle_bookmark(n_clicks_list, store_data):
    # When the bookmark list changes, the company table re-renders and
    # recreates every star button - including the one just clicked. Dash
    # carries the same n_clicks value over to the new button and reports
    # it as a fresh trigger, which made a single real click immediately
    # bookmark then un-bookmark the same company. Fixed by tracking each
    # company's last-seen n_clicks value and only toggling on a genuine
    # increase, not just any non-null value showing up again.
    store_data = store_data or {"bookmarked": [], "last_clicks": {}}
    bookmarked = store_data.get("bookmarked", [])
    last_clicks = store_data.get("last_clicks", {})

    triggered = ctx.triggered_id
    if triggered is None:
        return store_data
    company_name = triggered["index"]

    new_n_clicks = ctx.triggered[0]["value"] or 0
    previously_seen = last_clicks.get(company_name, 0)

    if new_n_clicks > previously_seen:
        if company_name in bookmarked:
            bookmarked = [c for c in bookmarked if c != company_name]
        else:
            bookmarked = bookmarked + [company_name]

    last_clicks[company_name] = new_n_clicks
    return {"bookmarked": bookmarked, "last_clicks": last_clicks}


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
    # This chart updates on every dropdown change (country, sector, region),
    # which can happen faster than style_fig()'s 400ms transition duration.
    # When a new figure arrives while Plotly is still animating the
    # previous one, the visible chart (including the title) can render
    # one selection behind the real data - confirmed by testing rapid
    # selections and checking the actual rendered SVG text, not just the
    # underlying figure object. Turning the transition off for this
    # specific chart fixes it, without touching the calculation logic or
    # any other chart's smooth-transition behaviour.
    styled_fig = style_fig(fig)
    styled_fig.update_layout(transition={"duration": 0})
    return results_display, styled_fig


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


@app.callback(
    Output("regional-heatmap-chart", "figure"),
    Output("regional-coverage-note", "children"),
    Input("regional-sector-filter", "value"),
)
def update_regional_heatmap(sector_filter):
    # Licensed sponsor organisations by region - this is NOT visa grant
    # data, since the Home Office doesn't publish Skilled Worker visas
    # by region. This counts where sponsor companies are registered.
    results = sponsors_df[sponsors_df["Region"].notna()]
    if sector_filter:
        results = results[results["Sector"] == sector_filter]

    region_counts = results["Region"].value_counts().sort_values(ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=region_counts.values,
        y=region_counts.index,
        orientation="h",
        marker_color=BLUE,
        text=region_counts.values,
        texttemplate="%{text:,}",
        textposition="outside",
        hovertemplate="%{y}: %{x:,} sponsors<extra></extra>",
    ))
    title_suffix = f" — {sector_filter}" if sector_filter else " — all sectors"
    fig.update_layout(title=f"Licensed sponsor organisations by region{title_suffix}")
    fig.update_xaxes(title="Number of sponsors")

    # the coverage note reflects the current filter, not just the overall
    # dataset total, since filtering by sector changes how many results
    # are actually shown in the chart above
    shown = len(results)
    if sector_filter:
        coverage_text = (
            f"Showing {shown:,} sponsors in {sector_filter} with a known region. "
            f"Overall, {REGION_MAPPED_COUNT:,} of {REGION_TOTAL_COUNT:,} sponsors "
            f"({REGION_MAPPED_COUNT/REGION_TOTAL_COUNT*100:.2f}%) have a matched region."
        )
    else:
        coverage_text = (
            f"Coverage: {REGION_MAPPED_COUNT:,} of {REGION_TOTAL_COUNT:,} sponsors "
            f"({REGION_MAPPED_COUNT/REGION_TOTAL_COUNT*100:.2f}%) matched to a region "
            f"from the City field. The remaining "
            f"{REGION_TOTAL_COUNT-REGION_MAPPED_COUNT:,} are mostly small towns not "
            f"in the mapping, or genuinely ambiguous place names (e.g. Richmond, "
            f"Newport) that were deliberately left unmapped rather than guessed."
        )
    return style_fig(fig), coverage_text


@app.callback(Output("mac-stay-rate-chart", "figure"), Input("main-tabs", "value"))
def update_mac_stay_rate_chart(_):
    # The MAC's Skilled Worker 5-year stay rate by region - a retention
    # measure, kept completely separate from the sponsor count above.
    # Sorted the same way (ascending) so the two charts are easy to
    # visually compare region by region without implying they're the
    # same kind of number.
    data = mac_stay_rate_df.sort_values("Stay_Rate_Percent", ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=data["Stay_Rate_Percent"],
        y=data["Region"],
        orientation="h",
        marker_color=TEAL,
        text=data["Stay_Rate_Percent"],
        texttemplate="%{text}%",
        textposition="outside",
        hovertemplate="%{y}: %{x}%% stay rate<extra></extra>",
    ))
    fig.update_layout(title="Skilled Worker 5-year stay rate by region (MAC, 2026)")
    fig.update_xaxes(title="% still holding valid immigration status after 5 years", range=[0, 100])
    return style_fig(fig)


@app.callback(
    Output("nationality-filter-dropdown", "options"),
    Input("nationality-sector-dropdown", "value"),
)
def update_nationality_filter_options(sector):
    # only listing nationalities that actually have data for this sector,
    # ranked by total grants so the most relevant ones are easiest to find
    # in the dropdown rather than scrolling through all 187
    sector_data = nationality_df[nationality_df["Sector"] == sector]
    totals = sector_data.groupby("Nationality")["Grants"].sum().sort_values(ascending=False)
    return [{"label": n, "value": n} for n in totals.index]


@app.callback(
    Output("nationality-ranking-chart", "figure"),
    Input("nationality-sector-dropdown", "value"),
    Input("nationality-filter-dropdown", "value"),
)
def update_nationality_ranking(sector, highlighted_nationality):
    # ranking is a total across every available quarter (2021 Q1-2026 Q1,
    # excluding the genuinely missing 2024 Q2-Q3) - this doesn't claim a
    # continuous trend, it's just "who's been sponsored in this sector
    # across the whole period we have real data for"
    sector_data = nationality_df[nationality_df["Sector"] == sector]
    totals = sector_data.groupby("Nationality")["Grants"].sum().sort_values(ascending=False)

    top10 = totals.head(10)
    # if the selected nationality isn't already in the top 10, showing top
    # 9 + the selected one instead of top 10 - otherwise a user could pick
    # a nationality from the dropdown that never appears in the chart at
    # all, with nothing to actually highlight
    if highlighted_nationality and highlighted_nationality not in top10.index and highlighted_nationality in totals.index:
        display = pd.concat([top10.head(9), totals[[highlighted_nationality]]])
    else:
        display = top10
    display = display.sort_values(ascending=True)

    colours = [AMBER if n == highlighted_nationality else BLUE for n in display.index]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=display.values, y=display.index, orientation="h",
        marker_color=colours,
        text=display.values, texttemplate="%{text:,}", textposition="outside",
        hovertemplate="%{y}: %{x:,} grants<extra></extra>",
    ))
    fig.update_layout(title=f"Top nationalities sponsored — {sector} (all available quarters combined)")
    fig.update_xaxes(title="Total visa grants")
    return style_fig(fig)


@app.callback(
    Output("nationality-trend-raw", "data"),
    Input("nationality-sector-dropdown", "value"),
    Input("nationality-filter-dropdown", "value"),
)
def update_nationality_trend(sector, highlighted_nationality):
    sector_data = nationality_df[nationality_df["Sector"] == sector]
    if highlighted_nationality:
        sector_data = sector_data[sector_data["Nationality"] == highlighted_nationality]

    quarterly = sector_data.groupby(["Quarter", "Source_Dataset"])["Grants"].sum().reset_index()

    # building each source's series against the FULL quarter list, so the
    # 2024 Q2-Q3 gap shows up as real empty space on the x-axis rather
    # than the chart just skipping straight over it
    soc2010 = quarterly[quarterly["Source_Dataset"] == "SOC 2010"].set_index("Quarter")["Grants"]
    soc2020 = quarterly[quarterly["Source_Dataset"] == "SOC 2020"].set_index("Quarter")["Grants"]
    soc2010_y = [soc2010.get(q) for q in ALL_POSSIBLE_QUARTERS]
    soc2020_y = [soc2020.get(q) for q in ALL_POSSIBLE_QUARTERS]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ALL_POSSIBLE_QUARTERS, y=soc2010_y, mode="lines+markers", name="SOC 2010 dataset",
        line=dict(color=BLUE, width=2), marker=dict(size=5),
        connectgaps=False, hovertemplate="%{x}: %{y:,} grants<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=ALL_POSSIBLE_QUARTERS, y=soc2020_y, mode="lines+markers", name="SOC 2020 dataset",
        line=dict(color=TEAL, width=2), marker=dict(size=5),
        connectgaps=False, hovertemplate="%{x}: %{y:,} grants<extra></extra>",
    ))

    title_suffix = f" — {highlighted_nationality}" if highlighted_nationality else " — all nationalities"
    fig.update_layout(title=f"{sector} visa grants by quarter{title_suffix}")
    fig.update_xaxes(title="Quarter", tickangle=-90, tickfont=dict(size=9))
    fig.update_yaxes(title="Grants")

    # marking exactly where the two official datasets meet, so the reader
    # sees this as a source change rather than a smooth continuation
    # this chart updates every time the sector or nationality dropdown
    # changes, which can happen faster than style_fig()'s 400ms transition -
    # confirmed by testing rapid consecutive nationality selections and
    # checking the actual rendered SVG title, same issue and same fix as
    # the ROI chart. Local to this chart only.
    styled_fig = style_fig(fig)
    styled_fig.update_layout(transition={"duration": 0})

    # returning the figure together with exactly which sector/nationality
    # it was computed for (straight from this callback's own arguments,
    # not a separate counter that could get out of sync) - the clientside
    # callback below compares this against whatever is CURRENTLY selected
    # before displaying it, so a slow, older response can't overwrite a
    # newer one just because it happens to arrive later
    return {"figure": styled_fig.to_dict(), "sector": sector, "nationality": highlighted_nationality}


# This clientside callback fixes a stale-response race condition on the
# nationality trend chart: if a user changes the nationality dropdown
# quickly, the server can take slightly different amounts of time to
# respond to each request, so an older response can arrive after a
# newer one. Confirmed this with a stress test (artificially varying
# server response time) - without this fix, 5-7 out of 7 rapid
# selections displayed the wrong, stale nationality.
#
# This runs in the browser, comparing the sector/nationality the
# incoming response was actually computed for against whatever is
# CURRENTLY selected in the dropdowns right now - if they don't match,
# the response is stale (the user has moved on to a different
# selection since this request was made) and gets ignored instead of
# overwriting the chart with outdated data.
app.clientside_callback(
    """
    function(rawData, currentSector, currentNationality) {
        if (!rawData) {
            return window.dash_clientside.no_update;
        }
        // treating null and undefined as the same "nothing selected" state -
        // JavaScript considers them different values by default, which was
        // silently blocking every comparison when no nationality is picked
        const normalise = function(v) { return (v === undefined || v === null) ? null : v; };
        if (normalise(rawData.sector) !== normalise(currentSector) ||
            normalise(rawData.nationality) !== normalise(currentNationality)) {
            return window.dash_clientside.no_update;
        }
        return rawData.figure;
    }
    """,
    Output("nationality-trend-chart", "figure"),
    Input("nationality-trend-raw", "data"),
    State("nationality-sector-dropdown", "value"),
    State("nationality-filter-dropdown", "value"),
)


@app.callback(Output("salary-slope-chart", "figure"), Input("main-tabs", "value"))
def update_salary_slope_chart(_):
    # a simple two-point comparison per sector - 2021 vs 2025 median
    # salary, using the corrected VACS02-era master dataset. This answers
    # "which sector's salary grew fastest" at a glance, which a bar chart
    # showing 5 separate years doesn't do as clearly
    fig = go.Figure()
    for i, sector in enumerate(SECTORS):
        sector_data = master_df[master_df["Sector"] == sector]
        salary_2021 = sector_data[sector_data["Year"] == 2021]["Median_Salary"].iloc[0]
        salary_2025 = sector_data[sector_data["Year"] == 2025]["Median_Salary"].iloc[0]
        colour = [BLUE, TEAL, AMBER, DANGER, "#8B5CF6"][i % 5]
        fig.add_trace(go.Scatter(
            x=["2021", "2025"], y=[salary_2021, salary_2025],
            mode="lines+markers+text", name=sector,
            line=dict(color=colour, width=2), marker=dict(size=8),
            # only labelling the 2025 endpoint - labelling both ends
            # caused the 2021-side text to overlap badly, since several
            # sectors start at a similar salary
            text=["", f"{sector}: £{salary_2025:,}"],
            textposition="middle right",
            hovertemplate="%{x}: £%{y:,}<extra></extra>",
        ))
    fig.update_layout(title="Median salary by sector, 2021 vs 2025", showlegend=True)
    fig.update_xaxes(range=[-0.3, 1.5])
    return style_fig(fig)


@app.callback(Output("small-multiples-chart", "figure"), Input("main-tabs", "value"))
def update_small_multiples(_):
    # 5 mini panels, one per sector, all sharing the same y-axis scale so
    # they're genuinely comparable at a glance - using the corrected
    # VACS02 vacancy data, same source the Sectors tab already uses
    fig = make_subplots(rows=1, cols=5, subplot_titles=SECTORS, shared_yaxes=True)
    for i, sector in enumerate(SECTORS):
        sector_data = master_df[master_df["Sector"] == sector].sort_values("Quarter")
        fig.add_trace(
            go.Scatter(
                x=sector_data["Quarter"], y=sector_data["Vacancy_Count"],
                mode="lines", line=dict(color=BLUE, width=2),
                fill="tozeroy", fillcolor="rgba(37,99,235,0.08)",
                showlegend=False, hovertemplate="%{x}: %{y:,}<extra></extra>",
            ),
            row=1, col=i + 1,
        )
        fig.update_xaxes(showticklabels=False, row=1, col=i + 1)
    fig.update_layout(height=280)
    return style_fig(fig)


@app.callback(
    Output("company-export-download", "data"),
    Input("company-export-button", "n_clicks"),
    State("city-search", "value"),
    State("company-sector-filter", "value"),
    State("favourites-only-toggle", "value"),
    State("bookmarked-companies", "data"),
    prevent_initial_call=True,
)
def export_companies_csv(n_clicks, search_value, sector_value, favourites_only, bookmarked):
    # reusing the exact same filtering logic as the table itself, so the
    # exported CSV always matches what's actually on screen, not some
    # separate unfiltered dump
    results = sponsors_df
    if sector_value:
        results = results[results["Sector"] == sector_value]

    # this was missing the favourites-only/bookmark filter the table
    # itself supports - without it, exporting while filtered to
    # bookmarked companies would silently export the wrong, unfiltered set
    bookmarked_list = (bookmarked or {}).get("bookmarked", [])
    if favourites_only:
        results = results[results["Organisation"].isin(bookmarked_list)]

    if not search_value:
        results = results.sort_values("Sector", na_position="last").head(10)
    else:
        results = results[results["City"].str.contains(search_value, case=False, na=False)]
        results = results.sort_values("Active_Job_Count", ascending=False, na_position="last").head(50)

    return dcc.send_data_frame(results.to_csv, "sponsor_companies.csv", index=False)


# Client-side export for the Sectors chart - using Plotly's own built-in
# image download rather than rebuilding the chart server-side. This
# guarantees the exported image always matches exactly what's on screen
# (including the SARIMA forecast overlay and annotations), without
# duplicating or touching the existing update_sector_chart logic at all.
app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks) {
            const graphDiv = document.getElementById('sector-vacancy-chart').querySelector('.js-plotly-plot');
            Plotly.downloadImage(graphDiv, {format: 'png', filename: 'sector_vacancy_chart'});
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("sector-chart-export-download", "data"),
    Input("sector-chart-export-button", "n_clicks"),
    prevent_initial_call=True,
)





@app.callback(Output("salary-surface-chart", "figure"), Input("main-tabs", "value"))
def update_salary_surface(_):
    # Year x Sector x Median_Salary - a real 5x5 grid from the master
    # dataset, checked during the audit to confirm every cell is a real
    # observation, nothing interpolated to fill a gap
    years = sorted(master_df["Year"].unique())
    pivot = master_df.pivot_table(index="Sector", columns="Year", values="Median_Salary", aggfunc="first")
    pivot = pivot.reindex(SECTORS)

    fig = go.Figure(data=[go.Surface(
        z=pivot.values, x=years, y=SECTORS,
        colorscale=[[0, "#DBEAFE"], [1, BLUE]],
        hovertemplate="Year %{x}<br>%{y}<br>£%{z:,.0f}<extra></extra>",
    )])
    fig.update_layout(
        scene=dict(
            xaxis_title="Year", yaxis_title="", zaxis_title="Median salary (£)",
        ),
        margin=dict(l=0, r=0, t=10, b=0),
        height=500,
    )
    return style_fig(fig)

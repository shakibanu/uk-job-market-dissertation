"""
callbacks.py

This file contains all the callbacks used in the dashboard.

Each callback updates a different part of the dashboard when the user
interacts with it, such as changing tabs, selecting a sector or choosing
a different year.

I also use the style_fig() function here so every chart follows the same
design instead of repeating the styling in every callback.
"""

import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Input, Output, html

from app_instance import app
from data_loader import (
    master_df, sponsors_df, SECTORS, SALARY_THRESHOLDS,
    SURFACE, BORDER, TEXT, TEXT_SECONDARY, BLUE, TEAL, AMBER, DANGER,
)
from sarima_forecast import SARIMA_RESULTS
from tabs import overview_tab, sectors_tab, companies_tab, salary_tab


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
    )
    return fig


# Each callback updates a different part of the dashboard

@app.callback(Output("tab-content", "children"), Input("main-tabs", "value"))
def render_tab(tab):
    return {
        "tab-overview": overview_tab,
        "tab-sectors": sectors_tab,
        "tab-companies": companies_tab,
        "tab-salary": salary_tab,
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

    # Get the forecast values for the selected sector and continue the line
    # from the last actual data point.
    sarima_info = SARIMA_RESULTS[sector]
    future_quarters = sarima_info["future_quarters"]
    last_actual_quarter = filtered["Quarter"].iloc[-1]
    last_actual_vacancy_count = filtered["Vacancy_Count"].iloc[-1]

    # Start the forecast from the last actual value so the transition looks
    # continuous on the chart.
    forecast_dates = [last_actual_quarter] + future_quarters
    forecast_values = [last_actual_vacancy_count] + sarima_info["forecast"]
    forecast_ci95_lower = [last_actual_vacancy_count] + sarima_info["ci95_lower"]
    forecast_ci95_upper = [last_actual_vacancy_count] + sarima_info["ci95_upper"]
    forecast_ci80_lower = [last_actual_vacancy_count] + sarima_info["ci80_lower"]
    forecast_ci80_upper = [last_actual_vacancy_count] + sarima_info["ci80_upper"]

    # Add the wider 95% confidence interval around the forecast.
    fig.add_trace(go.Scatter(
        x=forecast_dates + forecast_dates[::-1], y=forecast_ci95_upper + forecast_ci95_lower[::-1],
        fill="toself", fillcolor="rgba(242,169,59,0.12)", line=dict(width=0),
        showlegend=False, hoverinfo="skip",
    ))
    # Add the 80% confidence interval inside the wider band.
    fig.add_trace(go.Scatter(
        x=forecast_dates + forecast_dates[::-1], y=forecast_ci80_upper + forecast_ci80_lower[::-1],
        fill="toself", fillcolor="rgba(242,169,59,0.22)", line=dict(width=0),
        showlegend=False, hoverinfo="skip",
    ))
    # Draw the forecast line on top of the confidence intervals.
    fig.add_trace(go.Scatter(
        x=forecast_dates, y=forecast_values, mode="lines+markers",
        line=dict(color=AMBER, width=2, dash="dash"),
        marker=dict(size=5, color=AMBER),
        name="Forecast (4Q)",
        hovertemplate="%{x}: %{y:,.0f} (forecast)<extra></extra>",
    ))

    # Marking the key policy events on the chart: Brexit, the vacancy peak,
    # and the two salary threshold rises
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


@app.callback(Output("sponsorship-comparison-chart", "figure"), Input("main-tabs", "value"))
def update_sponsorship_comparison(_):
    # one row per sector per year - visa grants are already annual, so drop
    # the quarterly duplicates before building the animation
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


@app.callback(Output("company-table-container", "children"), Input("city-search", "value"))
def update_company_table(search_value):
    # Show the first few companies when no city has been searched yet
    if not search_value:
        results = sponsors_df.head(10)
    # Search for companies that match the city entered by the user
    else:
        results = sponsors_df[sponsors_df["City"].str.contains(search_value, case=False, na=False)].head(50)

    if results.empty:
        return html.P(f"No sponsors found for '{search_value}'.", style={"color": TEXT_SECONDARY})

    return dbc.Table.from_dataframe(results, striped=True, bordered=False, hover=True, size="sm")


@app.callback(Output("salary-chart", "figure"), Input("salary-year-dropdown", "value"))
def update_salary_chart(year):
    # Get the salary data for the selected year
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
            textposition="outside",
            hovertemplate="%{x}: £%{y:,}<extra></extra>",
            name="Median salary",
        )
    )
    # Add the salary threshold as a reference line on the chart
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

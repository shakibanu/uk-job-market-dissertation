"""
dashboard_components.py

This file contains reusable components that are used in different parts
of the dashboard. Keeping them here avoids repeating the same code in
multiple files.
"""

from dash import html

def make_sparkline(values, colour):
    #Create a small sparkline chart for the KPI cards.
    #The values are scaled so the sparkline always fits inside the available space.
    vmin, vmax = min(values), max(values)
    rng = (vmax - vmin) or 1
    points = []
    # Convert each value into x and y coordinates for the SVG line.
    for i, v in enumerate(values):
        x = i * (120 / (len(values) - 1))
        y = 22 - ((v - vmin) / rng) * 20
        points.append(f"{x:.1f},{y:.1f}")
    points_str = " ".join(points)
    # Create the SVG using the calculated points.
    svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 24' "
        f"preserveAspectRatio='none'><polyline points='{points_str}' fill='none' "
        f"stroke='{colour}' stroke-width='1.5'/></svg>"
    )
    return html.Img(
        src="data:image/svg+xml;utf8," + svg,
        style={"width": "100%", "height": "24px", "marginTop": "10px", "display": "block"},
    )


def stat_card(label, value, colour, sparkline_values=None, trend_pct=None, trend_caption=None):
    
    #Create a KPI card with the main value and label.
    #A trend indicator and sparkline are added only if they are available.
    # Add the main content of the KPI card.
    children = [
        html.Div(className="stat-signal", style={"background": colour}),
        html.Div(value, className="stat-value"),
        html.Div(label, className="stat-label"),
    ]
    # Add the trend arrow and percentage when trend data is available.
    if trend_pct is not None:
        direction = "up" if trend_pct >= 0 else "down"
        arrow = "▲" if trend_pct >= 0 else "▼"
        children.append(
            html.Div(f"{arrow} {trend_pct:+.1f}%", className=f"stat-trend {direction}")
        )
        if trend_caption:
            children.append(html.Div(trend_caption, className="stat-caption"))
    # Add a sparkline to show the overall trend.
    if sparkline_values is not None:
        children.append(make_sparkline(sparkline_values, colour))
    return html.Div(children, className="stat-card")


def pct_change(series):
    
    #Calculate the percentage change between the first and last values.
    #This is used to display the trend on the KPI cards.
    
    # Convert the input into a list so it can be accessed easily.
    values = list(series)
    if len(values) < 2 or values[0] == 0:
        return 0.0
    return ((values[-1] - values[0]) / values[0]) * 100

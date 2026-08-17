"""
dashboard_components.py

This file contains reusable components used across the dashboard.

Keeping these components here avoids repeating the same code in
multiple files.
"""

from dash import html
import urllib.parse

# Store the Feather SVG icons used throughout the dashboard
ICONS = {
    "layout": '<rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/>',
    "bar-chart-2": '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
    "briefcase": '<rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>',
    "trending-up": '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>',
    "percent": '<line x1="19" y1="5" x2="5" y2="19"/><circle cx="6.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/>',
    "check": '<polyline points="20 6 9 17 4 12"/>',
    "map": '<polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/><line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/>',
    "file-text": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>',
    "book-open": '<path d="M2,4 H10 V20 L2,18 Z"/><path d="M22,4 H14 V20 L22,18 Z"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15 15 0 0 1 0 20a15 15 0 0 1 0-20"/>',
}


def feather_icon(name, size=18, colour="currentColor"):
    """
    Create a Feather icon with the selected size and colour.
    """
    inner = ICONS[name]
    svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' "
        f"stroke='{colour}' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>{inner}</svg>"
    )
    # URL-encoding the SVG before putting it in the data URI - without this,
    # a hex colour like #2563EB has its # read as a URL fragment marker,
    # which cuts off everything after it and breaks the image
    return html.Img(
        src="data:image/svg+xml;utf8," + urllib.parse.quote(svg),
        style={"width": f"{size}px", "height": f"{size}px", "display": "inline-block", "verticalAlign": "middle"},
    )


def make_sparkline(values, colour):
    """
    Create a small sparkline chart for the KPI cards.

    The values are scaled so the sparkline always fits inside the available
    space.
    """
    vmin, vmax = min(values), max(values)
    rng = (vmax - vmin) or 1
    points = []
    for i, v in enumerate(values):
        x = i * (120 / (len(values) - 1))
        y = 22 - ((v - vmin) / rng) * 20
        points.append(f"{x:.1f},{y:.1f}")
    points_str = " ".join(points)
    # Build the sparkline as an SVG image
    svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 24' "
        f"preserveAspectRatio='none'><polyline points='{points_str}' fill='none' "
        f"stroke='{colour}' stroke-width='1.5'/></svg>"
    )
    return html.Img(
        src="data:image/svg+xml;utf8," + urllib.parse.quote(svg),
        style={"width": "100%", "height": "24px", "marginTop": "10px", "display": "block"},
    )


def stat_card(label, value, colour, sparkline_values=None, trend_pct=None, trend_caption=None, icon=None):
    """
    Create a KPI card with the main value and label.

    A trend indicator, sparkline and icon are added when they are available.
    """
    if icon:
        label_row = html.Div(
            [feather_icon(icon, size=14, colour=colour), html.Div(label, className="stat-label")],
            style={"display": "flex", "alignItems": "center", "gap": "6px"},
        )
    else:
        label_row = html.Div(label, className="stat-label")

    # Add the main content of the KPI card
    children = [
        html.Div(className="stat-signal", style={"background": colour}),
        html.Div(value, className="stat-value"),
        label_row,
    ]
    # Add the trend information when it is available
    if trend_pct is not None:
        direction = "up" if trend_pct >= 0 else "down"
        arrow = "▲" if trend_pct >= 0 else "▼"
        children.append(
            html.Div(f"{arrow} {trend_pct:+.1f}%", className=f"stat-trend {direction}")
        )
        if trend_caption:
            children.append(html.Div(trend_caption, className="stat-caption"))
    # Add a sparkline to show the overall trend
    if sparkline_values is not None:
        children.append(make_sparkline(sparkline_values, colour))
    return html.Div(children, className="stat-card")


def pct_change(series):
    """
    Calculate the percentage change between the first and last values.

    This is used to display the trend on the KPI cards.
    """
    values = list(series)
    if len(values) < 2 or values[0] == 0:
        return 0.0
    return ((values[-1] - values[0]) / values[0]) * 100

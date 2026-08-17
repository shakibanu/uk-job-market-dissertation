"""
app.py

This is the main file for my dissertation project: Navigating the UK
Job Market (2021-2026). It's built with Plotly Dash and has four tabs:
Overview, Sectors, Companies and Salary.

I've split the project into a few files instead of putting everything in
one place:

This file sets the overall page layout (the header and tab bar), brings
in the tabs and callbacks, and runs the server. This is the file to run:
python app.py

Styling is kept in assets/style.css, which Dash loads automatically.

Shakira Banu Shaffi - 19377581
"""

from dash import dcc, html
from app_instance import app, server
from dashboard_components import feather_icon
import narrative_routes  # noqa: F401 - registers the /story route on the same server


def tab_label(text, icon_name):
    # A tab label with a small icon next to the text
    # Combine the icon and text into a single tab label
    return html.Div(
        [feather_icon(icon_name, size=14), html.Span(text)],
        style={"display": "flex", "alignItems": "center", "gap": "6px"},
    )


# Create the main dashboard layout with the header, navigation tabs
# and the area where the selected tab will be displayed.
app.layout = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        html.P("UK Job Market Platform", className="app-title"),
                        html.P("Sponsorship and salary intelligence · 2021-2026", className="app-subtitle"),
                    ]
                ),
                # Link to the scrollytelling narrative - a real page (not a
                # Dash tab) since it's served as its own route on the same
                # server, so this is a normal link rather than a tab switch
                html.A(
                    [feather_icon("book-open", size=14), html.Span("The Story")],
                    href="/story",
                    className="story-link",
                    style={"display": "flex", "alignItems": "center", "gap": "6px"},
                ),
                dcc.Tabs(
                    id="main-tabs",
                    value="tab-overview",
                    className="custom-tabs",
                    children=[
                        dcc.Tab(label=tab_label("Overview", "layout"), value="tab-overview", className="tab", selected_className="tab--selected"),
                        dcc.Tab(label=tab_label("Sectors", "bar-chart-2"), value="tab-sectors", className="tab", selected_className="tab--selected"),
                        dcc.Tab(label=tab_label("Companies", "briefcase"), value="tab-companies", className="tab", selected_className="tab--selected"),
                        dcc.Tab(label=tab_label("Salary", "trending-up"), value="tab-salary", className="tab", selected_className="tab--selected"),
                        dcc.Tab(label=tab_label("Regional", "map"), value="tab-regional", className="tab", selected_className="tab--selected"),
                        dcc.Tab(label=tab_label("Is the UK Worth It", "percent"), value="tab-roi", className="tab", selected_className="tab--selected"),
                        dcc.Tab(label=tab_label("Sponsorship Fit", "check"), value="tab-fit", className="tab", selected_className="tab--selected"),
                        dcc.Tab(label=tab_label("Nationality", "globe"), value="tab-nationality", className="tab", selected_className="tab--selected"),
                        dcc.Tab(label=tab_label("Sources", "file-text"), value="tab-sources", className="tab", selected_className="tab--selected"),
                    ],
                ),
            ],
            className="app-header",
        ),
        # This container displays the content for the selected tab
        html.Div(id="tab-content"),
    ]
)

# Load the callbacks after creating the layout so they can use the
# component IDs defined above
import callbacks  # noqa: E402, F401

if __name__ == "__main__":
    app.run(debug=True, port=8050)

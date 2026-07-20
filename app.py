"""
app.py

This is the main file for my dashboard.

It creates the overall page layout, loads the tabs, registers the
callbacks and starts the Dash application.

The project is split into separate files to keep the code organised
and easier to manage.

Run this file to start the dashboard.

Shakira Banu Shaffi - 19377581
"""

from dash import dcc, html
from app_instance import app

# This is the main layout for the dashboard. It includes the page header,
# the navigation tabs and an empty content area where the selected tab will be displayed
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
                dcc.Tabs(
                    id="main-tabs",
                    value="tab-overview",
                    className="custom-tabs",
                    children=[
                        dcc.Tab(label="Overview", value="tab-overview", className="tab", selected_className="tab--selected"),
                        dcc.Tab(label="Sectors", value="tab-sectors", className="tab", selected_className="tab--selected"),
                        dcc.Tab(label="Companies", value="tab-companies", className="tab", selected_className="tab--selected"),
                        dcc.Tab(label="Salary", value="tab-salary", className="tab", selected_className="tab--selected"),
                    ],
                ),
            ],
            className="app-header",
        ),
        html.Div(id="tab-content"),
    ]
)

# Import the callbacks after creating the layout because the callbacks
# need to use the component IDs that are defined above
import callbacks  # noqa: E402, F401

if __name__ == "__main__":
    app.run(debug=True, port=8050)


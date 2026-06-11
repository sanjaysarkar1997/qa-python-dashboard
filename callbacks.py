"""
callbacks.py
============
Contains all Dash callback functions for the QA Analytics Dashboard.

What is a callback?
-------------------
A Dash callback is a Python function that runs automatically when a
user interacts with the dashboard (e.g. changes a date, clicks a button).
Each callback is linked to:
  • `Input`  — a component that triggers the update
  • `Output` — a component whose value/content gets replaced
  • `State`  — a component whose value is read but doesn't trigger (not used here)

Callbacks defined here:
  1. `update_dashboard` — main callback; updates all charts and KPI cards
                          whenever dates, status filter, or refresh fires
  2. `show_table`       — shows a data table when any of the 3 buttons is clicked

Usage:
    from callbacks import register
    register(app)
"""

import pandas as pd

from dash import Input, Output, callback_context, dash_table
from dash import html

from data_loader import load_all_reports
from charts import (
    build_kpi_cards,
    build_pie_chart,
    build_duration_chart,
    build_failed_chart,
    build_timeseries_chart,
    build_monitor_chart,
    build_failure_root_chart,
)
from config import (
    TABLE_PAGE_SIZE,
    FONT_FAMILY,
)


# ------------------------------------------------------------------
# TABLE STYLE DEFINITIONS
# ------------------------------------------------------------------
# These control how the DataTable looks.  Kept here so they can
# be easily adjusted without hunting through the callback logic.

TABLE_HEADER_STYLE = {
    "backgroundColor": "#1e3799",
    "color":           "white",
    "fontWeight":      "700",
    "textAlign":       "center",
    "fontFamily":      FONT_FAMILY,
    "fontSize":        "13px",
    "padding":         "12px 8px",
    "letterSpacing":   "0.5px",
}

TABLE_CELL_STYLE = {
    "textAlign":  "center",
    "padding":    "10px 8px",
    "fontFamily": FONT_FAMILY,
    "fontSize":   "12px",
    "minWidth":   "120px",
    "color":      "#2d3436",
}

TABLE_CONTAINER_STYLE = {
    "overflowX":       "auto",
    "maxHeight":       "560px",
    "overflowY":       "auto",
    "backgroundColor": "white",
    "borderRadius":    "12px",
    "boxShadow":       "0 2px 12px rgba(0,0,0,0.07)",
}

# Alternating row colours for readability (conditional formatting)
TABLE_STRIPE_STYLES = [
    {
        "if": {"row_index": "odd"},
        "backgroundColor": "#f8f9fa",
    },
    {
        "if": {"state": "active"},
        "backgroundColor": "#dfe6e9",
        "border":          "1px solid #b2bec3",
    },
]


def register(app) -> None:
    """
    Register all callbacks onto the Dash app instance.

    Call this function once from `app.py` after `app.layout` is set.

    Parameters
    ----------
    app : dash.Dash
        The Dash application object.
    """

    # ==============================================================
    # CALLBACK 1 — Main Dashboard Update
    # ==============================================================
    @app.callback(
        [
            Output("kpi_cards",          "children"),
            Output("pie_chart",          "figure"),
            Output("duration_chart",     "figure"),
            Output("failed_chart",       "figure"),
            Output("timeseries_chart",   "figure"),
            Output("monitor_chart",      "figure"),
            Output("failure_root_chart", "figure"),
        ],
        [
            Input("start_date",    "date"),
            Input("end_date",      "date"),
            Input("refresh_timer", "n_intervals"),
        ],
    )
    def update_dashboard(start_date, end_date, _refresh):
        """
        Reload data and rebuild all charts whenever:
          - The user selects a new date range
          - The auto-refresh timer fires (every 60 seconds)

        This means the dashboard always shows up-to-date data without
        the user having to restart the app manually.

        Parameters
        ----------
        start_date : str | None
            ISO date string from the start date picker (e.g. "2026-06-08")
        end_date : str | None
            ISO date string from the end date picker
        _refresh : int
            Number of times the auto-refresh interval has fired
            (we don't use the value — it just triggers the callback)

        Returns
        -------
        tuple
            Seven items matching the Outputs above, in the same order.
        """
        # Step 1: Reload CSVs (picks up any changes since last refresh)
        df = load_all_reports()

        # Step 2: Apply date range filter
        if start_date and end_date:
            start = pd.to_datetime(start_date).date()
            end   = pd.to_datetime(end_date).date()
            df = df[(df["DATE"] >= start) & (df["DATE"] <= end)]

        # Step 4: Build each component from the filtered data
        kpi     = build_kpi_cards(df)
        pie     = build_pie_chart(df)
        dur     = build_duration_chart(df)
        failed  = build_failed_chart(df)
        ts      = build_timeseries_chart(df)
        monitor = build_monitor_chart(df)
        root    = build_failure_root_chart(df)

        return kpi, pie, dur, failed, ts, monitor, root


    # ==============================================================
    # CALLBACK 2 — Table Button Toggle
    # ==============================================================
    @app.callback(
        Output("dynamic_table", "children"),
        [
            Input("btn_new",     "n_clicks"),
            Input("btn_updated", "n_clicks"),
            Input("btn_full",    "n_clicks"),
        ],
    )
    def show_table(new_clicks, updated_clicks, full_clicks):
        """
        Show a data table when the user clicks one of the three buttons.

        Dash's `callback_context` tells us *which* button was clicked
        most recently, so we can show the right table.

        Button mapping:
          • btn_new     → NEW TESTS    (columns: Date, Test ID, Name, Status, Duration)
          • btn_updated → UPDATED TESTS (columns: Date, Updated At, Test ID, Name, Status)
          • btn_full    → FULL DATASET  (all columns, all rows)

        Parameters
        ----------
        new_clicks, updated_clicks, full_clicks : int
            Click counts for each button (Dash passes these automatically)

        Returns
        -------
        dash.dash_table.DataTable | str
            A DataTable component, or an empty string if no button has
            been clicked yet (initial load).
        """
        ctx = callback_context

        # On initial load, no button has been clicked — hide the table
        if not ctx.triggered:
            return ""

        # Identify which button was clicked
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # Reload the latest data
        df = load_all_reports()

        # Select the right columns based on which button was clicked
        if button_id == "btn_new":
            # Show basic new test info
            cols = ["DATE", "TEST ID", "TEST NAME", "STATUS", "DURATION (S)"]
            # Only keep columns that actually exist (some CSVs may differ)
            cols = [c for c in cols if c in df.columns]
            table_df = df[cols]
            title = "🆕 New Tests"

        elif button_id == "btn_updated":
            # Show tests that have an UPDATED AT timestamp
            table_df = df[df["UPDATED AT"].notna()]
            cols = ["DATE", "UPDATED AT", "TEST ID", "TEST NAME", "STATUS"]
            cols = [c for c in cols if c in table_df.columns]
            table_df = table_df[cols]
            title = "✏️ Updated Tests"

        else:
            # Full dataset — all columns
            table_df = df.copy()
            title = "📋 Full Dataset"

        # Convert datetime columns to readable strings for display
        for col in ["DATE", "UPDATED AT", "UPDATED DATE", "CREATED AT"]:
            if col in table_df.columns:
                table_df[col] = table_df[col].astype(str)

        return html.Div(
            [
                # Table title
                html.Div(
                    title,
                    style={
                        "fontWeight":    "700",
                        "fontSize":      "15px",
                        "marginBottom":  "12px",
                        "fontFamily":    FONT_FAMILY,
                        "color":         "#2d3436",
                        "paddingLeft":   "4px",
                    },
                ),
                # The interactive DataTable
                dash_table.DataTable(
                    columns=[{"name": col, "id": col} for col in table_df.columns],
                    data=table_df.to_dict("records"),
                    page_size=TABLE_PAGE_SIZE,
                    filter_action="native",    # Users can type to filter rows
                    sort_action="native",      # Users can click headers to sort
                    style_table=TABLE_CONTAINER_STYLE,
                    style_header=TABLE_HEADER_STYLE,
                    style_cell=TABLE_CELL_STYLE,
                    style_data_conditional=TABLE_STRIPE_STYLES,
                ),
            ],
            style={
                "backgroundColor": "white",
                "borderRadius":    "14px",
                "boxShadow":       "0 2px 12px rgba(0,0,0,0.07)",
                "padding":         "20px",
            },
        )

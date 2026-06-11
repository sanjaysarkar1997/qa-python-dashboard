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
            Input("selected_date", "date"),
            Input("refresh_timer", "n_intervals"),
        ],
    )
    def update_dashboard(selected_date, _refresh):
        """
        Reload data and rebuild all charts whenever:
          - The user selects a new date
          - The auto-refresh timer fires (every 60 seconds)

        Parameters
        ----------
        selected_date : str | None
            ISO date string from the date picker (e.g. "2026-06-11")
        _refresh : int
            Number of times the auto-refresh interval has fired

        Returns
        -------
        tuple
            Seven items matching the Outputs above, in the same order.
        """
        # Step 1: Reload CSVs (picks up any changes since last refresh)
        df = load_all_reports()

        if not selected_date:
            selected_date = str(df["DATE"].dropna().max())

        selected_date_obj = pd.to_datetime(selected_date).date()

        # Step 2: Apply single date filter for general metrics/charts
        df_single = df[df["DATE"] == selected_date_obj]

        # Step 3: Apply filter for selected and last 10 days (total 11 days leading to selected_date)
        start_date_obj = selected_date_obj - pd.Timedelta(days=10)
        df_trend = df[(df["DATE"] >= start_date_obj) & (df["DATE"] <= selected_date_obj)]

        # Step 4: Build each component
        kpi     = build_kpi_cards(df_single)
        pie     = build_pie_chart(df_single)
        dur     = build_duration_chart(df_single)
        failed  = build_failed_chart(df_trend)
        ts      = build_timeseries_chart(df_trend)
        monitor = build_monitor_chart(df_single)
        root    = build_failure_root_chart(df_single)

        return kpi, pie, dur, failed, ts, monitor, root


    # ==============================================================
    # CALLBACK 2 — Update Active Table Type
    # ==============================================================
    @app.callback(
        Output("active_table_type", "data"),
        [
            Input("btn_new",     "n_clicks"),
            Input("btn_updated", "n_clicks"),
            Input("btn_full",    "n_clicks"),
        ],
        prevent_initial_call=True
    )
    def update_active_table(new_clicks, updated_clicks, full_clicks):
        """
        Track which button was clicked and update the active_table_type store.
        """
        ctx = callback_context
        if not ctx.triggered:
            return ""
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        return button_id


    # ==============================================================
    # CALLBACK 3 — Table Rendering
    # ==============================================================
    @app.callback(
        Output("dynamic_table", "children"),
        [
            Input("active_table_type", "data"),
            Input("selected_date", "date"),
            Input("refresh_timer", "n_intervals"),
        ],
    )
    def show_table(active_table, selected_date, _refresh):
        """
        Show/update the data table based on the active table type and selected date.

        Parameters
        ----------
        active_table : str
            The active table component ID (btn_new, btn_updated, btn_full) from dcc.Store
        selected_date : str | None
            ISO date string from the date picker
        _refresh : int
            Auto-refresh trigger

        Returns
        -------
        dash.html.Div | str
            A styled container with the DataTable, or empty string.
        """
        if not active_table:
            return ""

        # Reload the latest data
        df = load_all_reports()

        if not selected_date:
            selected_date = str(df["DATE"].dropna().max())
        selected_date_obj = pd.to_datetime(selected_date).date()

        # Filter the dataset for the selected date
        df_filtered = df[df["DATE"] == selected_date_obj]

        # Select the right columns based on which button was clicked
        if active_table == "btn_new":
            cols = ["DATE", "TEST ID", "TEST NAME", "STATUS", "DURATION (S)"]
            cols = [c for c in cols if c in df_filtered.columns]
            table_df = df_filtered[cols]
            title = f"🆕 New Tests (Selected Date: {selected_date_obj})"

        elif active_table == "btn_updated":
            # Show tests that have an UPDATED AT timestamp on selected date
            table_df = df_filtered[df_filtered["UPDATED AT"].notna()]
            cols = ["DATE", "UPDATED AT", "TEST ID", "TEST NAME", "STATUS"]
            cols = [c for c in cols if c in table_df.columns]
            table_df = table_df[cols]
            title = f"✏️ Updated Tests (Selected Date: {selected_date_obj})"

        else:
            table_df = df_filtered.copy()
            title = f"📋 Full Dataset (Selected Date: {selected_date_obj})"

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
                    filter_action="native",
                    sort_action="native",
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

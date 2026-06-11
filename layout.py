"""
layout.py
=========
Defines the full Dash HTML layout for the QA Analytics Dashboard.

Why a separate file?
--------------------
The layout is purely about *structure* — which components appear,
in what order, and what they look like.  Keeping it here means you
can redesign the page without touching any data or callback logic.

The `create_layout()` function is called once from `app.py` when the
server starts up.  It returns the top-level `html.Div` that Dash uses
as the page root.

Usage:
    from layout import create_layout
    app.layout = create_layout(df)
"""

import pandas as pd

from dash import dcc, html, dash_table

from config import (
    TABLE_PAGE_SIZE,
    STATUS_COLORS,
    FONT_FAMILY,
)


# ------------------------------------------------------------------
# SHARED STYLE TOKENS
# ------------------------------------------------------------------
# Define reusable style dictionaries here so the layout stays DRY
# (Don't Repeat Yourself).  Change a value once and it updates everywhere.

PAGE_BG = "linear-gradient(135deg, #f0f4ff 0%, #e8eef9 100%)"
CARD_BG = "white"
CARD_RADIUS = "16px"
CARD_SHADOW = "0 2px 12px rgba(0,0,0,0.07)"
CARD_PADDING = "16px"
SECTION_GAP = "16px"

CARD_STYLE = {
    "backgroundColor": CARD_BG,
    "borderRadius": CARD_RADIUS,
    "boxShadow": CARD_SHADOW,
    "padding": CARD_PADDING,
}

HALF_CARD_STYLE = {
    **CARD_STYLE,
    "width": "49%",
}

FULL_CARD_STYLE = {
    **CARD_STYLE,
    "width": "100%",
}

ROW_STYLE = {
    "display": "flex",
    "justifyContent": "space-between",
    "gap": SECTION_GAP,
    "marginBottom": SECTION_GAP,
}


# ------------------------------------------------------------------
# HELPER — Section header
# ------------------------------------------------------------------


def _section_header(title: str) -> html.Div:
    """
    Render a small uppercase section label above a chart group.

    Parameters
    ----------
    title : str
        Label text to display.

    Returns
    -------
    dash.html.Div
    """
    return html.Div(
        title.upper(),
        style={
            "fontSize": "11px",
            "fontWeight": "700",
            "letterSpacing": "2px",
            "color": "#a0aec0",
            "marginBottom": "8px",
            "paddingLeft": "4px",
            "fontFamily": FONT_FAMILY,
        },
    )


# ------------------------------------------------------------------
# HELPER — Action button
# ------------------------------------------------------------------


def _action_button(label: str, btn_id: str, color: str) -> html.Button:
    """
    Render a styled pill-shaped action button.

    Parameters
    ----------
    label : str
        Button text.
    btn_id : str
        Dash component ID.
    color : str
        Hex background color.

    Returns
    -------
    dash.html.Button
    """
    return html.Button(
        label,
        id=btn_id,
        n_clicks=0,
        style={
            "backgroundColor": color,
            "color": "white",
            "border": "none",
            "padding": "12px 24px",
            "borderRadius": "50px",
            "cursor": "pointer",
            "fontWeight": "600",
            "fontSize": "13px",
            "letterSpacing": "0.5px",
            "fontFamily": FONT_FAMILY,
            "boxShadow": f"0 4px 14px {color}55",
            "transition": "opacity 0.2s ease, transform 0.15s ease",
        },
    )


# ------------------------------------------------------------------
# MAIN LAYOUT FUNCTION
# ------------------------------------------------------------------


def create_layout(df: pd.DataFrame) -> html.Div:
    """
    Build and return the entire Dash page layout.

    The layout is divided into sections:
      1. Hero header with title and subtitle
      2. Filter bar (date range + status dropdown)
      3. KPI cards placeholder (filled by callback)
      4. Row 1 charts — Status Distribution + Duration Analysis
      5. Row 2 charts — Failed Tests + Daily Trend
      6. Row 3 charts — Monitor Priority + Root Cause (side by side)
      7. Table action buttons
      8. Dynamic table placeholder (filled by callback)

    Parameters
    ----------
    df : pd.DataFrame
        The initial loaded DataFrame — used to set date picker defaults.

    Returns
    -------
    dash.html.Div
        Root layout element passed to `app.layout`.
    """

    # Calculate default date range from the loaded data
    min_date = str(df["DATE"].dropna().min())
    max_date = str(df["DATE"].dropna().max())

    return html.Div(
        [
            dcc.Store(id="active_table_type", data=""),
            # ----------------------------------------------------------
            # SECTION 1 — HERO HEADER
            # ----------------------------------------------------------
            html.Div(
                [
                    html.H1(
                        "QA Analytics Dashboard",
                        style={
                            "margin": "0 0 6px 0",
                            "fontSize": "28px",
                            "fontWeight": "800",
                            "background": "linear-gradient(90deg, #1e3799, #0984e3)",
                            "WebkitBackgroundClip": "text",
                            "WebkitTextFillColor": "transparent",
                            "fontFamily": FONT_FAMILY,
                        },
                    ),
                    html.P(
                        "Test execution analytics",
                        style={
                            "margin": "0",
                            "fontSize": "13px",
                            "color": "#636e72",
                            "fontFamily": FONT_FAMILY,
                        },
                    ),
                ],
                style={
                    "background": "white",
                    "borderRadius": CARD_RADIUS,
                    "boxShadow": CARD_SHADOW,
                    "padding": "24px 28px",
                    "marginBottom": SECTION_GAP,
                    "borderLeft": "5px solid #0984e3",
                },
            ),
            # ----------------------------------------------------------
            # SECTION 2 — FILTER BAR
            # ----------------------------------------------------------
            html.Div(
                [
                    # Date Selection
                    html.Div(
                        [
                            html.Label(
                                "SELECT DATE",
                                style={
                                    "fontSize": "11px",
                                    "fontWeight": "700",
                                    "letterSpacing": "1.5px",
                                    "color": "#636e72",
                                    "marginBottom": "8px",
                                    "display": "block",
                                    "fontFamily": FONT_FAMILY,
                                },
                            ),
                            dcc.DatePickerSingle(
                                id="selected_date",
                                date=max_date,
                                display_format="DD MMM YYYY",
                                style={"width": "100%"},
                            ),
                        ],
                        style={"flex": "1"},
                    ),
                ],
                style={
                    **CARD_STYLE,
                    "display": "flex",
                    "gap": "20px",
                    "alignItems": "flex-end",
                    "marginBottom": SECTION_GAP,
                    "flexWrap": "wrap",
                },
            ),
            # ----------------------------------------------------------
            # SECTION 3 — KPI CARDS (filled by callback)
            # ----------------------------------------------------------
            # ----------------------------------------------------------
            # ----------------------------------------------------------
            # SECTION 3 — KPI CARDS (wrapped in Loading)
            # ----------------------------------------------------------
            dcc.Loading(
                id="loading-kpis",
                type="circle",
                color="#0984e3",
                children=html.Div(id="kpi_cards", style={"marginBottom": SECTION_GAP}),
            ),
            # ----------------------------------------------------------
            # SECTION 4 — ROW 1: Status Distribution + Duration
            # ----------------------------------------------------------
            _section_header("Overview"),
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Loading(
                                id="loading-pie",
                                type="circle",
                                color="#0984e3",
                                children=dcc.Graph(id="pie_chart"),
                            )
                        ],
                        style=HALF_CARD_STYLE,
                    ),
                    html.Div(
                        [
                            dcc.Loading(
                                id="loading-duration",
                                type="circle",
                                color="#0984e3",
                                children=dcc.Graph(id="duration_chart"),
                            )
                        ],
                        style=HALF_CARD_STYLE,
                    ),
                ],
                style=ROW_STYLE,
            ),
            # ----------------------------------------------------------
            # SECTION 5 — ROW 2: Failed Tests + Daily Trend
            # ----------------------------------------------------------
            _section_header("Failure & Trend Analysis"),
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Loading(
                                id="loading-failed",
                                type="circle",
                                color="#0984e3",
                                children=dcc.Graph(id="failed_chart"),
                            )
                        ],
                        style=HALF_CARD_STYLE,
                    ),
                    html.Div(
                        [
                            dcc.Loading(
                                id="loading-timeseries",
                                type="circle",
                                color="#0984e3",
                                children=dcc.Graph(id="timeseries_chart"),
                            )
                        ],
                        style=HALF_CARD_STYLE,
                    ),
                ],
                style=ROW_STYLE,
            ),
            # ----------------------------------------------------------
            # SECTION 6 — MONITOR PRIORITY + ROOT CAUSE (side by side)
            # ----------------------------------------------------------
            _section_header("Monitor Priority & Root Cause"),
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Loading(
                                id="loading-monitor",
                                type="circle",
                                color="#0984e3",
                                children=dcc.Graph(id="monitor_chart"),
                            )
                        ],
                        style=HALF_CARD_STYLE,
                    ),
                    html.Div(
                        [
                            dcc.Loading(
                                id="loading-failure-root",
                                type="circle",
                                color="#0984e3",
                                children=dcc.Graph(id="failure_root_chart"),
                            )
                        ],
                        style=HALF_CARD_STYLE,
                    ),
                ],
                style=ROW_STYLE,
            ),
            # ----------------------------------------------------------
            # SECTION 7 — ENVIRONMENT BREAKDOWN
            # ----------------------------------------------------------
            _section_header("Environment Breakdown"),
            html.Div(
                id="environment_breakdown_container",
                style={"marginBottom": SECTION_GAP},
            ),
            # ----------------------------------------------------------
            # SECTION 8 — MODULE / SQUAD BREAKDOWN
            # ----------------------------------------------------------
            _section_header("Module / Squad Breakdown"),
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Loading(
                                id="loading-module-breakdown",
                                type="circle",
                                color="#0984e3",
                                children=dcc.Graph(id="module_breakdown_chart"),
                            )
                        ],
                        style=FULL_CARD_STYLE,
                    )
                ],
                style=ROW_STYLE,
            ),
            # ----------------------------------------------------------
            # SECTION 9 — ACTION BUTTONS
            # ----------------------------------------------------------
            html.Div(
                [
                    _action_button("🆕  View New Tests", "btn_new", "#00b894"),
                    _action_button("✏️  View Updated Tests", "btn_updated", "#e17055"),
                    _action_button("❌  View Failed Tests", "btn_failed", "#d63031"),
                    _action_button("📋  Full Dataset", "btn_full", "#0984e3"),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "center",
                    "gap": "14px",
                    "marginBottom": SECTION_GAP,
                    "flexWrap": "wrap",
                },
            ),
            # ----------------------------------------------------------
            # DYNAMIC TABLE (filled by callback, wrapped in Loading)
            # ----------------------------------------------------------
            dcc.Loading(
                id="loading-table",
                type="circle",
                color="#0984e3",
                children=html.Div(id="dynamic_table"),
            ),
        ],
        style={
            "background": PAGE_BG,
            "minHeight": "100vh",
            "padding": "16px",
            "margin": "0px",
            "fontFamily": FONT_FAMILY,
            "boxSizing": "border-box",
        },
    )

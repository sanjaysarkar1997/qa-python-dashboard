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
from datetime import date

from dash import dcc, html, dash_table

from config import (
    TABLE_PAGE_SIZE,
    STATUS_COLORS,
    FONT_FAMILY,
    RUN_TEST_SERVER_URL,
    ALLURE_REPORT_URL,
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

    # Default date is today's date
    default_date = str(date.today())

    return html.Div(
        [
            dcc.Store(id="active_table_type", data=""),
            dcc.Store(id="flowchart_test_id", data=""),

            # ----------------------------------------------------------
            # FLOWCHART MODAL OVERLAY (hidden by default)
            # ----------------------------------------------------------
            html.Div(
                [
                    # Semi-transparent backdrop
                    html.Div(
                        id="flowchart_backdrop",
                        style={
                            "position": "fixed",
                            "top": "0",
                            "left": "0",
                            "width": "100vw",
                            "height": "100vh",
                            "backgroundColor": "rgba(15,23,42,0.65)",
                            "backdropFilter": "blur(4px)",
                            "zIndex": "9998",
                        },
                        n_clicks=0,
                    ),
                    # Modal card
                    html.Div(
                        [
                            # Modal header
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Span(
                                                "📊",
                                                style={"fontSize": "22px", "marginRight": "10px"},
                                            ),
                                            html.Span(
                                                id="flowchart_modal_title",
                                                style={
                                                    "fontFamily": FONT_FAMILY,
                                                    "fontWeight": "700",
                                                    "fontSize": "16px",
                                                    "color": "#1e293b",
                                                },
                                            ),
                                        ],
                                        style={"display": "flex", "alignItems": "center"},
                                    ),
                                    html.Button(
                                        "✕",
                                        id="flowchart_close_btn",
                                        n_clicks=0,
                                        style={
                                            "background": "none",
                                            "border": "none",
                                            "fontSize": "20px",
                                            "cursor": "pointer",
                                            "color": "#64748b",
                                            "padding": "4px 8px",
                                            "borderRadius": "6px",
                                            "lineHeight": "1",
                                        },
                                    ),
                                ],
                                style={
                                    "display": "flex",
                                    "justifyContent": "space-between",
                                    "alignItems": "center",
                                    "borderBottom": "1px solid #e2e8f0",
                                    "paddingBottom": "14px",
                                    "marginBottom": "20px",
                                },
                            ),
                            # Sub-type + description row
                            html.Div(
                                id="flowchart_modal_meta",
                                style={"marginBottom": "18px"},
                            ),
                            # Flowchart body
                            html.Div(
                                id="flowchart_modal_body",
                                style={
                                    "overflowY": "auto",
                                    "maxHeight": "60vh",
                                    "paddingRight": "4px",
                                },
                            ),
                        ],
                        style={
                            "position": "fixed",
                            "top": "50%",
                            "left": "50%",
                            "transform": "translate(-50%, -50%)",
                            "backgroundColor": "white",
                            "borderRadius": "20px",
                            "boxShadow": "0 25px 60px rgba(0,0,0,0.25)",
                            "padding": "28px 32px",
                            "zIndex": "9999",
                            "width": "min(90vw, 760px)",
                            "fontFamily": FONT_FAMILY,
                        },
                    ),
                ],
                id="flowchart_modal_overlay",
                style={"display": "none"},  # hidden until triggered
            ),

            # ----------------------------------------------------------
            html.Div(
                [
                    # Left: title + subtitle
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
                                "Test execution analytics — powered by Playwright & Allure",
                                style={
                                    "margin": "0",
                                    "fontSize": "13px",
                                    "color": "#636e72",
                                    "fontFamily": FONT_FAMILY,
                                },
                            ),
                        ],
                        style={"flex": "1"},
                    ),
                    # Right: quick links to the run-test-server
                    html.Div(
                        [
                            html.A(
                                "🧪  Run Tests",
                                href=RUN_TEST_SERVER_URL,
                                target="_blank",
                                rel="noopener noreferrer",
                                style={
                                    "display": "inline-flex",
                                    "alignItems": "center",
                                    "gap": "6px",
                                    "padding": "9px 20px",
                                    "background": "linear-gradient(135deg, #0984e3 0%, #1e3799 100%)",
                                    "color": "white",
                                    "borderRadius": "50px",
                                    "textDecoration": "none",
                                    "fontFamily": FONT_FAMILY,
                                    "fontWeight": "600",
                                    "fontSize": "13px",
                                    "boxShadow": "0 4px 14px rgba(9,132,227,0.35)",
                                    "transition": "opacity 0.2s",
                                    "marginRight": "10px",
                                },
                            ),
                            html.A(
                                "📄  Allure Report",
                                href=ALLURE_REPORT_URL,
                                target="_blank",
                                rel="noopener noreferrer",
                                style={
                                    "display": "inline-flex",
                                    "alignItems": "center",
                                    "gap": "6px",
                                    "padding": "9px 20px",
                                    "background": "linear-gradient(135deg, #00b894 0%, #00cec9 100%)",
                                    "color": "white",
                                    "borderRadius": "50px",
                                    "textDecoration": "none",
                                    "fontFamily": FONT_FAMILY,
                                    "fontWeight": "600",
                                    "fontSize": "13px",
                                    "boxShadow": "0 4px 14px rgba(0,184,148,0.35)",
                                    "transition": "opacity 0.2s",
                                },
                            ),
                        ],
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "flexShrink": "0",
                        },
                    ),
                ],
                style={
                    "background": "white",
                    "borderRadius": CARD_RADIUS,
                    "boxShadow": CARD_SHADOW,
                    "padding": "20px 28px",
                    "marginBottom": SECTION_GAP,
                    "borderLeft": "5px solid #0984e3",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "space-between",
                    "gap": "16px",
                    "flexWrap": "wrap",
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
                                date=default_date,
                                display_format="DD MMM YYYY",
                                style={"width": "100%"},
                            ),
                        ],
                        style={"flex": "1", "minWidth": "200px"},
                    ),
                    # Target Environment Selection
                    html.Div(
                        [
                            html.Label(
                                "TARGET ENVIRONMENT",
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
                            dcc.Dropdown(
                                id="target_env",
                                options=[
                                    {"label": "Dev / Local", "value": "dev"},
                                    {"label": "Quality (QA)", "value": "quality"},
                                    {"label": "Production", "value": "production"},
                                ],
                                value="dev",
                                clearable=False,
                                style={"width": "100%", "fontFamily": FONT_FAMILY},
                            ),
                        ],
                        style={"flex": "1", "minWidth": "200px"},
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
            # SECTION 9 — TOP FAILING ENDPOINTS
            # ----------------------------------------------------------
            _section_header("Top Failing Endpoints"),
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Loading(
                                id="loading-failed-endpoint",
                                type="circle",
                                color="#0984e3",
                                children=dcc.Graph(id="failed_endpoint_chart"),
                            )
                        ],
                        style=FULL_CARD_STYLE,
                    )
                ],
                style=ROW_STYLE,
            ),
            # ----------------------------------------------------------
            # SECTION 10 — FAILED LIFECYCLE STEPS
            # ----------------------------------------------------------
            _section_header("Failed Lifecycle Steps (Cross-Data-Flow)"),
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Loading(
                                id="loading-failed-step",
                                type="circle",
                                color="#0984e3",
                                children=dcc.Graph(id="failed_step_chart"),
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
                    _action_button("🔄  Cross-Data-Flow", "btn_crossflow", "#6c5ce7"),
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

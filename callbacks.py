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
  • `State`  — a component whose value is read but doesn't trigger

Callbacks defined here:
  1. `update_dashboard`       — main callback; updates all charts and KPI cards
  2. `update_active_table`    — tracks which table button was clicked
  3. `show_table`             — renders the data table with cross-flow HTML table
  4. `handle_flowchart_store` — captures test ID from flow button clicks
  5. `render_flowchart_modal` — shows/hides the flowchart modal with step diagram
  6. `close_flowchart_modal`  — closes modal on ✕ or backdrop click

Usage:
    from callbacks import register
    register(app)
"""

import json as _json
import pandas as pd
from datetime import date

import dash
from dash import Input, Output, State, callback_context, dash_table, ALL
from dash import html

from data_loader import load_all_reports
from cross_flow_loader import get_scenario, step_node_colors
from charts import (
    build_kpi_cards,
    build_pie_chart,
    build_duration_chart,
    build_failed_chart,
    build_timeseries_chart,
    build_monitor_chart,
    build_failure_root_chart,
    build_environment_table,
    build_module_chart,
    build_failed_endpoint_chart,
    build_failed_step_chart,
)
from config import (
    TABLE_PAGE_SIZE,
    FONT_FAMILY,
)


# ------------------------------------------------------------------
# TABLE STYLE DEFINITIONS
# ------------------------------------------------------------------
TABLE_HEADER_STYLE = {
    "backgroundColor": "#1e3799",
    "color": "white",
    "fontWeight": "700",
    "textAlign": "center",
    "fontFamily": FONT_FAMILY,
    "fontSize": "13px",
    "padding": "12px 8px",
    "letterSpacing": "0.5px",
}

TABLE_CELL_STYLE = {
    "textAlign": "center",
    "padding": "10px 8px",
    "fontFamily": FONT_FAMILY,
    "fontSize": "12px",
    "minWidth": "120px",
    "color": "#2d3436",
}

TABLE_CONTAINER_STYLE = {
    "overflowX": "auto",
    "maxHeight": "560px",
    "overflowY": "auto",
    "backgroundColor": "white",
    "borderRadius": "12px",
    "boxShadow": "0 2px 12px rgba(0,0,0,0.07)",
}

TABLE_STRIPE_STYLES = [
    {
        "if": {"row_index": "odd"},
        "backgroundColor": "#f8f9fa",
    },
    {
        "if": {"state": "active"},
        "backgroundColor": "#dfe6e9",
        "border": "1px solid #b2bec3",
    },
]


# ------------------------------------------------------------------
# SUBTYPE BADGE HELPER
# ------------------------------------------------------------------
_SUBTYPE_COLORS = {
    "common":  ("#dbeafe", "#1d4ed8"),
    "invoice": ("#dcfce7", "#15803d"),
    "rbac":    ("#f3e8ff", "#7e22ce"),
    "company": ("#fef9c3", "#92400e"),
}

def _subtype_badge(sub_type: str) -> html.Span:
    label = sub_type.strip().lower() if sub_type and sub_type.strip() not in ("", "—") else "—"
    bg, fg = _SUBTYPE_COLORS.get(label, ("#f1f5f9", "#475569"))
    return html.Span(
        label.upper() if label != "—" else "—",
        style={
            "backgroundColor": bg,
            "color": fg,
            "fontWeight": "700",
            "fontSize": "10px",
            "padding": "3px 8px",
            "borderRadius": "20px",
            "letterSpacing": "0.6px",
            "fontFamily": FONT_FAMILY,
        },
    )


# ------------------------------------------------------------------
# CROSS-FLOW HTML TABLE BUILDER
# ------------------------------------------------------------------

def _build_cross_flow_table(df_cross: pd.DataFrame) -> html.Div:
    """
    Build a premium custom HTML table for CrossDataFlow tests.
    Each row has a '📊 Flow' button that triggers the flowchart modal.
    Also shows Sub Type badge and Expected vs Got for every row.
    """
    if df_cross.empty:
        return html.Div(
            "No CrossDataFlow tests found for this date.",
            style={
                "textAlign": "center",
                "color": "#94a3b8",
                "padding": "40px",
                "fontFamily": FONT_FAMILY,
                "fontSize": "14px",
            },
        )

    status_colors = {
        "PASS":    ("#dcfce7", "#15803d"),
        "FAIL":    ("#fee2e2", "#b91c1c"),
        "SKIPPED": ("#fef9c3", "#92400e"),
        "BROKEN":  ("#f3e8ff", "#7e22ce"),
    }

    header_cells = [
        "Flow", "Test ID", "Sub Type", "Test Name",
        "Status", "Expected vs Got", "Failed Step", "Duration (s)",
    ]

    header_row = html.Tr([
        html.Th(
            col,
            style={
                "padding": "12px 14px",
                "textAlign": "left" if col != "Flow" else "center",
                "fontFamily": FONT_FAMILY,
                "fontSize": "11px",
                "fontWeight": "700",
                "letterSpacing": "0.8px",
                "color": "#94a3b8",
                "background": "#f8fafc",
                "borderBottom": "2px solid #e2e8f0",
                "whiteSpace": "nowrap",
            },
        )
        for col in header_cells
    ])

    rows = []
    for _, row in df_cross.iterrows():
        test_id  = str(row.get("TEST ID", ""))
        sub_type = str(row.get("SUB TYPE", "—"))
        status   = str(row.get("STATUS", "")).upper()
        evg      = str(row.get("EXPECTED VS GOT", "—"))
        step     = str(row.get("FAILED STEP", "—"))
        dur      = str(row.get("DURATION (S)", "—"))
        name     = str(row.get("TEST NAME", ""))

        st_bg, st_fg = status_colors.get(status, ("#f1f5f9", "#475569"))

        # Flow button — uses a custom data attribute as the test ID
        flow_btn = html.Button(
            "📊 Flow",
            id={"type": "flow_btn", "index": test_id},
            n_clicks=0,
            style={
                "background": "linear-gradient(135deg,#6366f1 0%,#818cf8 100%)",
                "color": "white",
                "border": "none",
                "padding": "5px 12px",
                "borderRadius": "8px",
                "fontSize": "11px",
                "fontWeight": "600",
                "cursor": "pointer",
                "fontFamily": FONT_FAMILY,
                "boxShadow": "0 2px 8px rgba(99,102,241,0.35)",
                "whiteSpace": "nowrap",
            },
        )

        rows.append(html.Tr(
            [
                html.Td(flow_btn, style={"padding": "10px 14px", "textAlign": "center"}),
                html.Td(
                    html.Span(test_id, style={
                        "fontFamily": "monospace",
                        "fontSize": "11px",
                        "color": "#334155",
                        "fontWeight": "600",
                    }),
                    style={"padding": "10px 14px", "whiteSpace": "nowrap"},
                ),
                html.Td(_subtype_badge(sub_type), style={"padding": "10px 14px"}),
                html.Td(
                    name,
                    style={
                        "padding": "10px 14px",
                        "maxWidth": "260px",
                        "overflow": "hidden",
                        "textOverflow": "ellipsis",
                        "whiteSpace": "nowrap",
                        "fontSize": "12px",
                        "color": "#334155",
                    },
                    title=name,
                ),
                html.Td(
                    html.Span(
                        status,
                        style={
                            "backgroundColor": st_bg,
                            "color": st_fg,
                            "fontWeight": "700",
                            "fontSize": "10px",
                            "padding": "3px 9px",
                            "borderRadius": "20px",
                            "fontFamily": FONT_FAMILY,
                        },
                    ),
                    style={"padding": "10px 14px"},
                ),
                html.Td(
                    html.Span(
                        evg if evg != "—" else "—",
                        style={
                            "fontFamily": "monospace",
                            "fontSize": "11px",
                            "color": "#0f766e" if ("→" in evg and "→" in evg and evg != "—") else "#94a3b8",
                        },
                    ),
                    style={"padding": "10px 14px", "whiteSpace": "nowrap"},
                ),
                html.Td(
                    html.Span(
                        step if step != "—" else "—",
                        style={
                            "color": "#ef4444" if step != "—" else "#94a3b8",
                            "fontSize": "11px",
                        },
                    ),
                    style={"padding": "10px 14px"},
                ),
                html.Td(
                    dur,
                    style={
                        "padding": "10px 14px",
                        "color": "#64748b",
                        "fontSize": "12px",
                    },
                ),
            ],
            style={
                "borderBottom": "1px solid #f1f5f9",
                "transition": "background-color 0.15s",
            },
        ))

    table = html.Table(
        [html.Thead(header_row), html.Tbody(rows)],
        style={
            "width": "100%",
            "borderCollapse": "collapse",
            "fontFamily": FONT_FAMILY,
            "fontSize": "13px",
        },
    )

    return html.Div(
        table,
        style={
            "overflowX": "auto",
            "maxHeight": "540px",
            "overflowY": "auto",
            "borderRadius": "12px",
        },
    )


# ------------------------------------------------------------------
# FLOWCHART RENDERER
# ------------------------------------------------------------------

_STEP_METHOD_ICONS = {
    "GET": "🔍", "POST": "➕", "DELETE": "🗑️", "PUT": "✏️", "PATCH": "🔧",
}

def _render_flowchart(steps: list) -> html.Div:
    """
    Render a premium, vertical step-by-step timeline flowchart.
    Each step is presented as a card linked by a continuous left vertical line.
    """
    nodes = []

    for i, step in enumerate(steps):
        step_name  = step.get("stepName", f"step_{i+1}")
        method     = str(step.get("method", "GET")).upper()
        endpoint   = step.get("endpoint", "")
        role       = step.get("userRole", "")
        expected   = step.get("expectedStatus", "")
        always_run = step.get("alwaysRun", False)
        capture    = step.get("captureAs", "")

        bg, fg = step_node_colors(step)
        icon = _STEP_METHOD_ICONS.get(method, "📡")

        # Method & utility badges
        method_pill = html.Span(
            f"{icon} {method}",
            style={
                "backgroundColor": fg,
                "color": "white",
                "fontSize": "9.5px",
                "fontWeight": "700",
                "padding": "2px 8px",
                "borderRadius": "12px",
                "letterSpacing": "0.4px",
            },
        )

        badges = [method_pill]
        if always_run:
            badges.append(html.Span(
                "CLEANUP",
                style={
                    "backgroundColor": "#fef3c7",
                    "color": "#92400e",
                    "fontSize": "9.5px",
                    "fontWeight": "700",
                    "padding": "2px 8px",
                    "borderRadius": "12px",
                    "letterSpacing": "0.4px",
                },
            ))
        if capture:
            badges.append(html.Span(
                f"→ :{capture}",
                style={
                    "backgroundColor": "#ede9fe",
                    "color": "#6d28d9",
                    "fontSize": "9.5px",
                    "fontWeight": "600",
                    "padding": "2px 8px",
                    "borderRadius": "12px",
                    "fontFamily": "monospace",
                },
            ))

        # Expected status badge
        expected_status_div = html.Div(
            [
                html.Span(
                    "Expected Status: ",
                    style={"color": "#64748b", "fontSize": "11px", "fontWeight": "600"},
                ),
                html.Span(
                    str(expected),
                    style={
                        "fontWeight": "800",
                        "fontSize": "11px",
                        "color": "#15803d" if str(expected).startswith("2") else "#b91c1c",
                        "backgroundColor": "#dcfce7" if str(expected).startswith("2") else "#fee2e2",
                        "padding": "2px 6px",
                        "borderRadius": "4px",
                    },
                ),
            ],
            style={"display": "inline-flex", "alignItems": "center", "marginTop": "8px"},
        ) if expected else html.Div()

        # Collapsible request/response bodies
        details_elements = []
        if step.get("body"):
            try:
                pretty_body = _json.dumps(step["body"], indent=2)
            except Exception:
                pretty_body = str(step["body"])
            details_elements.append(
                html.Details(
                    [
                        html.Summary(
                            "📦 View Request Payload",
                            style={
                                "fontSize": "11px",
                                "fontWeight": "700",
                                "color": "#4f46e5",
                                "cursor": "pointer",
                            }
                        ),
                        html.Pre(
                            pretty_body,
                            className="monospace-code",
                            style={
                                "backgroundColor": "#f8fafc",
                                "border": "1px solid #e2e8f0",
                                "borderRadius": "6px",
                                "padding": "8px 12px",
                                "fontSize": "10px",
                                "color": "#334155",
                                "marginTop": "6px",
                                "maxHeight": "150px",
                                "overflowY": "auto",
                                "textAlign": "left",
                            }
                        )
                    ]
                )
            )
        if step.get("validateBody"):
            try:
                pretty_val = _json.dumps(step["validateBody"], indent=2)
            except Exception:
                pretty_val = str(step["validateBody"])
            details_elements.append(
                html.Details(
                    [
                        html.Summary(
                            "🔍 View Response Assertions",
                            style={
                                "fontSize": "11px",
                                "fontWeight": "700",
                                "color": "#0891b2",
                                "cursor": "pointer",
                            }
                        ),
                        html.Pre(
                            pretty_val,
                            className="monospace-code",
                            style={
                                "backgroundColor": "#f8fafc",
                                "border": "1px solid #e2e8f0",
                                "borderRadius": "6px",
                                "padding": "8px 12px",
                                "fontSize": "10px",
                                "color": "#334155",
                                "marginTop": "6px",
                                "maxHeight": "150px",
                                "overflowY": "auto",
                                "textAlign": "left",
                            }
                        )
                    ]
                )
            )

        # Continuous timeline vertical line segment for this step
        if len(steps) == 1:
            line_style = {"display": "none"}
        elif i == 0:
            line_style = {
                "position": "absolute",
                "top": "16px",
                "bottom": "0",
                "left": "50%",
                "width": "2px",
                "backgroundColor": "#e2e8f0",
                "transform": "translateX(-50%)",
                "zIndex": "1",
            }
        elif i == len(steps) - 1:
            line_style = {
                "position": "absolute",
                "top": "0",
                "height": "16px",
                "left": "50%",
                "width": "2px",
                "backgroundColor": "#e2e8f0",
                "transform": "translateX(-50%)",
                "zIndex": "1",
            }
        else:
            line_style = {
                "position": "absolute",
                "top": "0",
                "bottom": "0",
                "left": "50%",
                "width": "2px",
                "backgroundColor": "#e2e8f0",
                "transform": "translateX(-50%)",
                "zIndex": "1",
            }

        node = html.Div(
            [
                # Timeline node column
                html.Div(
                    [
                        html.Div(style=line_style),
                        html.Div(
                            f"{i + 1}",
                            className="flow-circle",
                            style={
                                "width": "26px",
                                "height": "26px",
                                "borderRadius": "50%",
                                "backgroundColor": fg,
                                "color": "white",
                                "display": "flex",
                                "alignItems": "center",
                                "justifyContent": "center",
                                "fontSize": "10.5px",
                                "fontWeight": "800",
                                "zIndex": "2",
                                "boxShadow": f"0 0 0 4px {bg}, 0 4px 10px {fg}40",
                                "fontFamily": FONT_FAMILY,
                                "position": "relative",
                                "top": "3px",
                            },
                        ),
                    ],
                    style={
                        "width": "44px",
                        "display": "flex",
                        "justifyContent": "center",
                        "alignItems": "flex-start",
                        "position": "relative",
                        "flexShrink": "0",
                    },
                ),
                # Step Card column
                html.Div(
                    [
                        html.Div(
                            [
                                # Header (Name + Badges)
                                html.Div(
                                    [
                                        html.Span(
                                            step_name.replace("_", " ").upper(),
                                            style={
                                                "fontWeight": "850",
                                                "fontSize": "12.5px",
                                                "color": "#0f172a",
                                                "letterSpacing": "0.5px",
                                            },
                                        ),
                                        html.Div(
                                            badges,
                                            style={
                                                "display": "flex",
                                                "gap": "6px",
                                                "alignItems": "center",
                                            },
                                        ),
                                    ],
                                    style={
                                        "display": "flex",
                                        "justifyContent": "space-between",
                                        "alignItems": "center",
                                        "marginBottom": "10px",
                                        "flexWrap": "wrap",
                                        "gap": "6px",
                                    },
                                ),
                                # Details
                                html.Div(
                                    [
                                        # Role + Endpoint
                                        html.Div(
                                            [
                                                html.Span(
                                                    f"👤 {role}",
                                                    style={
                                                        "color": "#64748b",
                                                        "fontWeight": "600",
                                                        "fontSize": "11px",
                                                        "marginRight": "10px",
                                                    },
                                                ),
                                                html.Span(
                                                    endpoint,
                                                    className="monospace-code",
                                                    style={
                                                        "fontSize": "11px",
                                                        "color": "#334155",
                                                        "backgroundColor": "#f1f5f9",
                                                        "padding": "2px 8px",
                                                        "borderRadius": "4px",
                                                        "wordBreak": "break-all",
                                                    },
                                                ),
                                            ],
                                            style={
                                                "display": "flex",
                                                "alignItems": "center",
                                                "flexWrap": "wrap",
                                                "gap": "6px",
                                                "marginBottom": "6px",
                                            },
                                        ),
                                        expected_status_div,
                                    ]
                                ),
                                # Expandable details (body / validations)
                                *details_elements,
                            ],
                            className="step-card",
                            style={
                                "backgroundColor": "white",
                                "borderRadius": "10px",
                                "padding": "16px",
                                "border": "1px solid #e2e8f0",
                                "borderLeft": f"4px solid {fg}",
                                "boxShadow": "0 1px 3px 0 rgba(0, 0, 0, 0.05)",
                            },
                        )
                    ],
                    style={"flex": "1", "paddingBottom": "20px"},
                ),
            ],
            style={"display": "flex", "position": "relative"},
        )

        nodes.append(node)

    return html.Div(nodes)


# ------------------------------------------------------------------
# MAIN REGISTER FUNCTION
# ------------------------------------------------------------------

def register(app) -> None:
    """Register all callbacks onto the Dash app instance."""

    # ==============================================================
    # CALLBACK 1 — Main Dashboard Update
    # ==============================================================
    @app.callback(
        [
            Output("kpi_cards", "children"),
            Output("pie_chart", "figure"),
            Output("duration_chart", "figure"),
            Output("failed_chart", "figure"),
            Output("timeseries_chart", "figure"),
            Output("monitor_chart", "figure"),
            Output("failure_root_chart", "figure"),
            Output("environment_breakdown_container", "children"),
            Output("module_breakdown_chart", "figure"),
            Output("failed_endpoint_chart", "figure"),
            Output("failed_step_chart", "figure"),
        ],
        [
            Input("selected_date", "date"),
        ],
    )
    def update_dashboard(selected_date):
        df = load_all_reports()

        if not selected_date:
            selected_date = str(date.today())

        selected_date_obj = pd.to_datetime(selected_date).date()
        df_single = df[df["DATE"] == selected_date_obj]

        start_date_obj = selected_date_obj - pd.Timedelta(days=10)
        df_trend = df[
            (df["DATE"] >= start_date_obj) & (df["DATE"] <= selected_date_obj)
        ]

        kpi            = build_kpi_cards(df_single)
        pie            = build_pie_chart(df_single)
        dur            = build_duration_chart(df_single)
        failed         = build_failed_chart(df_trend)
        ts             = build_timeseries_chart(df_trend)
        monitor        = build_monitor_chart(df_single)
        root           = build_failure_root_chart(df_single)
        env_table      = build_environment_table(df_single, df_trend)
        module_chart   = build_module_chart(df_single)
        failed_endpoint= build_failed_endpoint_chart(df_single)
        failed_step    = build_failed_step_chart(df_single)

        return kpi, pie, dur, failed, ts, monitor, root, env_table, module_chart, failed_endpoint, failed_step

    # ==============================================================
    # CALLBACK 2 — Update Active Table Type
    # ==============================================================
    @app.callback(
        Output("active_table_type", "data"),
        [
            Input("btn_new", "n_clicks"),
            Input("btn_updated", "n_clicks"),
            Input("btn_failed", "n_clicks"),
            Input("btn_full", "n_clicks"),
            Input("btn_crossflow", "n_clicks"),
        ],
        prevent_initial_call=True,
    )
    def update_active_table(new_clicks, updated_clicks, failed_clicks, full_clicks, cross_clicks):
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
        ],
    )
    def show_table(active_table, selected_date):
        if not active_table:
            return ""

        df = load_all_reports()

        if not selected_date:
            selected_date = str(date.today())
        selected_date_obj = pd.to_datetime(selected_date).date()

        df_filtered = df[df["DATE"] == selected_date_obj]

        # ── CrossDataFlow custom HTML table ───────────────────────
        if active_table == "btn_crossflow":
            is_cross = df_filtered["FEATURE AREA"].astype(str).str.contains(
                "CrossDataFlow", case=False, na=False
            )
            df_cross = df_filtered[is_cross].copy()

            # Coerce datetime cols
            for col in ["DATE", "UPDATED AT", "CREATED AT"]:
                if col in df_cross.columns:
                    df_cross[col] = df_cross[col].astype(str)

            title = f"🔄 Cross-Data-Flow Tests (Selected Date: {selected_date_obj})"
            return html.Div(
                [
                    html.Div(
                        title,
                        style={
                            "fontWeight": "700",
                            "fontSize": "15px",
                            "marginBottom": "12px",
                            "fontFamily": FONT_FAMILY,
                            "color": "#2d3436",
                            "paddingLeft": "4px",
                        },
                    ),
                    _build_cross_flow_table(df_cross),
                ],
                style={
                    "backgroundColor": "white",
                    "borderRadius": "14px",
                    "boxShadow": "0 2px 12px rgba(0,0,0,0.07)",
                    "padding": "20px",
                },
            )

        # ── Standard DataTable views ───────────────────────────────
        if active_table == "btn_new":
            cols = ["DATE", "TEST ID", "TEST TYPE", "SUB TYPE", "TEST NAME", "STATUS",
                    "EXPECTED VS GOT", "DURATION (S)"]
            cols = [c for c in cols if c in df_filtered.columns]
            table_df = df_filtered[cols]
            title = f"🆕 New Tests (Selected Date: {selected_date_obj})"

        elif active_table == "btn_updated":
            table_df = df_filtered[df_filtered["UPDATED AT"].notna()]
            cols = ["DATE", "UPDATED AT", "TEST ID", "TEST TYPE", "SUB TYPE",
                    "TEST NAME", "STATUS", "EXPECTED VS GOT"]
            cols = [c for c in cols if c in table_df.columns]
            table_df = table_df[cols]
            title = f"✏️ Updated Tests (Selected Date: {selected_date_obj})"

        elif active_table == "btn_failed":
            table_df = df_filtered[
                df_filtered["STATUS"].astype(str).str.contains("FAIL", na=False)
            ]
            cols = [
                "DATE", "TEST ID", "TEST TYPE", "SUB TYPE", "TEST NAME",
                "STATUS", "DURATION (S)", "MONITOR STATUS",
                "FAILURE ROOT CAUSE", "FAILED ENDPOINT",
                "EXPECTED VS GOT", "SERVER ERROR MESSAGE",
                "FAILED STEP", "SOURCE LOCATION",
            ]
            cols = [c for c in cols if c in table_df.columns]
            table_df = table_df[cols]
            title = f"❌ Failed Tests (Selected Date: {selected_date_obj})"

        else:  # btn_full
            table_df = df_filtered.copy()
            # Put the most useful cols first
            priority_cols = [
                "DATE", "TEST ID", "TEST TYPE", "SUB TYPE", "TEST NAME",
                "STATUS", "EXPECTED VS GOT", "DURATION (S)",
            ]
            remaining = [c for c in table_df.columns if c not in priority_cols]
            col_order = [c for c in priority_cols if c in table_df.columns] + remaining
            table_df = table_df[col_order]
            title = f"📋 Full Dataset (Selected Date: {selected_date_obj})"

        # Convert datetime columns to readable strings
        for col in ["DATE", "UPDATED AT", "UPDATED DATE", "CREATED AT"]:
            if col in table_df.columns:
                table_df[col] = table_df[col].astype(str)

        # Conditional status row colouring
        status_styles = TABLE_STRIPE_STYLES + [
            {
                "if": {
                    "filter_query": '{STATUS} contains "FAIL"',
                },
                "backgroundColor": "#fff5f5",
            },
            {
                "if": {
                    "filter_query": '{STATUS} contains "PASS"',
                },
                "backgroundColor": "#f0fff4",
            },
        ]

        return html.Div(
            [
                html.Div(
                    title,
                    style={
                        "fontWeight": "700",
                        "fontSize": "15px",
                        "marginBottom": "12px",
                        "fontFamily": FONT_FAMILY,
                        "color": "#2d3436",
                        "paddingLeft": "4px",
                    },
                ),
                dash_table.DataTable(
                    columns=[{"name": col, "id": col} for col in table_df.columns],
                    data=table_df.to_dict("records"),
                    page_size=TABLE_PAGE_SIZE,
                    filter_action="native",
                    sort_action="native",
                    style_table=TABLE_CONTAINER_STYLE,
                    style_header=TABLE_HEADER_STYLE,
                    style_cell=TABLE_CELL_STYLE,
                    style_data_conditional=status_styles,
                ),
            ],
            style={
                "backgroundColor": "white",
                "borderRadius": "14px",
                "boxShadow": "0 2px 12px rgba(0,0,0,0.07)",
                "padding": "20px",
            },
        )

    # ==============================================================
    # CALLBACK 4 — Capture flow button click → store test ID
    # ==============================================================
    @app.callback(
        Output("flowchart_test_id", "data"),
        Input({"type": "flow_btn", "index": ALL}, "n_clicks"),
        prevent_initial_call=True,
    )
    def capture_flow_btn(n_clicks_list):
        ctx = callback_context
        if not ctx.triggered:
            return ""
        # The prop_id looks like: '{"index":"CROSS_FLOW_BUYER_LIFECYCLE","type":"flow_btn"}.n_clicks'
        prop_id = ctx.triggered[0]["prop_id"]
        try:
            id_part = prop_id.split(".n_clicks")[0]
            id_dict = _json.loads(id_part)
            return id_dict.get("index", "")
        except Exception:
            return ""

    # ==============================================================
    # CALLBACK 5 — Show/render the flowchart modal
    # ==============================================================
    @app.callback(
        [
            Output("flowchart_modal_overlay", "style"),
            Output("flowchart_modal_title", "children"),
            Output("flowchart_modal_meta", "children"),
            Output("flowchart_modal_body", "children"),
        ],
        [
            Input("flowchart_test_id", "data"),
            Input("flowchart_close_btn", "n_clicks"),
            Input("flowchart_backdrop", "n_clicks"),
        ],
    )
    def render_flowchart_modal(test_id, close_clicks, backdrop_clicks):
        hidden = {"display": "none"}
        visible = {"display": "block"}

        ctx = callback_context
        if not ctx.triggered:
            return hidden, "", "", ""

        trigger = ctx.triggered[0]["prop_id"].split(".")[0]

        # Close on ✕ button or backdrop click
        if trigger in ("flowchart_close_btn", "flowchart_backdrop"):
            return hidden, "", "", ""

        # Open when test_id changes
        if not test_id:
            return hidden, "", "", ""

        scenario = get_scenario(test_id)
        if not scenario:
            return (
                visible,
                f"Flow: {test_id}",
                html.Span("No scenario definition found.", style={"color": "#ef4444"}),
                html.Div(),
            )

        title = scenario.get("title", test_id)
        description = scenario.get("description", "")
        sub_type = scenario.get("subType", "")
        steps = scenario.get("steps", [])

        # Meta row: sub-type badge + description
        meta = html.Div(
            [
                html.Div(
                    [
                        html.Span(
                            "Sub-Type: ",
                            style={
                                "fontSize": "11px",
                                "color": "#94a3b8",
                                "fontWeight": "600",
                                "marginRight": "6px",
                            },
                        ),
                        _subtype_badge(sub_type),
                        html.Span(
                            f"  •  {len(steps)} steps",
                            style={
                                "fontSize": "11px",
                                "color": "#94a3b8",
                                "marginLeft": "10px",
                            },
                        ),
                    ],
                    style={"marginBottom": "8px"},
                ),
                html.P(
                    description,
                    style={
                        "fontSize": "12px",
                        "color": "#64748b",
                        "margin": "0",
                        "lineHeight": "1.6",
                        "fontFamily": FONT_FAMILY,
                    },
                ),
            ]
        )

        body = _render_flowchart(steps) if steps else html.Div(
            "No steps defined for this scenario.",
            style={"color": "#94a3b8", "fontSize": "13px"},
        )

        return visible, title, meta, body

import pandas as pd
import numpy as np

from dash import Dash
from dash import dcc
from dash import html
from dash import dash_table

from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State

from dash import callback_context

import plotly.express as px
import plotly.graph_objects as go

# =========================================================
# LOAD CSV FILES
# =========================================================

file1 = "test-summary-2026-06-08.csv"
file2 = "9 June.csv"
file3 = "10 June.csv"


# =========================================================
# LOAD DATA FUNCTION
# =========================================================
def load_data():

    print("Reloading CSV...")
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)
    df3 = pd.read_csv(file3)

    df = pd.concat([df1, df2, df3], ignore_index=True)

    # ==========================================
    # CLEAN COLUMN NAMES
    # ==========================================

    df.columns = df.columns.str.strip().str.upper()

    # ==========================================
    # DATE CONVERSION
    # ==========================================

    df["START TIME"] = pd.to_datetime(
        df["START TIME"], errors="coerce", dayfirst=True, format="mixed"
    )

    df["STOP TIME"] = pd.to_datetime(
        df["STOP TIME"], errors="coerce", dayfirst=True, format="mixed"
    )

    df["UPDATED AT"] = pd.to_datetime(
        df["UPDATED AT"], errors="coerce", dayfirst=True, format="mixed"
    )

    # ==========================================
    # REMOVE INVALID DATES
    # ==========================================

    df = df[df["START TIME"].notna()]

    # ==========================================
    # DATE COLUMNS
    # ==========================================

    df["DATE"] = df["START TIME"].dt.date

    df["UPDATED DATE"] = df["UPDATED AT"].dt.date

    # ==========================================
    # STATUS CLEANING
    # ==========================================

    df["STATUS"] = df["STATUS"].astype(str).str.upper().str.strip()

    if "MONITOR STATUS" not in df.columns:
        df["MONITOR STATUS"] = "MONITOR CLOSELY"

    df["MONITOR STATUS"] = (
        df["MONITOR STATUS"]
        .fillna("MONITOR CLOSELY")
        .replace("", "MONITOR CLOSELY")
        .astype(str)
        .str.upper()
        .str.strip()
    )

    df["STATUS"] = df["STATUS"].replace(
        {"PASSED": "PASS", "FAILED": "FAIL", "SUCCESS": "PASS", "ERROR": "FAIL"}
    )

    # ==========================================
    # DURATION
    # ==========================================

    df["DURATION (S)"] = (
        df["DURATION (S)"]
        .astype(str)
        .str.replace("s", "", regex=False)
        .str.replace(",", "", regex=False)
    )

    df["DURATION (S)"] = pd.to_numeric(df["DURATION (S)"], errors="coerce")

    bins = [0, 5, 10, 20, 30, 40, 50, 60, 100000]

    labels = [
        "0-5 Seconds",
        "5-10 Seconds",
        "10-20 Seconds",
        "20-30 Seconds",
        "30-40 Seconds",
        "40-50 Seconds",
        "50-60 Seconds",
        "60+ Seconds",
    ]

    df["DURATION GROUP"] = pd.cut(
        df["DURATION (S)"], bins=bins, labels=labels, include_lowest=True
    )

    return df


df = load_data()


# =========================================================
# COLORS
# =========================================================

status_colors = {
    "PASSED": "#2ecc71",
    "FAILED": "#e74c3c",
    "SKIPPED": "#f1c40f",
    "BROKEN": "#8e44ad",
}

# =========================================================
# APP
# =========================================================

app = Dash(__name__)

# =========================================================
# APP LAYOUT
# =========================================================

app.layout = html.Div(
    [
        dcc.Interval(id="refresh_timer", interval=60000, n_intervals=0),
        html.H1(
            "TEST EXECUTION ANALYTICS DASHBOARD",
            style={"textAlign": "center", "color": "#1b6ab9", "marginBottom": "20px"},
        ),
        # =====================================================
        # FILTERS
        # =====================================================
        html.Div(
            [
                html.Div(
                    [
                        html.Label("SELECT START DATE", style={"fontWeight": "bold"}),
                        dcc.DatePickerSingle(
                            id="start_date", date=str(df["DATE"].dropna().min())
                        ),
                    ],
                    style={"width": "32%", "display": "inline-block"},
                ),
                html.Div(
                    [
                        html.Label("SELECT END DATE", style={"fontWeight": "bold"}),
                        dcc.DatePickerSingle(
                            id="end_date", date=str(df["DATE"].dropna().max())
                        ),
                    ],
                    style={
                        "width": "32%",
                        "display": "inline-block",
                        "marginLeft": "1%",
                    },
                ),
                html.Div(
                    [
                        html.Label("FILTER STATUS", style={"fontWeight": "bold"}),
                        dcc.Dropdown(
                            id="status_filter",
                            options=[
                                {"label": i, "value": i}
                                for i in sorted(df["STATUS"].dropna().unique())
                            ],
                            multi=True,
                            placeholder="Select Status",
                        ),
                    ],
                    style={
                        "width": "32%",
                        "display": "inline-block",
                        "marginLeft": "1%",
                    },
                ),
            ],
            style={
                "backgroundColor": "white",
                "padding": "20px",
                "borderRadius": "10px",
            },
        ),
        html.Br(),
        html.Div(id="kpi_cards"),
        html.Br(),
        # =====================================================
        # ROW 1
        # =====================================================
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="pie_chart")],
                    style={
                        "width": "49%",
                        "backgroundColor": "white",
                        "padding": "10px",
                        "borderRadius": "10px",
                    },
                ),
                html.Div(
                    [dcc.Graph(id="duration_chart")],
                    style={
                        "width": "49%",
                        "backgroundColor": "white",
                        "padding": "10px",
                        "borderRadius": "10px",
                    },
                ),
            ],
            style={"display": "flex", "justifyContent": "space-between", "gap": "10px"},
        ),
        html.Br(),
        # =====================================================
        # ROW 2
        # =====================================================
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="failed_chart")],
                    style={
                        "width": "49%",
                        "backgroundColor": "white",
                        "padding": "10px",
                        "borderRadius": "10px",
                    },
                ),
                html.Div(
                    [dcc.Graph(id="timeseries_chart")],
                    style={
                        "width": "49%",
                        "backgroundColor": "white",
                        "padding": "10px",
                        "borderRadius": "10px",
                    },
                ),
            ],
            style={"display": "flex", "justifyContent": "space-between", "gap": "10px"},
        ),
        html.Br(),
        # =====================================================
        # MONITOR GRAPH
        # =====================================================
        html.Div(
            [dcc.Graph(id="monitor_chart")],
            style={
                "backgroundColor": "white",
                "padding": "10px",
                "borderRadius": "5px",
            },
        ),
        html.Br(),
        # =====================================================
        # FAILURE ROOT CAUSE DONUT CHART
        # =====================================================
        html.Div(
            [dcc.Graph(id="failure_root_chart")],
            style={
                "backgroundColor": "white",
                "padding": "10px",
                "borderRadius": "8px",
            },
        ),
        # =====================================================
        # BUTTONS
        # =====================================================
        html.Div(
            [
                html.Button(
                    "VIEW NEW TESTS",
                    id="btn_new",
                    n_clicks=0,
                    style={
                        "backgroundColor": "#2ecc71",
                        "color": "white",
                        "border": "none",
                        "padding": "12px 20px",
                        "marginRight": "10px",
                        "cursor": "pointer",
                    },
                ),
                html.Button(
                    "VIEW UPDATED TESTS",
                    id="btn_updated",
                    n_clicks=0,
                    style={
                        "backgroundColor": "#e67e22",
                        "color": "white",
                        "border": "none",
                        "padding": "12px 20px",
                        "marginRight": "10px",
                        "cursor": "pointer",
                    },
                ),
                html.Button(
                    "FULL CSV TABLE",
                    id="btn_full",
                    n_clicks=0,
                    style={
                        "backgroundColor": "#3498db",
                        "color": "white",
                        "border": "none",
                        "padding": "12px 20px",
                        "cursor": "pointer",
                    },
                ),
            ],
            style={"textAlign": "center", "marginTop": "15px"},
        ),
        html.Br(),
        html.Div(id="dynamic_table"),
    ],
    style={"backgroundColor": "#f5f7fa", "padding": "20px"},
)

# =========================================================
# CALLBACK
# =========================================================


@app.callback(
    [
        Output("kpi_cards", "children"),
        Output("pie_chart", "figure"),
        Output("duration_chart", "figure"),
        Output("failed_chart", "figure"),
        Output("timeseries_chart", "figure"),
        Output("monitor_chart", "figure"),
        Output("failure_root_chart", "figure"),
    ],
    [
        Input("start_date", "date"),
        Input("end_date", "date"),
        Input("status_filter", "value"),
        Input("refresh_timer", "n_intervals"),
    ],
)
def update_dashboard(start_date, end_date, selected_status, refresh_timer):
    df = load_data()

    filtered_df = df.copy()

    # =====================================================
    # FILTERING
    # =====================================================

    if start_date and end_date:

        start_date = pd.to_datetime(start_date).date()

        end_date = pd.to_datetime(end_date).date()

        filtered_df = filtered_df[
            (filtered_df["DATE"] >= start_date) & (filtered_df["DATE"] <= end_date)
        ]

    if selected_status:

        filtered_df = filtered_df[filtered_df["STATUS"].isin(selected_status)]

    # =====================================================
    # KPI COUNTS
    # =====================================================

    status_series = filtered_df["STATUS"].astype(str).str.upper().str.strip()

    total_count = len(filtered_df)

    pass_count = status_series.str.contains("PASS", na=False).sum()

    fail_count = status_series.str.contains("FAIL", na=False).sum()

    skipped_count = status_series.str.contains("SKIP", na=False).sum()

    broken_count = status_series.str.contains("BROKEN", na=False).sum()

    # =====================================================
    # KPI CARDS
    # =====================================================

    kpi_cards = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [html.H3("TOTAL"), html.H1(total_count)],
                        style={
                            "backgroundColor": "#dfe6e9",
                            "width": "18%",
                            "padding": "20px",
                            "textAlign": "center",
                            "borderRadius": "8px",
                        },
                    ),
                    html.Div(
                        [html.H3("PASS"), html.H1(pass_count)],
                        style={
                            "backgroundColor": "#2ecc71",
                            "color": "white",
                            "width": "18%",
                            "padding": "20px",
                            "textAlign": "center",
                            "borderRadius": "8px",
                        },
                    ),
                    html.Div(
                        [html.H3("FAIL"), html.H1(fail_count)],
                        style={
                            "backgroundColor": "#e74c3c",
                            "color": "white",
                            "width": "18%",
                            "padding": "20px",
                            "textAlign": "center",
                            "borderRadius": "8px",
                        },
                    ),
                    html.Div(
                        [html.H3("SKIPPED"), html.H1(skipped_count)],
                        style={
                            "backgroundColor": "#f1c40f",
                            "width": "18%",
                            "padding": "20px",
                            "textAlign": "center",
                            "borderRadius": "8px",
                        },
                    ),
                    html.Div(
                        [html.H3("BROKEN"), html.H1(broken_count)],
                        style={
                            "backgroundColor": "#6c2bd9",
                            "color": "white",
                            "width": "18%",
                            "padding": "20px",
                            "textAlign": "center",
                            "borderRadius": "8px",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "gap": "10px",
                    "marginBottom": "15px",
                },
            )
        ]
    )

    # =====================================================
    # PIE CHART
    # =====================================================

    pie_df = filtered_df["STATUS"].value_counts().reset_index()

    pie_df.columns = ["STATUS", "COUNT"]

    pie_fig = go.Figure(
        data=[
            go.Pie(
                labels=pie_df["STATUS"],
                values=pie_df["COUNT"],
                hole=0.4,
                marker=dict(
                    colors=[
                        (
                            "#2ecc71"
                            if "PASS" in str(i)
                            else (
                                "#e74c3c"
                                if "FAIL" in str(i)
                                else "#f1c40f" if "SKIP" in str(i) else "#8e44ad"
                            )
                        )
                        for i in pie_df["STATUS"]
                    ]
                ),
                textinfo="label+value+percent",
            )
        ]
    )

    pie_fig.update_layout(
        title="TEST STATUS DISTRIBUTION",
        height=350,
        legend=dict(orientation="v", x=1, y=0.9),
        margin=dict(l=20, r=20, t=50, b=20),
    )

    # =====================================================
    # DURATION CHART
    # =====================================================

    duration_df = (
        filtered_df["DURATION GROUP"].value_counts().sort_index().reset_index()
    )

    duration_df.columns = ["DURATION RANGE", "COUNT"]

    duration_fig = px.bar(
        duration_df,
        x="DURATION RANGE",
        y="COUNT",
        text="COUNT",
        color="COUNT",
        title="DURATION ANALYSIS BAR CHART",
    )

    duration_fig.update_traces(textposition="outside")

    duration_fig.update_layout(height=420)

    # =====================================================
    # FAILED GRAPH
    # =====================================================

    failed_df = filtered_df[filtered_df["STATUS"].astype(str).str.contains("FAIL")]

    failed_group = failed_df.groupby("DATE").size().reset_index(name="FAILED COUNT")

    failed_fig = px.bar(
        failed_group,
        x="DATE",
        y="FAILED COUNT",
        text="FAILED COUNT",
        color="FAILED COUNT",
        title="FAILED TEST ANALYSIS",
    )

    failed_fig.update_traces(textposition="outside")

    failed_fig.update_layout(height=420)

    # =====================================================
    # TIMESERIES
    # =====================================================

    daily_total = filtered_df.groupby("DATE").size().reset_index(name="DAILY TESTS")

    # =====================================================
    # CUMULATIVE TOTAL
    # =====================================================

    daily_total["TOTAL TESTS"] = daily_total["DAILY TESTS"].cumsum()

    # =====================================================
    # NEW TESTS DAILY
    # =====================================================

    new_tests = filtered_df.groupby("DATE").size().reset_index(name="NEW TESTS")

    # =====================================================
    # UPDATED TESTS
    # =====================================================

    updated_df = filtered_df[filtered_df["UPDATED AT"].notna()]

    updated_tests = updated_df.groupby("DATE").size().reset_index(name="UPDATED TESTS")

    # =====================================================
    # TIMESERIES FIGURE
    # =====================================================

    ts_fig = go.Figure()

    ts_fig.add_trace(
        go.Scatter(
            x=daily_total["DATE"],
            y=daily_total["TOTAL TESTS"],
            mode="lines+markers",
            name="TOTAL TESTS",
            line=dict(color="blue", width=3),
        )
    )

    ts_fig.add_trace(
        go.Scatter(
            x=new_tests["DATE"],
            y=new_tests["NEW TESTS"],
            mode="lines+markers",
            name="NEW TESTS",
            line=dict(color="green", width=3),
        )
    )

    ts_fig.add_trace(
        go.Scatter(
            x=updated_tests["DATE"],
            y=updated_tests["UPDATED TESTS"],
            mode="lines+markers",
            name="UPDATED TESTS",
            line=dict(color="red", width=3),
        )
    )

    ts_fig.update_layout(
        title="DAILY UPDATED TEST TREND",
        xaxis_title="DATE",
        yaxis_title="COUNT",
        height=420,
    )

    # =====================================================
    # MONITOR STATUS ANALYSIS
    # =====================================================
    print("\nMONITOR STATUS VALUES:")
    print(filtered_df["MONITOR STATUS"].value_counts())

    monitor_df = filtered_df[
        filtered_df["MONITOR STATUS"].isin(["HIGH", "CRITICAL", "MONITOR CLOSELY"])
    ]

    monitor_group = (
        monitor_df.groupby(["MONITOR STATUS", "STATUS"])
        .size()
        .reset_index(name="COUNT")
    )
    print(monitor_group["STATUS"].unique())
    monitor_fig = px.bar(
        monitor_group,
        x="MONITOR STATUS",
        y="COUNT",
        color="STATUS",
        text="COUNT",
        barmode="stack",
        title="HIGH / CRITICAL / MONITOR CLOSELY STATUS",
        color_discrete_map={
            "✅ PASSED": "#2ecc71",
            "❌ FAILED": "#e74c3c",
            "⏭️ SKIPPED": "#f1c40f",
            "⚠️ BROKEN": "#8e44ad",
        },
    )

    monitor_fig.update_traces(textposition="inside")

    monitor_fig.update_layout(
        height=450,
        xaxis_title="MONITOR STATUS",
        yaxis_title="COUNT",
        legend_title="TEST STATUS",
    )
    # =====================================================
    # FAILURE ROOT CAUSE DONUT CHART
    # =====================================================

    failed_root_df = filtered_df[
        filtered_df["STATUS"].astype(str).str.contains("FAIL", na=False)
    ]

    root_group = (
        failed_root_df.groupby("FAILURE ROOT CAUSE")
        .size()
        .reset_index(name="FAILED COUNT")
    )

    root_group.columns = ["ROOT CAUSE", "FAILED COUNT"]

    root_group = root_group.sort_values(by="FAILED COUNT", ascending=False)

    failure_root_fig = px.pie(
        root_group,
        names="ROOT CAUSE",
        values="FAILED COUNT",
        hole=0.60,
        title="FAILURE ROOT CAUSE ANALYSIS",
    )

    failure_root_fig.update_traces(textinfo="label+value+percent")

    failure_root_fig.update_layout(height=450)

    return (
        kpi_cards,
        pie_fig,
        duration_fig,
        failed_fig,
        ts_fig,
        monitor_fig,
        failure_root_fig,
    )


# =========================================================
# TABLE BUTTON CALLBACK
# =========================================================


@app.callback(
    Output("dynamic_table", "children"),
    [
        Input("btn_new", "n_clicks"),
        Input("btn_updated", "n_clicks"),
        Input("btn_full", "n_clicks"),
    ],
)
def show_tables(new_clicks, updated_clicks, full_clicks):
    df = load_data()
    ctx = callback_context

    if not ctx.triggered:
        return ""

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "btn_new":

        table_df = df[["DATE", "TEST ID", "TEST NAME", "STATUS", "DURATION (S)"]]

    elif button_id == "btn_updated":

        table_df = df[df["UPDATED AT"].notna()][
            ["DATE", "UPDATED AT", "TEST ID", "TEST NAME", "STATUS"]
        ]

    else:

        table_df = df.copy()

    return dash_table.DataTable(
        columns=[{"name": i, "id": i} for i in table_df.columns],
        data=table_df.to_dict("records"),
        page_size=15,
        filter_action="native",
        sort_action="native",
        style_table={
            "overflowX": "auto",
            "height": "600px",
            "overflowY": "auto",
            "backgroundColor": "white",
        },
        style_header={
            "backgroundColor": "#dfe6e9",
            "fontWeight": "bold",
            "textAlign": "center",
        },
        style_cell={"textAlign": "center", "padding": "8px", "minWidth": "140px"},
    )


# =========================================================
# RUN APP
# =========================================================

if __name__ == "__main__":

    app.run(debug=True, port=8052)

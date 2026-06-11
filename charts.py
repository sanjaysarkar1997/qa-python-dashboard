"""
charts.py
=========
Contains one builder function for every chart on the dashboard.

Why a separate file?
--------------------
Each chart is self-contained here.  If you want to change only the
"Failed Test" chart, you edit `build_failed_chart()` without touching
any other part of the application.

All charts share:
  • The same `PLOTLY_TEMPLATE` (defined in config.py)
  • The same `STATUS_COLORS` color palette
  • Consistent axis labels, hover tooltips, and font sizes

Functions
---------
build_kpi_cards(df)          → Dash HTML (not a Plotly figure)
build_pie_chart(df)          → Donut — status distribution
build_duration_chart(df)     → Bar — test duration groups
build_failed_chart(df)       → Bar — failed tests per day
build_timeseries_chart(df)   → Line — daily / cumulative trends
build_monitor_chart(df)      → Stacked bar — monitor status breakdown
build_failure_root_chart(df) → Donut — failure root cause
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from dash import html

from config import (
    STATUS_COLORS,
    KPI_CARD_COLORS,
    KPI_TEXT_COLORS,
    PLOTLY_TEMPLATE,
    CHART_HEIGHT_SMALL,
    CHART_HEIGHT_MEDIUM,
    CHART_HEIGHT_LARGE,
)

# ------------------------------------------------------------------
# SHARED LAYOUT DEFAULTS
# ------------------------------------------------------------------
# Reusable layout kwargs applied to every chart for visual consistency.
_BASE_LAYOUT = dict(
    template=PLOTLY_TEMPLATE,
    font=dict(family="Inter, Segoe UI, sans-serif", size=13, color="#2d3436"),
    paper_bgcolor="rgba(0,0,0,0)",   # Transparent background (card handles it)
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=30, r=30, t=55, b=30),
    hoverlabel=dict(
        bgcolor="#1e293b",
        bordercolor="#334155",
        font=dict(family="Inter, Segoe UI, sans-serif", size=13, color="#cbd5e1"),
        align="left",
    ),
)


def _apply_base_layout(fig: go.Figure, **extra_kwargs) -> go.Figure:
    """Helper — merge the base layout with any chart-specific overrides."""
    layout_args = {**_BASE_LAYOUT, **extra_kwargs}
    fig.update_layout(**layout_args)
    return fig


# ------------------------------------------------------------------
# STATUS COLOR HELPER
# ------------------------------------------------------------------

def _status_color(label: str) -> str:
    """
    Return a hex color for a given status label.

    Checks for substring matches so that partial strings like
    "PASS" still match correctly.

    Parameters
    ----------
    label : str
        Status string (e.g. "PASS", "FAIL", "SKIPPED", "BROKEN")

    Returns
    -------
    str
        A hex color string.
    """
    label = str(label).upper()
    if "PASS"   in label: return STATUS_COLORS["PASS"]
    if "FAIL"   in label: return STATUS_COLORS["FAIL"]
    if "SKIP"   in label: return STATUS_COLORS["SKIPPED"]
    if "BROKEN" in label: return STATUS_COLORS["BROKEN"]
    return "#b2bec3"  # Default light grey for unrecognised statuses


# ==================================================================
# 1. KPI CARDS
# ==================================================================

def build_kpi_cards(df: pd.DataFrame) -> html.Div:
    """
    Build the five KPI summary cards shown at the top of the dashboard.

    Each card shows a metric label + count.  The card colors are
    defined in `config.KPI_CARD_COLORS`.

    Parameters
    ----------
    df : pd.DataFrame
        The filtered DataFrame for the selected date range and status.

    Returns
    -------
    dash.html.Div
        A Dash HTML component (not a Plotly figure) containing all cards.
    """
    status_series = df["STATUS"].astype(str).str.upper().str.strip()

    # Count each status type
    metrics = {
        "TOTAL":   len(df),
        "PASS":    status_series.str.contains("PASS",   na=False).sum(),
        "FAIL":    status_series.str.contains("FAIL",   na=False).sum(),
        "SKIPPED": status_series.str.contains("SKIP",   na=False).sum(),
        "BROKEN":  status_series.str.contains("BROKEN", na=False).sum(),
    }

    # Icons for each KPI card
    icons = {
        "TOTAL":   "🧪",
        "PASS":    "✅",
        "FAIL":    "❌",
        "SKIPPED": "⏭️",
        "BROKEN":  "⚠️",
    }

    cards = []
    for label, count in metrics.items():
        bg_color   = KPI_CARD_COLORS[label]
        text_color = KPI_TEXT_COLORS[label]

        card = html.Div(
            [
                # Icon row
                html.Div(
                    icons[label],
                    style={"fontSize": "28px", "marginBottom": "6px"},
                ),
                # Metric label
                html.Div(
                    label,
                    style={
                        "fontSize": "12px",
                        "fontWeight": "600",
                        "letterSpacing": "1.5px",
                        "opacity": "0.9",
                        "marginBottom": "4px",
                    },
                ),
                # Count number (big)
                html.Div(
                    str(count),
                    style={
                        "fontSize": "36px",
                        "fontWeight": "800",
                        "lineHeight": "1.1",
                    },
                ),
            ],
            style={
                "backgroundColor": bg_color,
                "color": text_color,
                "width": "18%",
                "padding": "22px 16px",
                "textAlign": "center",
                "borderRadius": "14px",
                "boxShadow": "0 4px 15px rgba(0,0,0,0.12)",
                "transition": "transform 0.2s ease",
                "cursor": "default",
                "fontFamily": "Inter, Segoe UI, sans-serif",
            },
        )
        cards.append(card)

    return html.Div(
        cards,
        style={
            "display": "flex",
            "justifyContent": "space-between",
            "gap": "14px",
        },
    )


# ==================================================================
# 2. STATUS DISTRIBUTION PIE / DONUT CHART
# ==================================================================

def build_pie_chart(df: pd.DataFrame) -> go.Figure:
    """
    Build the test status distribution donut chart.

    Shows the proportion of PASS / FAIL / SKIPPED / BROKEN tests.
    The center hole (hole=0.5) gives a modern donut appearance.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    plotly.graph_objects.Figure
    """
    # Count each status
    pie_df = df["STATUS"].value_counts().reset_index()
    pie_df.columns = ["STATUS", "COUNT"]

    # Build color list in the same order as the data
    colors = [_status_color(s) for s in pie_df["STATUS"]]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=pie_df["STATUS"],
                values=pie_df["COUNT"],
                hole=0.50,
                marker=dict(colors=colors, line=dict(color="white", width=2)),
                textinfo="label+value+percent",
                textfont=dict(size=12),
                hovertemplate=(
                    "<span style='font-size: 14px; font-weight: bold; color: #38bdf8;'>%{label}</span><br>"
                    "<span style='color: #94a3b8;'>Count:</span> <b>%{value:,}</b><br>"
                    "<span style='color: #94a3b8;'>Share:</span> <b>%{percent}</b><extra></extra>"
                ),
                # Pull the largest slice slightly outward for emphasis
                pull=[0.04 if i == pie_df["COUNT"].idxmax() else 0
                      for i in range(len(pie_df))],
            )
        ]
    )

    fig = _apply_base_layout(
        fig,
        title=dict(text="Test Status Distribution", font=dict(size=16)),
        height=CHART_HEIGHT_SMALL,
        legend=dict(orientation="v", x=1.02, y=0.9, bgcolor="rgba(0,0,0,0)"),
        showlegend=True,
    )

    return fig


# ==================================================================
# 3. DURATION ANALYSIS BAR CHART
# ==================================================================

def build_duration_chart(df: pd.DataFrame) -> go.Figure:
    """
    Build the test execution duration bar chart.

    Tests are grouped into time buckets (0–10 s, 10–20 s, etc.)
    defined in `config.DURATION_LABELS`.  Color intensity represents
    count — darker bars = more tests in that bucket.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    plotly.graph_objects.Figure
    """
    duration_df = (
        df["DURATION GROUP"]
        .value_counts()
        .sort_index()
        .reset_index()
    )
    duration_df.columns = ["DURATION RANGE", "COUNT"]

    fig = px.bar(
        duration_df,
        x="DURATION RANGE",
        y="COUNT",
        text="COUNT",
        color="COUNT",
        color_continuous_scale=["#74b9ff", "#0984e3", "#1e3799"],  # Blue gradient
        title="Test Execution Duration",
    )

    fig.update_traces(
        textposition="outside",
        textfont=dict(size=12, color="#2d3436"),
        marker_line_width=0,
        hovertemplate=(
            "<span style='font-size: 14px; font-weight: bold; color: #38bdf8;'>%{x}</span><br>"
            "<span style='color: #94a3b8;'>Tests:</span> <b>%{y:,}</b><extra></extra>"
        ),
    )

    fig.update_coloraxes(showscale=False)  # Hide the colour legend bar

    fig = _apply_base_layout(
        fig,
        title=dict(text="Test Execution Duration", font=dict(size=16)),
        height=CHART_HEIGHT_MEDIUM,
        xaxis=dict(title="Duration Range", tickfont=dict(size=11)),
        yaxis=dict(title="Number of Tests", gridcolor="#f1f2f6"),
    )

    return fig


# ==================================================================
# 4. FAILED TESTS PER DAY BAR CHART
# ==================================================================

def build_failed_chart(df: pd.DataFrame) -> go.Figure:
    """
    Build the daily failed test count bar chart.

    Filters to only FAIL records, then groups by DATE to show how
    many tests failed on each day.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    plotly.graph_objects.Figure
    """
    failed_df = df[df["STATUS"].astype(str).str.contains("FAIL", na=False)]
    failed_group = failed_df.groupby("DATE").size().reset_index(name="FAILED COUNT")

    fig = px.bar(
        failed_group,
        x="DATE",
        y="FAILED COUNT",
        text="FAILED COUNT",
        title="Failed Tests Per Day",
        color="FAILED COUNT",
        color_continuous_scale=["#ff7675", "#d63031", "#6d0000"],  # Red gradient
    )

    fig.update_traces(
        textposition="outside",
        textfont=dict(size=12, color="#2d3436"),
        marker_line_width=0,
        hovertemplate=(
            "<span style='font-size: 14px; font-weight: bold; color: #f87171;'>%{x}</span><br>"
            "<span style='color: #94a3b8;'>Failed:</span> <b>%{y:,}</b><extra></extra>"
        ),
    )

    fig.update_coloraxes(showscale=False)

    fig = _apply_base_layout(
        fig,
        title=dict(text="Failed Tests Per Day", font=dict(size=16)),
        height=CHART_HEIGHT_MEDIUM,
        xaxis=dict(title="Date", tickfont=dict(size=11)),
        yaxis=dict(title="Failed Count", gridcolor="#f1f2f6"),
    )

    return fig


# ==================================================================
# 5. DAILY TEST TREND (TIMESERIES) LINE CHART
# ==================================================================

def build_timeseries_chart(df: pd.DataFrame) -> go.Figure:
    """
    Build the multi-line daily test trend chart.

    Three lines:
      • Total Tests (cumulative)   — blue
      • New Tests per day          — green
      • Updated Tests per day      — orange

    Using smooth spline interpolation + a filled area beneath each
    line for a polished look.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    plotly.graph_objects.Figure
    """
    # Daily total tests
    daily_total = df.groupby("DATE").size().reset_index(name="DAILY TESTS")
    all_dates = daily_total["DATE"]

    # New tests per day (records where CREATED AT date matches the execution DATE)
    new_df = df[df["CREATED AT"].dt.date == df["DATE"]]
    new_counts = new_df.groupby("DATE").size()
    new_tests = new_counts.reindex(all_dates, fill_value=0).reset_index(name="NEW TESTS")

    # Updated tests per day (records where UPDATED AT date matches the execution DATE)
    updated_df = df[df["UPDATED AT"].dt.date == df["DATE"]]
    updated_counts = updated_df.groupby("DATE").size()
    updated_tests = updated_counts.reindex(all_dates, fill_value=0).reset_index(name="UPDATED TESTS")

    fig = go.Figure()

    # --- Line 1: Daily total tests ---
    fig.add_trace(
        go.Scatter(
            x=daily_total["DATE"],
            y=daily_total["DAILY TESTS"],
            mode="lines+markers",
            name="Total Tests (Daily)",
            line=dict(color="#0984e3", width=3, shape="spline"),
            fill="tozeroy",
            fillcolor="rgba(9,132,227,0.08)",
            marker=dict(size=7, color="#0984e3"),
            hovertemplate=(
                "<span style='font-size: 14px; font-weight: bold; color: #38bdf8;'>%{x}</span><br>"
                "<span style='color: #94a3b8;'>Total Tests:</span> <b>%{y:,}</b><extra></extra>"
            ),
        )
    )

    # --- Line 2: New tests per day ---
    fig.add_trace(
        go.Scatter(
            x=new_tests["DATE"],
            y=new_tests["NEW TESTS"],
            mode="lines+markers",
            name="New Tests (Daily)",
            line=dict(color="#00b894", width=2.5, shape="spline", dash="dot"),
            marker=dict(size=7, color="#00b894"),
            hovertemplate=(
                "<span style='font-size: 14px; font-weight: bold; color: #34d399;'>%{x}</span><br>"
                "<span style='color: #94a3b8;'>New Tests:</span> <b>%{y:,}</b><extra></extra>"
            ),
        )
    )

    # --- Line 3: Updated tests per day ---
    if not updated_tests.empty:
        fig.add_trace(
            go.Scatter(
                x=updated_tests["DATE"],
                y=updated_tests["UPDATED TESTS"],
                mode="lines+markers",
                name="Updated Tests (Daily)",
                line=dict(color="#e17055", width=2.5, shape="spline", dash="dash"),
                marker=dict(size=7, color="#e17055"),
                hovertemplate=(
                    "<span style='font-size: 14px; font-weight: bold; color: #fb923c;'>%{x}</span><br>"
                    "<span style='color: #94a3b8;'>Updated Tests:</span> <b>%{y:,}</b><extra></extra>"
                ),
            )
        )

    fig = _apply_base_layout(
        fig,
        title=dict(text="Daily Test Trend", font=dict(size=16)),
        height=CHART_HEIGHT_LARGE,
        xaxis=dict(title="Date", gridcolor="#f1f2f6"),
        yaxis=dict(title="Count", gridcolor="#f1f2f6"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0)",
        ),
    )

    return fig


# ==================================================================
# 6. MONITOR STATUS STACKED BAR CHART
# ==================================================================

def build_monitor_chart(df: pd.DataFrame) -> go.Figure:
    """
    Build the stacked bar chart for HIGH / CRITICAL / MONITOR CLOSELY tests.

    Each bar represents a monitor priority level (x-axis), stacked by
    test STATUS (color).  This helps QA leads quickly see which
    high-priority tests are failing.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    plotly.graph_objects.Figure
    """
    # Filter only the priority categories we care about
    priority_levels = ["HIGH", "CRITICAL", "MONITOR CLOSELY"]
    monitor_df = df[df["MONITOR STATUS"].isin(priority_levels)]

    if monitor_df.empty:
        # Return an empty placeholder figure with a friendly message
        fig = go.Figure()
        fig.add_annotation(
            text="No HIGH / CRITICAL / MONITOR CLOSELY data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="#636e72"),
        )
        return _apply_base_layout(
            fig,
            title=dict(text="Monitor Status Breakdown", font=dict(size=16)),
            height=CHART_HEIGHT_LARGE,
        )

    monitor_group = (
        monitor_df
        .groupby(["MONITOR STATUS", "STATUS"])
        .size()
        .reset_index(name="COUNT")
    )

    # Build color map for whatever status values actually appear
    color_map = {s: _status_color(s) for s in monitor_group["STATUS"].unique()}

    fig = px.bar(
        monitor_group,
        x="MONITOR STATUS",
        y="COUNT",
        color="STATUS",
        text="COUNT",
        barmode="stack",
        color_discrete_map=color_map,
        category_orders={"MONITOR STATUS": priority_levels},
    )

    fig.update_traces(
        textposition="inside",
        textfont=dict(size=12, color="white"),
        hovertemplate=(
            "<span style='font-size: 14px; font-weight: bold; color: #38bdf8;'>%{x}</span><br>"
            "<span style='color: #94a3b8;'>Status:</span> <b>%{fullData.name}</b><br>"
            "<span style='color: #94a3b8;'>Count:</span> <b>%{y:,}</b><extra></extra>"
        ),
    )

    fig = _apply_base_layout(
        fig,
        title=dict(text="Monitor Status Breakdown", font=dict(size=16)),
        height=CHART_HEIGHT_LARGE,
        xaxis=dict(title="Priority Level"),
        yaxis=dict(title="Test Count", gridcolor="#f1f2f6"),
        legend=dict(title="Status", bgcolor="rgba(0,0,0,0)"),
    )

    return fig


# ==================================================================
# 7. FAILURE ROOT CAUSE DONUT CHART
# ==================================================================

def build_failure_root_chart(df: pd.DataFrame) -> go.Figure:
    """
    Build the failure root cause donut chart.

    Filters to only failed tests, then groups by the FAILURE ROOT CAUSE
    column to show what proportion of failures share each root cause.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    plotly.graph_objects.Figure
    """
    failed_df = df[df["STATUS"].astype(str).str.contains("FAIL", na=False)]

    # Drop rows where root cause is the placeholder em-dash or empty
    root_df = failed_df[
        failed_df["FAILURE ROOT CAUSE"].notna()
        & (failed_df["FAILURE ROOT CAUSE"].astype(str).str.strip() != "—")
        & (failed_df["FAILURE ROOT CAUSE"].astype(str).str.strip() != "")
    ]

    if root_df.empty:
        # Friendly empty state
        fig = go.Figure()
        fig.add_annotation(
            text="No failure root cause data available for this date range",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="#636e72"),
        )
        return _apply_base_layout(
            fig,
            title=dict(text="Failure Root Cause Analysis", font=dict(size=16)),
            height=CHART_HEIGHT_LARGE,
        )

    root_group = (
        root_df.groupby("FAILURE ROOT CAUSE")
        .size()
        .reset_index(name="FAILED COUNT")
        .sort_values("FAILED COUNT", ascending=False)
    )

    # Use a rich qualitative palette for the root cause slices
    PALETTE = [
        "#d63031", "#e17055", "#fdcb6e", "#6c5ce7",
        "#0984e3", "#00b894", "#fd79a8", "#00cec9",
        "#2d3436", "#636e72",
    ]
    colors = [PALETTE[i % len(PALETTE)] for i in range(len(root_group))]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=root_group["FAILURE ROOT CAUSE"],
                values=root_group["FAILED COUNT"],
                hole=0.60,
                marker=dict(colors=colors, line=dict(color="white", width=2)),
                textinfo="label+value+percent",
                textfont=dict(size=11),
                hovertemplate=(
                    "<span style='font-size: 14px; font-weight: bold; color: #f87171;'>%{label}</span><br>"
                    "<span style='color: #94a3b8;'>Failures:</span> <b>%{value:,}</b><br>"
                    "<span style='color: #94a3b8;'>Share:</span> <b>%{percent}</b><extra></extra>"
                ),
            )
        ]
    )

    # Add a centered annotation inside the donut hole
    fig.add_annotation(
        text=f"<b>{root_group['FAILED COUNT'].sum():,}</b><br><span style='font-size:11px'>Failures</span>",
        x=0.5, y=0.5,
        xref="paper", yref="paper",
        showarrow=False,
        font=dict(size=16, color="#d63031"),
    )

    fig = _apply_base_layout(
        fig,
        title=dict(text="Failure Root Cause Analysis", font=dict(size=16)),
        height=CHART_HEIGHT_LARGE,
        legend=dict(
            orientation="v",
            x=1.02,
            y=0.9,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11),
        ),
        showlegend=True,
    )

    return fig

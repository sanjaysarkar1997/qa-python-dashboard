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
    font=dict(family="Inter, Segoe UI, sans-serif", size=12, color="#2d3436"),
    paper_bgcolor="rgba(0,0,0,0)",  # Transparent background (card handles it)
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
    if "PASS" in label:
        return STATUS_COLORS["PASS"]
    if "FAIL" in label:
        return STATUS_COLORS["FAIL"]
    if "SKIP" in label:
        return STATUS_COLORS["SKIPPED"]
    if "BROKEN" in label:
        return STATUS_COLORS["BROKEN"]
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
        "TOTAL": len(df),
        "PASS": status_series.str.contains("PASS", na=False).sum(),
        "FAIL": status_series.str.contains("FAIL", na=False).sum(),
        "SKIPPED": status_series.str.contains("SKIP", na=False).sum(),
        "BROKEN": status_series.str.contains("BROKEN", na=False).sum(),
    }

    # Icons for each KPI card
    icons = {
        "TOTAL": "🧪",
        "PASS": "✅",
        "FAIL": "❌",
        "SKIPPED": "⏭️",
        "BROKEN": "⚠️",
    }

    cards = []
    for label, count in metrics.items():
        bg_color = KPI_CARD_COLORS[label]
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
                pull=[
                    0.04 if i == pie_df["COUNT"].idxmax() else 0
                    for i in range(len(pie_df))
                ],
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
    duration_df = df["DURATION GROUP"].value_counts().sort_index().reset_index()
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
    Build the daily failed test count stacked bar chart (API vs UI).

    Filters to only FAIL records, then groups by DATE and TEST TYPE to show how
    many tests of each type failed on each day.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    plotly.graph_objects.Figure
    """
    from config import SLA_THRESHOLD

    failed_df = df[df["STATUS"].astype(str).str.contains("FAIL", na=False)]
    
    unique_dates = sorted(df["DATE"].dropna().unique())
    
    fig = go.Figure()

    # Define the colors for the test types
    colors = {
        "API": "#7f0000",   # Deep maroon / dark red
        "UI": "#ff7675",    # Light coral / pastel red
    }
    
    # We support API and UI; check what types actually exist in failed_df
    found_types = failed_df["TEST TYPE"].dropna().unique() if not failed_df.empty else []
    # Order them nicely (API first, then UI, then others)
    test_types = [t for t in ["API", "UI"] if t in found_types]
    for t in found_types:
        if t not in test_types:
            test_types.append(t)
            
    # If there are no failures at all, we still show the unique dates on the x-axis with 0 counts
    if failed_df.empty or len(test_types) == 0:
        fig.add_trace(
            go.Bar(
                x=unique_dates,
                y=[0] * len(unique_dates),
                text=[""] * len(unique_dates),
                textposition="outside",
                textfont=dict(size=12, color="#2d3436"),
                marker=dict(color="#d63031"),
                name="Failed Tests",
                hovertemplate=(
                    "<span style='font-size: 14px; font-weight: bold; color: #f87171;'>%{x}</span><br>"
                    "<span style='color: #94a3b8;'>Failed:</span> <b>0</b><extra></extra>"
                ),
            )
        )
    else:
        for ttype in test_types:
            type_df = failed_df[failed_df["TEST TYPE"] == ttype]
            type_counts = type_df.groupby("DATE").size()
            y_values = [type_counts.get(d, 0) for d in unique_dates]
            
            # Show text label inside/outside the bar segment if it is non-zero
            text_values = [str(val) if val > 0 else "" for val in y_values]
            
            color_val = colors.get(ttype, "#b2bec3")
            
            fig.add_trace(
                go.Bar(
                    x=unique_dates,
                    y=y_values,
                    text=text_values,
                    textposition="auto",
                    textfont=dict(size=12, color="white" if ttype in colors else "#2d3436"),
                    marker=dict(color=color_val),
                    name=f"{ttype} Failures",
                    hovertemplate=(
                        f"<span style='font-size: 14px; font-weight: bold; color: {color_val};'>%{{x}}</span><br>"
                        f"<span style='color: #94a3b8;'>{ttype} Failed:</span> <b>%{{y:,}}</b><extra></extra>"
                    ),
                )
            )

    # Add horizontal dashed SLA threshold line
    if unique_dates:
        min_date = min(unique_dates)
        max_date = max(unique_dates)
        fig.add_trace(
            go.Scatter(
                x=[min_date, max_date],
                y=[SLA_THRESHOLD, SLA_THRESHOLD],
                mode="lines",
                name="SLA Threshold",
                line=dict(color="#2d3436", width=2, dash="dash"),
                hovertemplate="SLA Threshold: %{y}<extra></extra>",
            )
        )

    fig = _apply_base_layout(
        fig,
        title=dict(text="Failed Tests Per Day", font=dict(size=16)),
        height=CHART_HEIGHT_MEDIUM,
        xaxis=dict(title="Date", tickfont=dict(size=11)),
        yaxis=dict(title="Failed Count", gridcolor="#f1f2f6"),
        barmode="stack",
        showlegend=True,
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

    # Ensure test IDs are filled and normalized (fallback to test name if empty/missing)
    clean_df = df.copy()
    clean_df["TEST ID"] = clean_df["TEST ID"].fillna("").astype(str).str.strip()
    clean_df["TEST ID"] = clean_df.apply(
        lambda r: r["TEST ID"] if r["TEST ID"] != "" else r["TEST NAME"], axis=1
    )

    # Keep only the latest occurrence of each unique test case (sorted by START TIME)
    # to get the most up-to-date CREATED AT and UPDATED AT metadata.
    unique_df = clean_df.sort_values("START TIME").drop_duplicates(
        subset=["TEST ID"], keep="last"
    )

    # New tests per day (grouped by their actual CREATED AT date)
    new_df = unique_df[unique_df["CREATED AT"].notna()]
    new_counts = new_df.groupby(new_df["CREATED AT"].dt.date).size()
    new_tests = new_counts.reindex(all_dates, fill_value=0).reset_index(
        name="NEW TESTS"
    )

    # Updated tests per day (grouped by their actual UPDATED AT date)
    updated_df = unique_df[unique_df["UPDATED AT"].notna()]
    updated_counts = updated_df.groupby(updated_df["UPDATED AT"].dt.date).size()
    updated_tests = updated_counts.reindex(all_dates, fill_value=0).reset_index(
        name="UPDATED TESTS"
    )

    fig = go.Figure()

    # --- Line 1: Total Tests ---
    fig.add_trace(
        go.Scatter(
            x=daily_total["DATE"],
            y=daily_total["DAILY TESTS"],
            mode="lines+markers",
            name="Total Tests",
            line=dict(color="#378ADD", width=3, shape="spline"),  # solid blue
            marker=dict(size=7, color="#378ADD"),
            hovertemplate=(
                "<span style='font-size: 14px; font-weight: bold; color: #38bdf8;'>%{x}</span><br>"
                "<span style='color: #94a3b8;'>Total Tests:</span> <b>%{y:,}</b><extra></extra>"
            ),
        )
    )

    # --- Line 2: New Tests ---
    fig.add_trace(
        go.Scatter(
            x=new_tests["DATE"],
            y=new_tests["NEW TESTS"],
            mode="lines+markers",
            name="New Tests",
            line=dict(
                color="#00b894", width=2.5, shape="spline", dash="dash"
            ),  # dashed teal
            marker=dict(size=8, color="#00b894", symbol="square"),
            hovertemplate=(
                "<span style='font-size: 14px; font-weight: bold; color: #34d399;'>%{x}</span><br>"
                "<span style='color: #94a3b8;'>New Tests:</span> <b>%{y:,}</b><extra></extra>"
            ),
        )
    )

    # --- Line 3: Updated Tests ---
    fig.add_trace(
        go.Scatter(
            x=updated_tests["DATE"],
            y=updated_tests["UPDATED TESTS"],
            mode="lines+markers",
            name="Updated Tests",
            line=dict(
                color="#E24B4A", width=2.5, shape="spline", dash="dash"
            ),  # dashed red
            marker=dict(size=8, color="#E24B4A", symbol="diamond"),
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
        yaxis=dict(title="Test Count", gridcolor="#f1f2f6"),
        hovermode="x",
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
    Build the stacked bar chart for monitor status breakdown by environment.

    Each bar represents a derived environment (x-axis), stacked by
    test STATUS (color).

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    plotly.graph_objects.Figure
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14, color="#636e72"),
        )
        return _apply_base_layout(
            fig,
            title=dict(text="Monitor Status Breakdown", font=dict(size=16)),
            height=CHART_HEIGHT_LARGE,
        )

    # Group by derived ENV and STATUS
    monitor_group = df.groupby(["ENV", "STATUS"]).size().reset_index(name="COUNT")

    # Color map mapping STATUS to hex colors: PASS -> #1D9E75, FAIL -> #E24B4A
    color_map = {
        "PASS": "#1D9E75",
        "FAIL": "#E24B4A",
        "SKIPPED": "#fdcb6e",  # standard warm amber
        "BROKEN": "#6c5ce7",  # standard violet
    }

    fig = px.bar(
        monitor_group,
        x="ENV",
        y="COUNT",
        color="STATUS",
        text="COUNT",
        barmode="stack",
        color_discrete_map=color_map,
        category_orders={"ENV": sorted(monitor_group["ENV"].unique())},
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
        xaxis=dict(title="Environment"),
        yaxis=dict(title="Test Count", gridcolor="#f1f2f6"),
        legend=dict(title="Status", bgcolor="rgba(0,0,0,0)"),
    )

    return fig


# ==================================================================
# 7. FAILURE ROOT CAUSE DONUT CHART
# ==================================================================


def build_failure_root_chart(df: pd.DataFrame) -> go.Figure:
    """
    Build the failure root cause horizontal bar chart.

    Filters to only failed tests, then groups by the FAILURE ROOT CAUSE
    column to show why tests failed.

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
            text="No failure root cause data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
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
        .sort_values(
            "FAILED COUNT", ascending=True
        )  # Sort ascending so largest is at the top of the horizontal chart!
    )

    fig = go.Figure(
        data=[
            go.Bar(
                x=root_group["FAILED COUNT"],
                y=root_group["FAILURE ROOT CAUSE"],
                orientation="h",
                text=root_group["FAILED COUNT"],
                textposition="outside",
                textfont=dict(size=12, color="#2d3436"),
                marker=dict(
                    color=root_group["FAILED COUNT"],
                    colorscale=[
                        "#ffb3b3",
                        "#ff7675",
                        "#E24B4A",
                        "#b32d2c",
                    ],  # red color ramp
                    showscale=False,
                ),
                hovertemplate=(
                    "<span style='font-size: 14px; font-weight: bold; color: #f87171;'>%{y}</span><br>"
                    "<span style='color: #94a3b8;'>Failures:</span> <b>%{x:,}</b><extra></extra>"
                ),
            )
        ]
    )

    fig = _apply_base_layout(
        fig,
        title=dict(text="Failure Root Cause Analysis", font=dict(size=16)),
        height=CHART_HEIGHT_LARGE,
        xaxis=dict(title="Failure Count", gridcolor="#f1f2f6"),
        yaxis=dict(title="Root Cause"),
    )

    return fig


# ==================================================================
# 8. ENVIRONMENT BREAKDOWN TABLE
# ==================================================================


def build_environment_table(
    df_single: pd.DataFrame, df_trend: pd.DataFrame
) -> html.Div:
    """
    Build the Environment Breakdown custom HTML table.

    Includes conditional Pass Rate styling and mini sparkline bar charts
    representing pass rates over the 11-day trend window.
    """
    from config import SLA_TARGET, FONT_FAMILY

    # Unique environments present in the dataset
    all_envs = sorted(list(set(df_trend["ENV"].dropna().unique())))

    # Preferred sorting order for environments
    envs_order = ["Rbac", "API", "UI", "Invoice", "Platform", "Tenant", "Company"]
    preferred_order = {env: i for i, env in enumerate(envs_order)}
    all_envs = sorted(all_envs, key=lambda e: preferred_order.get(e, 99))

    rows = []
    trend_dates = sorted(df_trend["DATE"].dropna().unique())

    for env in all_envs:
        # Single day metrics
        env_single = df_single[df_single["ENV"] == env]
        total = len(env_single)
        passed = len(env_single[env_single["STATUS"] == "PASS"])
        failed = len(env_single[env_single["STATUS"] == "FAIL"])

        pass_rate = (passed / total * 100) if total > 0 else 0.0

        # Determine pass rate color
        if pass_rate >= SLA_TARGET:
            pr_color = "#1D9E75"  # Green
        elif pass_rate >= 60.0:
            pr_color = "#E67E22"  # Amber (60–94%)
        else:
            pr_color = "#E24B4A"  # Red (<60%)

        # Build trend array (chronological pass rates)
        trend_bars = []
        for d in trend_dates:
            env_day = df_trend[(df_trend["ENV"] == env) & (df_trend["DATE"] == d)]
            d_total = len(env_day)
            d_passed = len(env_day[env_day["STATUS"] == "PASS"])
            d_rate = (d_passed / d_total * 100) if d_total > 0 else 100.0

            # Determine color for this individual bar
            if d_rate >= SLA_TARGET:
                bar_color = "#1D9E75"
            elif d_rate >= 60.0:
                bar_color = "#E67E22"
            else:
                bar_color = "#E24B4A"

            # Height: scale 0-100% to 0-22px
            bar_height = max(2, int(d_rate * 0.22))

            trend_bars.append(
                html.Div(
                    style={
                        "backgroundColor": bar_color,
                        "width": "4px",
                        "height": f"{bar_height}px",
                        "marginRight": "2px",
                        "borderRadius": "1px",
                    },
                    title=f"{d}: {d_rate:.1f}% Pass Rate ({d_passed}/{d_total})",
                )
            )

        sparkline = html.Div(
            trend_bars,
            style={
                "display": "flex",
                "alignItems": "flex-end",
                "height": "22px",
                "justifyContent": "center",
            },
        )

        rows.append(
            html.Tr(
                [
                    html.Td(
                        env,
                        style={
                            "textAlign": "left",
                            "fontWeight": "600",
                            "padding": "12px 16px",
                        },
                    ),
                    html.Td(f"{total:,}", style={"padding": "12px 16px"}),
                    html.Td(
                        f"{passed:,}",
                        style={
                            "color": "#1D9E75",
                            "fontWeight": "600",
                            "padding": "12px 16px",
                        },
                    ),
                    html.Td(
                        f"{failed:,}",
                        style={
                            "color": "#E24B4A",
                            "fontWeight": "600",
                            "padding": "12px 16px",
                        },
                    ),
                    html.Td(
                        f"{pass_rate:.1f}%",
                        style={
                            "color": pr_color,
                            "fontWeight": "700",
                            "padding": "12px 16px",
                        },
                    ),
                    html.Td(sparkline, style={"padding": "12px 16px"}),
                ],
                style={
                    "borderBottom": "1px solid #f1f2f6",
                    "transition": "background-color 0.15s ease",
                },
            )
        )

    table = html.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th(
                            "Environment",
                            style={
                                "textAlign": "left",
                                "padding": "12px 16px",
                                "backgroundColor": "#f8f9fa",
                                "color": "#2d3436",
                                "borderTopLeftRadius": "8px",
                                "borderBottomLeftRadius": "8px",
                            },
                        ),
                        html.Th(
                            "Total Tests",
                            style={
                                "padding": "12px 16px",
                                "backgroundColor": "#f8f9fa",
                                "color": "#2d3436",
                            },
                        ),
                        html.Th(
                            "Passed",
                            style={
                                "padding": "12px 16px",
                                "backgroundColor": "#f8f9fa",
                                "color": "#2d3436",
                            },
                        ),
                        html.Th(
                            "Failed",
                            style={
                                "padding": "12px 16px",
                                "backgroundColor": "#f8f9fa",
                                "color": "#2d3436",
                            },
                        ),
                        html.Th(
                            "Pass Rate",
                            style={
                                "padding": "12px 16px",
                                "backgroundColor": "#f8f9fa",
                                "color": "#2d3436",
                            },
                        ),
                        html.Th(
                            "11-Day Trend",
                            style={
                                "padding": "12px 16px",
                                "backgroundColor": "#f8f9fa",
                                "color": "#2d3436",
                                "borderTopRightRadius": "8px",
                                "borderBottomRightRadius": "8px",
                            },
                        ),
                    ]
                )
            ),
            html.Tbody(rows),
        ],
        style={
            "width": "100%",
            "borderCollapse": "collapse",
            "fontFamily": FONT_FAMILY,
            "fontSize": "13px",
            "textAlign": "center",
        },
    )

    return html.Div(
        [
            html.Div(
                "Environment Breakdown",
                style={
                    "fontSize": "15px",
                    "fontWeight": "700",
                    "marginBottom": "14px",
                    "color": "#2d3436",
                    "letterSpacing": "0.5px",
                },
            ),
            table,
        ],
        style={
            "backgroundColor": "white",
            "borderRadius": "16px",
            "boxShadow": "0 2px 12px rgba(0,0,0,0.07)",
            "padding": "20px",
            "marginBottom": "16px",
        },
    )


# ==================================================================
# 9. MODULE / SQUAD BREAKDOWN CHART
# ==================================================================


def build_module_chart(df: pd.DataFrame) -> go.Figure:
    """
    Build the Module / Squad Breakdown horizontal bar chart.

    Counts failures per module, sorts descending, and applies colors based
    on failure count: Red (>40), Amber (20-40), Green (<20).
    """
    failed_df = df[df["STATUS"] == "FAIL"]

    if failed_df.empty:
        # Return friendly empty state
        fig = go.Figure()
        fig.add_annotation(
            text="No failed tests available to display Module breakdown",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14, color="#636e72"),
        )
        return _apply_base_layout(
            fig,
            title=dict(text="Module / Squad Breakdown (Failures)", font=dict(size=16)),
            height=CHART_HEIGHT_MEDIUM,
        )

    # Group by MOD and count failures
    module_group = (
        failed_df.groupby("MOD")
        .size()
        .reset_index(name="FAILURES")
        .sort_values(
            "FAILURES", ascending=True
        )  # Sort ascending so largest is at the top of the horizontal chart!
    )

    # Determine colors: Red when failures > 40, Amber when 20-40, Green when < 20
    colors = []
    for count in module_group["FAILURES"]:
        if count > 40:
            colors.append("#E24B4A")  # Red
        elif count >= 20:
            colors.append("#E67E22")  # Amber
        else:
            colors.append("#1D9E75")  # Green

    fig = go.Figure(
        data=[
            go.Bar(
                x=module_group["FAILURES"],
                y=module_group["MOD"],
                orientation="h",
                text=module_group["FAILURES"],
                textposition="outside",
                textfont=dict(size=12, color="#2d3436"),
                marker=dict(color=colors),
                hovertemplate=(
                    "<span style='font-size: 14px; font-weight: bold; color: #f87171;'>%{y}</span><br>"
                    "<span style='color: #94a3b8;'>Failures:</span> <b>%{x}</b><extra></extra>"
                ),
            )
        ]
    )

    fig = _apply_base_layout(
        fig,
        title=dict(text="Module / Squad Breakdown (Failures)", font=dict(size=16)),
        height=CHART_HEIGHT_MEDIUM,
        xaxis=dict(title="Failure Count", gridcolor="#f1f2f6"),
        yaxis=dict(title="Module Name"),
    )

    return fig

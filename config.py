"""
config.py
=========
Central configuration file for the QA Analytics Dashboard.

All constants (colors, paths, chart settings) are stored here so that
an intern only needs to change this one file to tweak behavior across
the entire dashboard.

How to use:
    from config import STATUS_COLORS, REPORTS_FOLDER, PORT
"""

import os

# ------------------------------------------------------------------
# REPORTS FOLDER
# ------------------------------------------------------------------
# Path (relative to app.py) where all test-summary CSV files live.
# The dashboard will auto-discover every *.csv file in this folder.
# Just drop a new CSV in and restart the app — it will be picked up.
REPORTS_FOLDER = os.path.join(os.path.dirname(__file__), "reports")

# ------------------------------------------------------------------
# APP SERVER SETTINGS
# ------------------------------------------------------------------
PORT = 8052          # Port the Dash app will run on
DEBUG = True         # Set to False in production

# ------------------------------------------------------------------
# AUTO-REFRESH INTERVAL
# ------------------------------------------------------------------
# How often (in milliseconds) the dashboard polls for new data.
# 60000 ms = 60 seconds
REFRESH_INTERVAL_MS = 60_000

# ------------------------------------------------------------------
# STATUS COLOR MAP
# ------------------------------------------------------------------
# Maps cleaned status values (PASS / FAIL / SKIP / BROKEN) to
# specific hex colors used consistently across all charts and KPI cards.
STATUS_COLORS = {
    "PASS":    "#00b894",   # Emerald green
    "FAIL":    "#d63031",   # Vivid red
    "SKIPPED": "#fdcb6e",   # Warm amber
    "BROKEN":  "#6c5ce7",   # Rich violet
}

# ------------------------------------------------------------------
# KPI CARD GRADIENT COLORS
# ------------------------------------------------------------------
# Each card gets a start → end gradient so they look premium.
KPI_CARD_GRADIENTS = {
    "TOTAL":   ("from", "#636e72", "#b2bec3"),   # Cool grey
    "PASS":    ("from", "#00b894", "#00cec9"),   # Green → teal
    "FAIL":    ("from", "#d63031", "#e17055"),   # Red → coral
    "SKIPPED": ("from", "#f9ca24", "#f0932b"),   # Yellow → orange
    "BROKEN":  ("from", "#6c5ce7", "#a29bfe"),   # Violet → lavender
}

# Simple solid colors for KPI card backgrounds (used as inline style)
KPI_CARD_COLORS = {
    "TOTAL":   "#636e72",
    "PASS":    "#00b894",
    "FAIL":    "#d63031",
    "SKIPPED": "#f9ca24",
    "BROKEN":  "#6c5ce7",
}

# Text color override per card (yellow card needs dark text)
KPI_TEXT_COLORS = {
    "TOTAL":   "white",
    "PASS":    "white",
    "FAIL":    "white",
    "SKIPPED": "#2d3436",   # Dark text on yellow
    "BROKEN":  "white",
}

# ------------------------------------------------------------------
# FONT
# ------------------------------------------------------------------
FONT_FAMILY = "Inter, Segoe UI, Arial, sans-serif"

# ------------------------------------------------------------------
# PLOTLY CHART TEMPLATE
# ------------------------------------------------------------------
# Changing this one string switches every chart's look simultaneously.
# Options: "plotly_white", "plotly_dark", "ggplot2", "seaborn", etc.
PLOTLY_TEMPLATE = "plotly_white"

# ------------------------------------------------------------------
# DURATION BINS
# ------------------------------------------------------------------
# Tests are grouped by how long they took (in seconds).
# Add more ranges here if needed — just add to both lists.
DURATION_BINS = [0, 10, 20, 30, 40, 50, 60, 100_000]
DURATION_LABELS = [
    "0–10 s",
    "10–20 s",
    "20–30 s",
    "30–40 s",
    "40–50 s",
    "50–60 s",
    "60+ s",
]

# ------------------------------------------------------------------
# CHART HEIGHT DEFAULTS (pixels)
# ------------------------------------------------------------------
CHART_HEIGHT_SMALL  = 380   # Pie / donut charts
CHART_HEIGHT_MEDIUM = 430   # Bar charts
CHART_HEIGHT_LARGE  = 460   # Monitor / timeseries charts

# ------------------------------------------------------------------
# TABLE SETTINGS
# ------------------------------------------------------------------
TABLE_PAGE_SIZE = 15   # Rows shown per page in the data table

# ------------------------------------------------------------------
# SLA SETTINGS
# ------------------------------------------------------------------
SLA_THRESHOLD = 30     # Max acceptable failed tests per day
SLA_TARGET = 95        # Target environment pass rate (%)

"""
config.py
=========
Central configuration file for the QA Analytics Dashboard.

All environment-specific values (paths, ports, URLs) are loaded from
a .env file via python-dotenv.  Purely visual constants (colors, chart
settings) remain here as code.

Required .env variables
-----------------------
  DASHBOARD_PORT          Port the Dash app will run on
  DASHBOARD_DEBUG         "true" or "false"
  REPORTS_FOLDER          Absolute path to the CSV reports folder
  RUN_TEST_SERVER_URL     URL for the run-test-server (e.g. http://localhost:4000)
  ALLURE_REPORT_URL       URL for the Allure report viewer

The app raises a ValueError at startup if ANY required variable is missing.

Usage:
    from config import STATUS_COLORS, REPORTS_FOLDER, PORT
"""

import os

from dotenv import load_dotenv

# ------------------------------------------------------------------
# LOAD .env
# ------------------------------------------------------------------
# override=False means already-set environment variables win over .env
load_dotenv(override=False)


# ------------------------------------------------------------------
# INTERNAL HELPER
# ------------------------------------------------------------------

def _require_env(name: str) -> str:
    """
    Return the value of environment variable *name*.

    Raises
    ------
    ValueError
        Immediately, with a clear message, if the variable is not set
        or is an empty string.  No fallback values are provided.
    """
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(
            f"\n\n  [config] Missing required environment variable: {name!r}\n"
            f"  Please add it to your .env file.  See .env.example for reference.\n"
        )
    return value


# ------------------------------------------------------------------
# APP SERVER SETTINGS  (from .env — required)
# ------------------------------------------------------------------
PORT  = int(_require_env("DASHBOARD_PORT"))
DEBUG = _require_env("DASHBOARD_DEBUG").lower() == "true"

# ------------------------------------------------------------------
# REPORTS FOLDER  (from .env — required)
# ------------------------------------------------------------------
# Absolute path to the folder that contains all test-summary CSV files.
# The dashboard auto-discovers every *.csv file inside this folder.
REPORTS_FOLDER = _require_env("REPORTS_FOLDER")

# ------------------------------------------------------------------
# EXTERNAL SERVICE URLs  (from .env — required)
# ------------------------------------------------------------------
RUN_TEST_SERVER_URL = _require_env("RUN_TEST_SERVER_URL")
ALLURE_REPORT_URL   = _require_env("ALLURE_REPORT_URL")

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

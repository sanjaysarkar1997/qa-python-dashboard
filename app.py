"""
app.py
======
Entry point for the QA Analytics Dashboard.

How to run:
    python app.py

Then open your browser at:
    http://127.0.0.1:8052

Project Structure:
------------------
    app.py          ← YOU ARE HERE — starts the server
    config.py       ← Constants (colors, paths, port, etc.)
    data_loader.py  ← Reads and cleans CSV files from reports/
    charts.py       ← Builds all Plotly chart figures
    layout.py       ← Defines the HTML page structure
    callbacks.py    ← Handles user interactions (filters, buttons)
    reports/        ← Drop CSV files here (auto-discovered)

How it works (high level):
--------------------------
  1. `load_all_reports()` reads all CSVs from the reports/ folder
  2. `create_layout(df)` builds the page with date-picker defaults
  3. `callbacks.register(app)` wires up all user interactions
  4. `app.run()` starts the local web server

Auto-refresh:
-------------
  The dashboard automatically reloads data every 60 seconds so you
  don't need to restart after updating a CSV file.
"""

from dash import Dash

from data_loader import load_all_reports
from layout import create_layout
import callbacks
from config import PORT, DEBUG

# ------------------------------------------------------------------
# 1. CREATE THE DASH APPLICATION
# ------------------------------------------------------------------
# suppress_callback_exceptions=True is needed because some components
# (like dynamic_table and kpi_cards) are created inside callbacks,
# not directly in the layout — Dash would raise warnings otherwise.
app = Dash(
    __name__,
    suppress_callback_exceptions=True,
    title="QA Analytics Dashboard",
)

# ------------------------------------------------------------------
# 2. LOAD INITIAL DATA
# ------------------------------------------------------------------
# We load data once at startup to set default date-picker values in
# the layout.  The callbacks reload data on every user interaction
# and on the 60-second auto-refresh timer.
print("[app] Starting QA Analytics Dashboard...")
df_initial = load_all_reports()

# ------------------------------------------------------------------
# 3. SET THE PAGE LAYOUT
# ------------------------------------------------------------------
app.layout = create_layout(df_initial)

# ------------------------------------------------------------------
# 4. REGISTER ALL CALLBACKS
# ------------------------------------------------------------------
callbacks.register(app)

# ------------------------------------------------------------------
# 5. RUN THE SERVER
# ------------------------------------------------------------------
if __name__ == "__main__":
    print(f"[app] Dashboard running at  →  http://127.0.0.1:{PORT}")
    app.run(debug=DEBUG, port=PORT)

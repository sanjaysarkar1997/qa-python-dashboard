# QA Analytics Dashboard

A Python-based interactive dashboard that reads daily test execution CSV reports and displays live charts, KPI cards, and filterable tables.

Built with **Python · Dash · Plotly · Pandas**

---

## 📁 Project Structure

```
qa-python-dashboard/
│
├── app.py            ← 🚀 Start here — runs the dashboard server
├── config.py         ← ⚙️  All settings (colors, port, paths)
├── data_loader.py    ← 📂 Reads and cleans CSV files
├── charts.py         ← 📊 Builds every chart / graph
├── layout.py         ← 🖼️  Defines the page structure
├── callbacks.py      ← 🔄 Handles user interactions
│
├── reports/          ← 📋 DROP YOUR CSV FILES HERE
│   ├── test-summary-2026-06-08.csv
│   ├── test-summary-2026-06-09.csv
│   └── test-summary-2026-06-10.csv
│
└── README.md
```

> **For interns:** Each file has one job.  
> - To change a color → edit `config.py`  
> - To change how CSV data is read → edit `data_loader.py`  
> - To change a chart → edit `charts.py`  
> - To change the page layout → edit `layout.py`  
> - To change what happens on a button click → edit `callbacks.py`

---

## ⚙️ How CSV Files Are Loaded

The dashboard **auto-discovers** all `*.csv` files inside the `reports/` folder.

You do **not** need to edit any code when adding a new report:

1. Export your test summary as a CSV from your test runner
2. Save it into the `reports/` folder
3. Restart the app (or wait for the 60-second auto-refresh)

The file name does not matter — any `.csv` file in `reports/` will be picked up.

---

## 🔧 Required CSV Columns

The dashboard expects these columns (column names are case-insensitive):

| Column | Required? | Description |
|--------|-----------|-------------|
| `Test ID` | Optional | Unique test identifier |
| `Test Name` | ✅ Yes | Human-readable test name |
| `Status` | ✅ Yes | `Passed`, `Failed`, `Skipped`, `Broken` |
| `Start Time` | ✅ Yes | When the test began |
| `Stop Time` | Optional | When the test ended |
| `Duration (s)` | Optional | Runtime in seconds |
| `Monitor Status` | Optional | `High`, `Critical`, `Normal`, etc. |
| `Failure Root Cause` | Optional | Why the test failed |
| `Updated At` | Optional | When the test was last updated |
| `Created At` | Optional | When the test was created |

> **Note:** If a column is missing from an older CSV, the dashboard fills in a safe default — it will not crash.

---

## 🚀 Installation & Setup

> **Why a virtual environment?**  
> Modern Linux/Ubuntu systems block installing Python packages system-wide  
> (`externally-managed-environment` error). A **virtual environment** creates  
> an isolated Python sandbox just for this project — safe and clean.

### Step 1 — Create a virtual environment (first time only)

Open a terminal inside the project folder and run:

```bash
# Navigate to the project folder
cd qa-python-dashboard

# Create the virtual environment (creates a .venv folder)
python3 -m venv .venv
```

### Step 2 — Install required packages

```bash
.venv/bin/pip install -r requirements.txt
```

You should see packages being downloaded and installed.  
This only needs to be done **once**.

### Step 3 — Place CSV files in the `reports/` folder

```
reports/
├── test-summary-2026-06-08.csv
├── test-summary-2026-06-09.csv
└── test-summary-2026-06-10.csv
```

### Step 4 — Run the dashboard

```bash
# Always use the venv Python to run the app
.venv/bin/python3 app.py
```

> **Windows users:** use `.venv\Scripts\python app.py` instead

Expected output:

```
[app] Starting QA Analytics Dashboard...
[data_loader] Found 3 CSV file(s):
   • test-summary-2026-06-08.csv
   • test-summary-2026-06-09.csv
   • test-summary-2026-06-10.csv
[data_loader] Total rows after merge: 1,532
[app] Dashboard running at  →  http://127.0.0.1:8052
```

### Step 4 — Open in browser

```
http://127.0.0.1:8052
```

---

## 📊 Dashboard Features

### 🔍 Filters (top of page)

| Filter | What it does |
|--------|--------------|
| **FROM DATE** | Show only tests run on or after this date |
| **TO DATE** | Show only tests run on or before this date |

All charts update instantly when you change a filter.

---

### 🧮 KPI Cards

Five summary cards show at a glance:

| Card | Color | Meaning |
|------|-------|---------|
| 🧪 TOTAL | Grey | All test runs in the selected range |
| ✅ PASS | Green | Tests that passed |
| ❌ FAIL | Red | Tests that failed |
| ⏭️ SKIPPED | Yellow | Tests that were skipped |
| ⚠️ BROKEN | Purple | Tests marked as broken |

---

### 📈 Charts

| Chart | Description |
|-------|-------------|
| **Test Status Distribution** | Donut chart — proportion of each status |
| **Test Execution Duration** | Bar chart — how long tests take (grouped into 10 s buckets) |
| **Failed Tests Per Day** | Bar chart — failure count per date |
| **Daily Test Trend** | Line chart — daily total, daily new, and daily updated |
| **Monitor Status Breakdown** | Stacked bar — HIGH / CRITICAL / MONITOR CLOSELY priority tests |
| **Failure Root Cause Analysis** | Donut chart — distribution of why tests failed |

---

### 📋 Table Buttons

| Button | Shows |
|--------|-------|
| 🆕 **View New Tests** | Date, Test ID, Test Name, Status, Duration |
| ✏️ **View Updated Tests** | Date, Updated At, Test ID, Test Name, Status |
| 📋 **Full Dataset** | Every column in the combined CSV data |

The table supports:
- **Column sorting** — click any column header
- **Row filtering** — type in the filter row below headers
- **Pagination** — 15 rows per page by default

---

## 🔁 Auto-Refresh

The dashboard automatically reloads data every **60 seconds**.

If you update a CSV while the dashboard is running, the new data will appear within the next refresh cycle — no restart needed.

To force an immediate reload: change a filter value and change it back.

---

## ⚙️ Configuration

Open `config.py` to change dashboard settings without touching any other file:

```python
PORT = 8052                  # Change the server port
REFRESH_INTERVAL_MS = 60000  # Auto-refresh interval (milliseconds)
TABLE_PAGE_SIZE = 15         # Rows shown per page in the data table
PLOTLY_TEMPLATE = "plotly_white"  # Chart visual theme
```

---

## 🐛 Troubleshooting

### `ModuleNotFoundError: No module named 'dash'`

Install dependencies:
```bash
pip install dash plotly pandas numpy
```

---

### `FileNotFoundError: Reports folder not found`

Create the `reports/` folder next to `app.py` and drop your CSV files in it:
```bash
mkdir reports
```

---

### `RuntimeError: No CSV files found in 'reports'`

Make sure the folder contains at least one `.csv` file.

---

### `KeyError: 'START TIME'`

The dashboard expects columns to be named exactly as listed in the **Required CSV Columns** table above.  Check the actual column names in your CSV:

```bash
head -1 reports/your-file.csv
```

---

### Dashboard shows 0 tests / empty charts

Check that:
1. The `DATE` column is being parsed correctly (check `Start Time` column format)
2. Your CSV uses one of the supported status values: `Passed`, `Failed`, `Skipped`, `Broken`

---

### Port already in use

Change the port in `config.py`:
```python
PORT = 8053   # or any free port
```

---

## 🌐 Default URL

```
http://127.0.0.1:8052
```

---

## 📝 For Developers / Interns — How to Extend

### Add a new chart

1. Write a `build_my_chart(df)` function in `charts.py`
2. Add a `dcc.Graph(id="my_chart")` to `layout.py`
3. Add it to the `Output` list and return value in `callbacks.py → update_dashboard()`

### Add a new filter

1. Add the Dash component to `layout.py`
2. Add an `Input("my_filter", "value")` to the callback in `callbacks.py`
3. Apply the filter to `df` inside `update_dashboard()`

### Change the color palette

Edit `STATUS_COLORS` and `KPI_CARD_COLORS` in `config.py`.  
Changes automatically apply to all charts and KPI cards.

---

## 🛑 Stopping the Dashboard

Press `Ctrl + C` in the terminal where the app is running.

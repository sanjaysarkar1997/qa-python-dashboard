# Test Execution Analytics Dashboard - Run Guide

## Overview

This dashboard is built using:

* Python 3.13+
* Dash
* Plotly
* Pandas

The dashboard reads test execution CSV files and provides:

* Status Distribution (Pass / Fail / Skipped / Broken)
* Duration Analysis
* Failed Test Analysis
* Daily Test Trend
* Monitor Status Analysis
* Failure Root Cause Analysis
* New Test Table
* Updated Test Table
* Complete CSV Table



## Required Files

Place all files in the same folder:


infocus.py

test-summary-2026-06-08.csv
9 June.csv
10 June.csv


Example:

Documents/

├── infocus.py
├── test-summary-2026-06-08.csv
├── 9 June.csv
├── 10 June.csv

## Install Required Libraries

Open PowerShell or Command Prompt:

```bash
pip install dash
pip install plotly
pip install pandas
pip install numpy
```

Or:


pip install dash plotly pandas numpy

## Verify Installation

```bash
pip list
```

Should show:

```text
dash
plotly
pandas
numpy
```

---

## Run Dashboard

Navigate to folder:

```bash
cd C:\Users\User\OneDrive\Documents
```

Run:

```bash
python infocus.py
```

Expected output:

```text
Dash is running on http://127.0.0.1:8052/
```

Open browser:

```text
http://127.0.0.1:8052
```

---

## Dashboard Features

### Date Filter

Select:

* Start Date
* End Date

Examples:

```text
08-Jun-2026 → 08-Jun-2026
```

Shows only 8 June data.

```text
08-Jun-2026 → 09-Jun-2026
```

Shows combined 8 June and 9 June data.

---

### Status Filter

Filter by:

```text
PASS
FAIL
SKIPPED
BROKEN
```

---

### KPI Cards

Displays:

```text
TOTAL
PASS
FAIL
SKIPPED
BROKEN
```

---

### Status Distribution Chart

Color mapping:

```text
PASS     → Green
FAIL     → Red
SKIPPED  → Yellow
BROKEN   → Purple
```

---

### Duration Analysis

Execution duration groups:

```text
0-10
10-20
20-30
30-40
40-50
50-60
60+
```

---

### Failed Test Analysis

Displays:

```text
Failed Count
vs
Execution Date
```

---

### Daily Updated Test Trend

Blue:

```text
Total Tests
```

Green:

```text
New Tests
```

Red:

```text
Updated Tests
```

---

### Monitor Status Analysis

Displays:

```text
HIGH
CRITICAL
MONITOR CLOSELY
```

with corresponding test statuses.

---

### Failure Root Cause Analysis

Displays:

```text
Root Cause Distribution
```

for failed tests.

---

### View New Tests

Shows:

```text
DATE
TEST ID
TEST NAME
STATUS
DURATION
```

---

### View Updated Tests

Shows:

```text
UPDATED DATE
UPDATED AT
TEST ID
TEST NAME
STATUS
```

---

### Full CSV Table

Displays:

```text
Entire Dataset
```

with:

* Search
* Filter
* Sort
* Scroll

---

## Refreshing Data

If CSV files are modified:

Save CSV.

Stop dashboard:

```bash
CTRL + C
```

Restart:

```bash
python infocus.py
```

Dashboard will reload latest data.

---

## Common Errors

### File Not Found

Error:

```text
FileNotFoundError
```

Fix:

Ensure CSV file names exactly match:

```text
test-summary-2026-06-08.csv
9 June.csv
10 June.csv
```

---

### Column Not Found

Error:

```text
KeyError: START_DATE
```

Fix:

Check actual CSV column names.

Current dashboard uses:

```text
START TIME
STOP TIME
UPDATED AT
STATUS
MONITOR STATUS
DURATION (S)
```

---

### Dashboard Not Updating

Restart:

```bash
CTRL + C

python infocus.py
```

because data is loaded during application startup.

---

## Default Dashboard URL

```text
http://127.0.0.1:8052
```

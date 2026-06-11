"""
data_loader.py
==============
Responsible for:
  1. Auto-discovering all CSV files inside the `reports/` folder
  2. Loading and concatenating them into a single DataFrame
  3. Cleaning column names, dates, statuses, and durations

Why a separate file?
--------------------
Keeping data-loading logic here means that if the CSV format changes
(new columns, different date format, etc.), you only need to edit
this file — the rest of the dashboard stays untouched.

Usage:
    from data_loader import load_all_reports
    df = load_all_reports()
"""

import os
import glob

import pandas as pd

from config import (
    REPORTS_FOLDER,
    DURATION_BINS,
    DURATION_LABELS,
)


# ------------------------------------------------------------------
# EMOJI → STATUS MAPPING
# ------------------------------------------------------------------
# The CSV files from the test runner contain emoji prefixes in the
# Status column (e.g. "✅ Passed", "❌ Failed").  We normalise these
# to plain uppercase keywords that the dashboard understands.
EMOJI_STATUS_MAP = {
    "✅ PASSED":  "PASS",
    "❌ FAILED":  "FAIL",
    "⏭️ SKIPPED": "SKIPPED",
    "⚠️ BROKEN":  "BROKEN",
    # Also handle plain text variants (older CSVs / manual entries)
    "PASSED":     "PASS",
    "FAILED":     "FAIL",
    "SUCCESS":    "PASS",
    "ERROR":      "FAIL",
}


def _discover_csv_files() -> list[str]:
    """
    Scan the `reports/` folder and return a sorted list of CSV file paths.

    Why auto-discover?
    ------------------
    Hardcoding filenames means someone has to edit the code every time
    a new daily report is added.  Auto-discovery picks up any file that
    matches `reports/test-summary-*.csv` automatically.

    Returns
    -------
    list[str]
        Absolute paths to every CSV found in the reports folder.

    Raises
    ------
    FileNotFoundError
        If the `reports/` folder does not exist.
    RuntimeError
        If no CSV files are found inside the folder.
    """
    if not os.path.isdir(REPORTS_FOLDER):
        raise FileNotFoundError(
            f"Reports folder not found: '{REPORTS_FOLDER}'\n"
            "Please create it and place your CSV files inside."
        )

    # Match ALL .csv files in the folder (case-insensitive extension)
    pattern = os.path.join(REPORTS_FOLDER, "*.csv")
    files = sorted(glob.glob(pattern))

    if not files:
        raise RuntimeError(
            f"No CSV files found in '{REPORTS_FOLDER}'.\n"
            "Drop your test-summary CSV files there and restart the app."
        )

    print(f"[data_loader] Found {len(files)} CSV file(s):")
    for f in files:
        print(f"   • {os.path.basename(f)}")

    return files


def _load_single_csv(path: str) -> pd.DataFrame:
    """
    Load one CSV file into a DataFrame and standardise its column names.

    Different report dates may have slightly different columns
    (e.g. 'Failure Root Cause' was added later).  We handle that here
    so the rest of the code can always assume the same column set.

    Parameters
    ----------
    path : str
        Absolute path to the CSV file.

    Returns
    -------
    pd.DataFrame
        Raw DataFrame with uppercase, stripped column names.
    """
    df = pd.read_csv(path)

    # Standardise column names: strip whitespace and force UPPERCASE
    df.columns = df.columns.str.strip().str.upper()

    return df


def _add_missing_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure all expected columns exist, filling with sensible defaults
    when a column is absent (e.g. older CSV files didn't have all fields).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame that may be missing some optional columns.

    Returns
    -------
    pd.DataFrame
        DataFrame guaranteed to have all required columns.
    """
    # Maps column name → default value when the column is missing
    optional_columns = {
        "MONITOR STATUS":     "NORMAL",
        "FAILURE ROOT CAUSE": "—",          # em-dash = not applicable
        "UPDATED AT":         pd.NaT,
        "CREATED AT":         pd.NaT,
        "TEST TYPE":          "UNKNOWN",
        "FEATURE AREA":       "UNKNOWN",
        "SEVERITY":           "NORMAL",
        "TAGS":               "",
    }

    for col, default in optional_columns.items():
        if col not in df.columns:
            df[col] = default

    return df


def _clean_status(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalise the STATUS column.

    The test runner writes values like "✅ Passed" or "⏭️ Skipped".
    We strip emojis and normalise everything to PASS / FAIL / SKIPPED / BROKEN.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    # Strip whitespace and force uppercase first
    df["STATUS"] = df["STATUS"].astype(str).str.strip().str.upper()

    # Apply the emoji → keyword mapping
    df["STATUS"] = df["STATUS"].replace(EMOJI_STATUS_MAP)

    # Catch any remaining emoji-prefixed variants by checking substrings
    def _fallback_clean(val: str) -> str:
        if "PASS" in val:
            return "PASS"
        if "FAIL" in val:
            return "FAIL"
        if "SKIP" in val:
            return "SKIPPED"
        if "BROKEN" in val:
            return "BROKEN"
        return val  # Keep original if none matched

    df["STATUS"] = df["STATUS"].apply(_fallback_clean)

    return df


def _clean_monitor_status(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalise the MONITOR STATUS column.

    Fills blanks with 'NORMAL' and strips any emoji / extra whitespace.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    df["MONITOR STATUS"] = (
        df["MONITOR STATUS"]
        .fillna("NORMAL")
        .replace("", "NORMAL")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Strip any leading emoji characters (e.g. "⚠️ HIGH" → "HIGH")
    # by keeping only alphanumeric + spaces after stripping unicode symbols
    import re
    df["MONITOR STATUS"] = df["MONITOR STATUS"].apply(
        lambda x: re.sub(r"[^\w\s]", "", x).strip()
    )

    return df


def _parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert date/time columns from strings to proper datetime objects.

    The CSV can have mixed formats (e.g. "08 Jun 2026, 12:21:18 pm"
    or "2026-06-01"), so we use errors='coerce' to safely handle
    anything unparseable (it becomes NaT instead of crashing).

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    date_columns = ["START TIME", "STOP TIME", "UPDATED AT", "CREATED AT"]

    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(
                df[col], errors="coerce", dayfirst=True, format="mixed"
            )

    # Remove rows where START TIME could not be parsed (they have no date)
    df = df[df["START TIME"].notna()].copy()

    # Create date-only columns for grouping by day
    df["DATE"] = df["START TIME"].dt.date
    df["UPDATED DATE"] = df["UPDATED AT"].dt.date

    return df


def _clean_duration(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert DURATION (S) from strings like "1.23 s" to numeric seconds,
    then bucket them into human-readable groups (e.g. "0–10 s").

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    df["DURATION (S)"] = (
        df["DURATION (S)"]
        .astype(str)
        .str.replace("s", "", regex=False)    # Remove trailing " s"
        .str.replace(",", "", regex=False)    # Remove thousands separator
        .str.strip()
    )

    df["DURATION (S)"] = pd.to_numeric(df["DURATION (S)"], errors="coerce")

    # Group into duration buckets defined in config.py
    df["DURATION GROUP"] = pd.cut(
        df["DURATION (S)"],
        bins=DURATION_BINS,
        labels=DURATION_LABELS,
        include_lowest=True,
    )

    return df


def load_all_reports() -> pd.DataFrame:
    """
    Main entry point — load, merge, and clean all CSV reports.

    This function:
      1. Discovers all CSV files in the `reports/` folder
      2. Loads and concatenates them into one DataFrame
      3. Adds missing columns (for older CSV formats)
      4. Cleans dates, statuses, durations
      5. Returns the final clean DataFrame

    Returns
    -------
    pd.DataFrame
        A clean, analysis-ready DataFrame with all test records.

    Example
    -------
    >>> from data_loader import load_all_reports
    >>> df = load_all_reports()
    >>> print(df.shape)
    (1500, 18)
    """
    csv_files = _discover_csv_files()

    # Load each CSV and store in a list
    frames = []
    for path in csv_files:
        try:
            frame = _load_single_csv(path)
            frames.append(frame)
            print(f"[data_loader]   Loaded {len(frame):,} rows from {os.path.basename(path)}")
        except Exception as exc:
            # Log the error but continue — don't crash on one bad file
            print(f"[data_loader]   ⚠ Skipped {os.path.basename(path)}: {exc}")

    if not frames:
        raise RuntimeError("No data could be loaded. Check your CSV files.")

    # Stack all frames into one big DataFrame
    df = pd.concat(frames, ignore_index=True)
    print(f"[data_loader] Total rows after merge: {len(df):,}")

    # Apply cleaning pipeline step by step
    df = _add_missing_columns(df)
    df = _parse_dates(df)
    df = _clean_status(df)
    df = _clean_monitor_status(df)
    df = _clean_duration(df)

    return df

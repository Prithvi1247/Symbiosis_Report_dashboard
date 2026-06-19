"""
Data Layer: CSV Loader
======================
Handles all CSV loading, parsing, validation, and caching.

The portal exports are non-standard: each file has a report title on
line 0, a blank line 1, and then the actual header + data from line 2
onward. Some files have a trailing Total row. This module normalises
all of that into clean DataFrames so the rest of the application never
has to deal with raw file quirks.
"""

from __future__ import annotations

import functools
import io
import os
from pathlib import Path
from typing import Optional

import pandas as pd

# ── Constants ──────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent.parent / "data"

# Files that have a trailing total/summary row (first column is blank or 'Total')
FILES_WITH_TOTAL_ROW = {
    "course_wise_data.csv",
    "course_wise_paid.csv",
    "course_wise_registration.csv",
}

# TestDateWiseCityReport has a different header structure (4 metadata rows)
SNAP_TEST_FILE = "TestDateWiseCityReport.csv"


# ── Core loader ────────────────────────────────────────────────────────────────

@functools.lru_cache(maxsize=32)
def load_dataset(filename: str) -> pd.DataFrame:
    """
    Load and clean a portal-exported CSV file.

    Returns a validated, cleaned DataFrame with proper column names
    and numeric types. Results are cached in memory (lru_cache) so
    repeated calls within a session are free.

    Parameters
    ----------
    filename : str
        Bare filename (e.g. "category_wise.csv") relative to data/.
    """
    path = DATA_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    if filename == SNAP_TEST_FILE:
        return _load_snap_test(path)

    return _load_standard_portal_export(path, filename)


def _load_standard_portal_export(path: Path, filename: str) -> pd.DataFrame:
    """
    Standard portal format:
      Line 0:  Report title  (skip)
      Line 1:  blank         (skip)
      Line 2:  header row
      Line 3+: data rows
      Last row (some files): Total row — detected and dropped
    """
    with open(path, encoding="utf-8-sig") as f:
        lines = f.readlines()

    # Strip report title (line 0) and blank (line 1), keep from line 2
    content = "".join(lines[2:])

    df = pd.read_csv(
        io.StringIO(content),
        skip_blank_lines=True,
    )

    # Drop the S.No. column — it adds no analytical value
    if "S.No." in df.columns or "S.No" in df.columns:
        sno_col = "S.No." if "S.No." in df.columns else "S.No"
        df = df.drop(columns=[sno_col])

    # Drop trailing Total row if applicable
    if filename in FILES_WITH_TOTAL_ROW:
        first_col = df.columns[0]
        # Drop rows where first col is blank OR equals literal "Total"
        mask_blank = df[first_col].isna() | (df[first_col].astype(str).str.strip() == "")
        mask_total = df[first_col].astype(str).str.strip().str.lower() == "total"
        df = df[~(mask_blank | mask_total)]

    # Drop any fully empty columns (artifact of trailing commas in portal exports)
    df = df.dropna(axis=1, how="all")
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]

    # Coerce numeric columns
    numeric_candidates = [
        "Registered Applicants", "Paid Applicants", "%",
        "Paid Applicants", "Registered Applicants",
    ]
    for col in df.columns:
        if col in numeric_candidates or df[col].dtype == object:
            try:
                df[col] = pd.to_numeric(df[col], errors="ignore")
            except Exception:
                pass

    df = df.reset_index(drop=True)
    return df


def _load_snap_test(path: Path) -> pd.DataFrame:
    """
    SNAP Test Date/City report has a distinct structure:
      Line 0: blank
      Line 1: Test,All
      Line 2: State Name,All
      Line 3: blank
      Line 4: S.No,City Name,SNAP Test 1 Registered,...
      Line 5+: data
    """
    with open(path, encoding="utf-8-sig") as f:
        lines = f.readlines()

    # Header is line 4 (index 4), data from line 5
    content = "".join(lines[4:])

    df = pd.read_csv(
        io.StringIO(content),
        skip_blank_lines=True,
    )

    # Drop S.No
    if "S.No" in df.columns:
        df = df.drop(columns=["S.No"])

    # Drop trailing empty column from trailing commas
    df = df.dropna(axis=1, how="all")
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]

    # Coerce numeric
    for col in df.columns:
        if col != "City Name":
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # Parse city and state from "City - State" format for easier filtering
    if "City Name" in df.columns:
        df[["City", "State"]] = df["City Name"].str.rsplit(" - ", n=1, expand=True)
        df["City"] = df["City"].str.strip()
        df["State"] = df["State"].str.strip().fillna("Unknown")

    df = df.reset_index(drop=True)
    return df


# ── Utility helpers ────────────────────────────────────────────────────────────

def list_available_datasets() -> list[str]:
    """Return all CSV filenames present in the data directory."""
    return sorted(f.name for f in DATA_DIR.glob("*.csv"))


def get_dataset_info(filename: str) -> dict:
    """Return shape, columns, and null counts for a dataset."""
    df = load_dataset(filename)
    return {
        "rows": len(df),
        "columns": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "nulls": df.isnull().sum().to_dict(),
    }


def clear_cache() -> None:
    """Invalidate the loader cache (call when data files are refreshed)."""
    load_dataset.cache_clear()

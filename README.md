# Admissions Analytics — Phase 1: Dynamic Report Builder

> Production-grade reporting tool for the university admissions team.
> Built for the Admissions Head, Marketing Team, and Senior Management.

---

## Quick Start

```bash
# 1. Install dependencies (Python 3.9+)
pip install -r requirements.txt

# 2. Run the application
streamlit run app.py

# 3. Open in browser (auto-opens at http://localhost:8501)
```

**No database. No backend. No login required.**
Drop updated CSVs from the portal into `data/` and click "Refresh Data."

---

## Folder Structure

```
admissions_app/
│
├── app.py                      # Streamlit entry point + UI orchestration
│
├── requirements.txt            # Python dependencies
│
├── data/                       # CSV files (source of record)
│   ├── admission_nri.csv
│   ├── category_wise.csv
│   ├── city_wise_data.csv
│   ├── course_wise_data.csv
│   ├── course_wise_paid.csv
│   ├── course_wise_registration.csv
│   ├── education_type_data.csv
│   ├── experience_wise_data.csv
│   ├── gender_data.csv
│   ├── nri_data.csv
│   ├── paid_wise_data.csv
│   ├── payment_mode_data.csv
│   ├── registration_by_date_data.csv
│   ├── state_wise_data.csv
│   └── TestDateWiseCityReport.csv
│
├── config/
│   └── metadata.py             # Dataset registry (single source of truth)
│
├── engine/
│   ├── loader.py               # CSV loading, cleaning, validation, caching
│   └── charts.py               # Chart generation (matplotlib, no Streamlit dependency)
│
└── ui/
    └── components.py           # Reusable Streamlit widgets
```

---

## Architecture

### Layer Responsibilities

```
┌─────────────────────────────────────────────────────┐
│  UI Layer  (app.py, ui/components.py)               │
│  Streamlit controls, layout, chart display, export  │
├─────────────────────────────────────────────────────┤
│  Report Engine  (engine/charts.py)                  │
│  Dataset-agnostic chart and summary generation      │
├─────────────────────────────────────────────────────┤
│  Metadata Layer  (config/metadata.py)               │
│  Dataset registry: columns, metrics, chart defaults │
├─────────────────────────────────────────────────────┤
│  Data Layer  (engine/loader.py)                     │
│  CSV loading, portal-format parsing, LRU cache      │
├─────────────────────────────────────────────────────┤
│  Data Files  (data/*.csv)                           │
│  Exported portal reports — system of record         │
└─────────────────────────────────────────────────────┘
```

**Key design principle:** each layer has one job and no upward dependencies.
The chart engine does not know about Streamlit. The loader does not know
about charts. The metadata does not know about either.

---

## CSV Data Analysis

After inspecting all 15 portal-exported files, the following was found:

### Export Format (all standard files)
```
Line 0:   Report title   ← stripped by loader
Line 1:   (blank)        ← stripped by loader
Line 2:   S.No.,ColA,ColB,...
Line 3+:  data rows
Last row: Total row (some files) ← detected and dropped
```

### Dataset Inventory

| Dataset ID             | File                            | Dimension            | Metrics                          | Group            |
|------------------------|---------------------------------|----------------------|----------------------------------|------------------|
| registration_by_date   | registration_by_date_data.csv   | Date                 | Registered, Paid, Conversion %   | Funnel           |
| paid_by_date           | paid_wise_data.csv              | Date                 | Paid Applicants                  | Funnel           |
| payment_mode           | payment_mode_data.csv           | Payment Mode         | Registered, Paid, Conversion %   | Funnel           |
| course_wise            | course_wise_data.csv            | Program (Institute)  | Registered, Paid                 | Programs         |
| course_wise_registration | course_wise_registration.csv  | Program              | Registered                       | Programs         |
| course_wise_paid       | course_wise_paid.csv            | Program              | Paid                             | Programs         |
| state_wise             | state_wise_data.csv             | State                | Registered, Paid, Conversion %   | Geography        |
| city_wise              | city_wise_data.csv              | City                 | Registered, Paid, Conversion %   | Geography        |
| snap_test_city         | TestDateWiseCityReport.csv      | City (Test Centre)   | Per-test Registered/Paid/Avail.  | Geography        |
| gender                 | gender_data.csv                 | Gender               | Registered, Paid, Conversion %   | Demographics     |
| category_wise          | category_wise.csv               | Reservation Category | Registered, Paid, Conversion %   | Demographics     |
| education_type         | education_type_data.csv         | Education Stream     | Registered, Paid, Conversion %   | Demographics     |
| experience_wise        | experience_wise_data.csv        | Experience Level     | Registered, Paid, Conversion %   | Demographics     |
| nri_status             | nri_data.csv                    | NRI Flag             | Registered, Paid, Conversion %   | NRI/International|
| admission_nri          | admission_nri.csv               | NRI Quota Flag       | Registered, Paid, Conversion %   | NRI/International|

### Data Quality Notes
- `city_wise_data.csv` contains data-entry artefacts ("fsdfsdf", "vnb") — these come from the source system and are passed through transparently.
- `course_wise_*.csv` files contain a trailing `Total` row which is automatically detected and removed.
- `TestDateWiseCityReport.csv` has a 4-line metadata header (test name, state filter) before the column row — handled by a dedicated parser.
- Date columns use `%b-%d-%Y` format (e.g. `Jun-18-2026`) — parsed for line chart ordering.
- State column has asterisks on some entries marking union territories — passed through as-is.

---

## Metadata Model

Every dataset is described by one entry in `config/metadata.py`:

```python
"registration_by_date": {
    "file":           "registration_by_date_data.csv",
    "label":          "Registrations by Date",       # shown in UI
    "description":    "Daily count of...",            # subtitle/tooltip
    "dimension_col":  "DateWise",                    # X-axis / grouping column
    "metrics": [
        {
            "col":     "Registered Applicants",      # exact column name
            "label":   "Registered Applicants",      # displayed in UI
            "unit":    "count",                      # "count" or "percent"
            "tooltip": "Total applicants who...",    # context tooltip
        },
    ],
    "default_metric": "Registered Applicants",       # pre-selected
    "default_chart":  "line",                        # pre-selected chart type
    "sort_by":        "DateWise",                    # default sort column
    "date_col":       "DateWise",                    # enables date parsing for line charts
    "group":          "Funnel",                      # sidebar navigation group
    "notes":          None,                          # optional data quality note
}
```

**Adding a new dataset requires only this config change — no code changes.**

---

## Report Engine

`engine/charts.py` exposes three public functions:

```python
build_chart(df, dimension_col, metric_col, metric_label, chart_type, title, ...)
    → matplotlib.Figure | None

build_summary_stats(df, metric_col, dimension_col)
    → {"total": int, "top_dimension": str, "top_value": float, "average": float, "count": int}

prepare_export_df(df, dimension_col, metric_col)
    → pd.DataFrame  (sorted, clean, export-ready)
```

The engine is **100% independent of Streamlit** — it can be imported in
Jupyter notebooks, scheduled scripts, or a future FastAPI backend without
modification.

### Supported Chart Types

| Type  | Best for                          | Notes                                  |
|-------|-----------------------------------|----------------------------------------|
| Bar   | Categorical comparisons           | Horizontal; auto-truncates at 30 items |
| Line  | Time-series / trends              | Parses date strings for x-axis order  |
| Pie   | Small-N distributions (≤ 8)       | Collapses excess slices into "Others" |
| Table | Full data exploration / audit     | Always available as fallback           |

---

## Data Layer

`engine/loader.py` uses Python's `functools.lru_cache` to cache each
loaded DataFrame in memory. This means:

- First load: reads and parses the CSV file.
- Subsequent loads (same session): returns the cached DataFrame instantly.
- Cache invalidation: the "Refresh Data" button calls `clear_cache()` and re-runs.

**Parsing logic handles:**
- Report title header (lines 0–1 skipped)
- Trailing S.No. column dropped
- Trailing Total rows detected and removed
- Fully-empty columns from trailing commas removed
- Numeric coercion applied to metric columns
- Special parser for `TestDateWiseCityReport.csv` (4-line metadata header)

---

## Error Handling Strategy

| Scenario                      | Response                                        |
|-------------------------------|-------------------------------------------------|
| CSV file not found            | `FileNotFoundError` caught; friendly error UI   |
| Column missing in dataset     | Checked before rendering; explains which column |
| Zero-value dataset            | Empty-state message shown                       |
| Chart with all-zero values    | xlim guard prevents matplotlib crash            |
| Date parse failure (line chart)| Falls back to string labels; no crash         |
| Large number of categories    | Bar chart caps at 30; pie collapses to 7+Others |
| Pie chart with 1 row          | Renders correctly; user sees full label         |

---

## Phase 2+ Roadmap

The architecture is designed so future dashboards can be added as new
Streamlit pages without modifying any existing code.

### Planned Dashboards

#### Executive Dashboard
KPI overview across all datasets in one view. Uses `build_summary_stats()`
from the engine against each dataset in the registry. No new engine code.

#### Demand Dashboard
Multi-dataset view: programs ranked by registered vs. paid applicants,
with a calculated conversion column. Combines `course_wise`,
`course_wise_registration`, `course_wise_paid`.

#### Geography Dashboard
State + city heatmap table, SNAP centre capacity overview. Uses
`state_wise`, `city_wise`, `snap_test_city`.

#### Demographics Dashboard
Side-by-side charts for gender, category, education type, experience.
Uses `gender`, `category_wise`, `education_type`, `experience_wise`.

#### Funnel Dashboard
Registration → Payment conversion funnel. Combines
`registration_by_date` and `paid_by_date` with a calculated conversion
rate by day.

### Adding a Phase 2 Page

```python
# pages/02_demand_dashboard.py

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.loader import load_dataset
from engine.charts import build_chart, build_summary_stats
from config.metadata import get_dataset_meta, get_metric_labels
from ui.components import render_kpi_strip, render_chart_or_table, render_export_button

# All reusable — no duplication
```

Streamlit's multi-page feature (`pages/` directory) will automatically
surface each dashboard as a sidebar navigation item.

---

## Updating Data

When the admissions portal produces updated exports:

1. Replace the relevant CSV in `data/`.
2. Click **"🔄 Refresh Data"** in the sidebar (or restart the app).
3. Reports update immediately.

No schema changes, no migrations, no database credentials.

---

## Decisions & Trade-offs

| Decision | Rationale |
|----------|-----------|
| **matplotlib over Plotly** | No network required; lightweight; renders in any environment |
| **lru_cache over st.cache_data** | Engine stays Streamlit-agnostic; easier unit testing |
| **Metadata dict over YAML** | No extra dependency; type hints work; easier to validate in CI |
| **Horizontal bar charts** | Long program names (e.g. MBA course names) don't fit on vertical axes |
| **No database** | Data is exported snapshots, not live data; CSV is the system of record |
| **No ML/AI** | Out of scope; adds complexity without admissions business value |
| **Single `app.py`** | Simpler for Phase 1; pages/ dir added in Phase 2 without refactoring |
# Symbiosis_Report_dashboard

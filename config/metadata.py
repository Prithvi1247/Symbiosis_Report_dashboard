"""
Metadata Layer: Dataset Registry
=================================
This is the single source of truth for every dataset the application
knows about. Adding a new CSV to the data/ folder and defining its
entry here is all that is needed to surface it in every report, dashboard,
and export without touching any other code.

Schema
------
Each entry in DATASET_REGISTRY is keyed by a stable dataset_id and
contains:

  file          : str   — filename in data/
  label         : str   — human-readable name shown in the UI
  description   : str   — one-sentence description for tooltips
  dimension_col : str   — the primary grouping/category column
  metrics       : list  — available numeric columns with metadata
  default_metric: str   — column selected by default
  default_chart : str   — "bar" | "line" | "pie" | "table"
  sort_by       : str   — column to sort descending by default
  date_col      : str?  — set if the dimension is a date/time field
  group         : str   — logical grouping for UI navigation
  notes         : str?  — optional data quality notes shown in UI

Metric metadata fields
----------------------
  col     : str  — exact column name in the CSV
  label   : str  — display label
  unit    : str  — "count" | "percent"
  tooltip : str  — description shown to user
"""

from __future__ import annotations

DATASET_REGISTRY: dict[str, dict] = {

    # ── Application Funnel ─────────────────────────────────────────────────────

    "registration_by_date": {
        "file": "registration_by_date_data.csv",
        "label": "Registrations by Date",
        "description": "Daily count of registered and paid applicants over time.",
        "dimension_col": "DateWise",
        "metrics": [
            {
                "col": "Registered Applicants",
                "label": "Registered Applicants",
                "unit": "count",
                "tooltip": "Total applicants who started registration on this date.",
            },
            {
                "col": "Paid Applicants",
                "label": "Paid Applicants",
                "unit": "count",
                "tooltip": "Applicants who completed fee payment on this date.",
            },
            {
                "col": "%",
                "label": "Payment Conversion Rate (%)",
                "unit": "percent",
                "tooltip": "Percentage of registered applicants who paid on this date.",
            },
        ],
        "default_metric": "Registered Applicants",
        "default_chart": "line",
        "sort_by": "DateWise",
        "date_col": "DateWise",
        "group": "Funnel",
        "notes": None,
    },

    "paid_by_date": {
        "file": "paid_wise_data.csv",
        "label": "Payments by Date",
        "description": "Daily paid applicant count — payment completion timeline.",
        "dimension_col": "Paidwise",
        "metrics": [
            {
                "col": "Paid Applicants",
                "label": "Paid Applicants",
                "unit": "count",
                "tooltip": "Number of applicants whose payment was completed on this date.",
            },
        ],
        "default_metric": "Paid Applicants",
        "default_chart": "line",
        "sort_by": "Paidwise",
        "date_col": "Paidwise",
        "group": "Funnel",
        "notes": None,
    },

    "payment_mode": {
        "file": "payment_mode_data.csv",
        "label": "Payment Mode",
        "description": "Breakdown of applicants by payment method used.",
        "dimension_col": "Paymentmodewise",
        "metrics": [
            {
                "col": "Registered Applicants",
                "label": "Registered Applicants",
                "unit": "count",
                "tooltip": "Total registrations using this payment mode.",
            },
            {
                "col": "Paid Applicants",
                "label": "Paid Applicants",
                "unit": "count",
                "tooltip": "Completed payments via this mode.",
            },
            {
                "col": "%",
                "label": "Conversion Rate (%)",
                "unit": "percent",
                "tooltip": "Payment success rate for this mode.",
            },
        ],
        "default_metric": "Paid Applicants",
        "default_chart": "bar",
        "sort_by": "Paid Applicants",
        "date_col": None,
        "group": "Funnel",
        "notes": None,
    },

    # ── Program Demand ─────────────────────────────────────────────────────────

    "course_wise": {
        "file": "course_wise_data.csv",
        "label": "Applications by Program",
        "description": "Registered and paid applicants for each MBA program.",
        "dimension_col": "Institute",
        "metrics": [
            {
                "col": "Registered Applicants",
                "label": "Registered Applicants",
                "unit": "count",
                "tooltip": "Total registrations for this program.",
            },
            {
                "col": "Paid Applicants",
                "label": "Paid Applicants",
                "unit": "count",
                "tooltip": "Applicants who completed payment for this program.",
            },
        ],
        "default_metric": "Registered Applicants",
        "default_chart": "bar",
        "sort_by": "Registered Applicants",
        "date_col": None,
        "group": "Programs",
        "notes": "Each applicant may register for multiple programs.",
    },

    "course_wise_registration": {
        "file": "course_wise_registration.csv",
        "label": "Registrations by Program",
        "description": "Registration-only view per program (excludes payment data).",
        "dimension_col": "Institute",
        "metrics": [
            {
                "col": "Registered Applicants",
                "label": "Registered Applicants",
                "unit": "count",
                "tooltip": "Total registrations for this program.",
            },
        ],
        "default_metric": "Registered Applicants",
        "default_chart": "bar",
        "sort_by": "Registered Applicants",
        "date_col": None,
        "group": "Programs",
        "notes": None,
    },

    "course_wise_paid": {
        "file": "course_wise_paid.csv",
        "label": "Paid Applications by Program",
        "description": "Fee-paid applicants per program — confirmed demand indicator.",
        "dimension_col": "Institute",
        "metrics": [
            {
                "col": "Paid Applicants",
                "label": "Paid Applicants",
                "unit": "count",
                "tooltip": "Applicants who completed payment for this program.",
            },
        ],
        "default_metric": "Paid Applicants",
        "default_chart": "bar",
        "sort_by": "Paid Applicants",
        "date_col": None,
        "group": "Programs",
        "notes": None,
    },

    # ── Geography ──────────────────────────────────────────────────────────────

    "state_wise": {
        "file": "state_wise_data.csv",
        "label": "Applications by State",
        "description": "State-level breakdown of registered and paid applicants.",
        "dimension_col": "StateWise",
        "metrics": [
            {
                "col": "Registered Applicants",
                "label": "Registered Applicants",
                "unit": "count",
                "tooltip": "Total registrations from this state.",
            },
            {
                "col": "Paid Applicants",
                "label": "Paid Applicants",
                "unit": "count",
                "tooltip": "Paid applicants from this state.",
            },
            {
                "col": "%",
                "label": "Conversion Rate (%)",
                "unit": "percent",
                "tooltip": "Percentage of state registrations that converted to paid.",
            },
        ],
        "default_metric": "Registered Applicants",
        "default_chart": "bar",
        "sort_by": "Registered Applicants",
        "date_col": None,
        "group": "Geography",
        "notes": "States marked with * indicate union territories.",
    },

    "city_wise": {
        "file": "city_wise_data.csv",
        "label": "Applications by City",
        "description": "City-level breakdown of registered and paid applicants.",
        "dimension_col": "CityWise",
        "metrics": [
            {
                "col": "Registered Applicants",
                "label": "Registered Applicants",
                "unit": "count",
                "tooltip": "Total registrations from this city.",
            },
            {
                "col": "Paid Applicants",
                "label": "Paid Applicants",
                "unit": "count",
                "tooltip": "Paid applicants from this city.",
            },
            {
                "col": "%",
                "label": "Conversion Rate (%)",
                "unit": "percent",
                "tooltip": "Percentage of city registrations that converted to paid.",
            },
        ],
        "default_metric": "Registered Applicants",
        "default_chart": "bar",
        "sort_by": "Registered Applicants",
        "date_col": None,
        "group": "Geography",
        "notes": "Some entries may contain data entry artefacts from the source system.",
    },

    "snap_test_city": {
        "file": "TestDateWiseCityReport.csv",
        "label": "SNAP Test Centre Capacity",
        "description": "Per-city SNAP test centre registration, payment, capacity and availability across 3 test dates.",
        "dimension_col": "City Name",
        "metrics": [
            {
                "col": "SNAP Test 1 Registered",
                "label": "SNAP Test 1 — Registered",
                "unit": "count",
                "tooltip": "Candidates registered for SNAP Test 1 at this centre.",
            },
            {
                "col": "SNAP Test 1 Paid",
                "label": "SNAP Test 1 — Paid",
                "unit": "count",
                "tooltip": "Candidates who paid for SNAP Test 1 at this centre.",
            },
            {
                "col": "SNAP Test 1 Available",
                "label": "SNAP Test 1 — Seats Available",
                "unit": "count",
                "tooltip": "Remaining capacity at SNAP Test 1 centre.",
            },
            {
                "col": "SNAP Test 2 Registered",
                "label": "SNAP Test 2 — Registered",
                "unit": "count",
                "tooltip": "Candidates registered for SNAP Test 2 at this centre.",
            },
            {
                "col": "SNAP Test 2 Paid",
                "label": "SNAP Test 2 — Paid",
                "unit": "count",
                "tooltip": "Candidates who paid for SNAP Test 2 at this centre.",
            },
            {
                "col": "SNAP Test 2 Available",
                "label": "SNAP Test 2 — Seats Available",
                "unit": "count",
                "tooltip": "Remaining capacity at SNAP Test 2 centre.",
            },
            {
                "col": "SNAP Test 3 Registered",
                "label": "SNAP Test 3 — Registered",
                "unit": "count",
                "tooltip": "Candidates registered for SNAP Test 3 at this centre.",
            },
            {
                "col": "SNAP Test 3 Paid",
                "label": "SNAP Test 3 — Paid",
                "unit": "count",
                "tooltip": "Candidates who paid for SNAP Test 3 at this centre.",
            },
            {
                "col": "SNAP Test 3 Available",
                "label": "SNAP Test 3 — Seats Available",
                "unit": "count",
                "tooltip": "Remaining capacity at SNAP Test 3 centre.",
            },
        ],
        "default_metric": "SNAP Test 1 Registered",
        "default_chart": "bar",
        "sort_by": "SNAP Test 1 Registered",
        "date_col": None,
        "group": "Geography",
        "notes": "Showing only centres with at least one registration by default. Filter can be removed.",
    },

    # ── Demographics ───────────────────────────────────────────────────────────

    "gender": {
        "file": "gender_data.csv",
        "label": "Gender Distribution",
        "description": "Applicant breakdown by gender.",
        "dimension_col": "GenderWise",
        "metrics": [
            {
                "col": "Registered Applicants",
                "label": "Registered Applicants",
                "unit": "count",
                "tooltip": "Total registrations for each gender.",
            },
            {
                "col": "Paid Applicants",
                "label": "Paid Applicants",
                "unit": "count",
                "tooltip": "Paid applicants for each gender.",
            },
            {
                "col": "%",
                "label": "Conversion Rate (%)",
                "unit": "percent",
                "tooltip": "Payment conversion rate by gender.",
            },
        ],
        "default_metric": "Registered Applicants",
        "default_chart": "pie",
        "sort_by": "Registered Applicants",
        "date_col": None,
        "group": "Demographics",
        "notes": None,
    },

    "category_wise": {
        "file": "category_wise.csv",
        "label": "Reservation Category",
        "description": "Applicant distribution across government-defined reservation categories.",
        "dimension_col": "CategoryWise",
        "metrics": [
            {
                "col": "Registered Applicants",
                "label": "Registered Applicants",
                "unit": "count",
                "tooltip": "Total registrations per category.",
            },
            {
                "col": "Paid Applicants",
                "label": "Paid Applicants",
                "unit": "count",
                "tooltip": "Paid applicants per category.",
            },
            {
                "col": "%",
                "label": "Conversion Rate (%)",
                "unit": "percent",
                "tooltip": "Payment conversion rate by category.",
            },
        ],
        "default_metric": "Registered Applicants",
        "default_chart": "bar",
        "sort_by": "Registered Applicants",
        "date_col": None,
        "group": "Demographics",
        "notes": None,
    },

    "education_type": {
        "file": "education_type_data.csv",
        "label": "Education Background",
        "description": "Applicant distribution by undergraduate education stream.",
        "dimension_col": "EducationTypeWise",
        "metrics": [
            {
                "col": "Registered Applicants",
                "label": "Registered Applicants",
                "unit": "count",
                "tooltip": "Total registrations per education type.",
            },
            {
                "col": "Paid Applicants",
                "label": "Paid Applicants",
                "unit": "count",
                "tooltip": "Paid applicants per education type.",
            },
            {
                "col": "%",
                "label": "Conversion Rate (%)",
                "unit": "percent",
                "tooltip": "Payment conversion rate by education type.",
            },
        ],
        "default_metric": "Registered Applicants",
        "default_chart": "pie",
        "sort_by": "Registered Applicants",
        "date_col": None,
        "group": "Demographics",
        "notes": None,
    },

    "experience_wise": {
        "file": "experience_wise_data.csv",
        "label": "Work Experience",
        "description": "Fresher vs. experienced applicant split.",
        "dimension_col": "ExperienceWise",
        "metrics": [
            {
                "col": "Registered Applicants",
                "label": "Registered Applicants",
                "unit": "count",
                "tooltip": "Total registrations per experience category.",
            },
            {
                "col": "Paid Applicants",
                "label": "Paid Applicants",
                "unit": "count",
                "tooltip": "Paid applicants per experience category.",
            },
            {
                "col": "%",
                "label": "Conversion Rate (%)",
                "unit": "percent",
                "tooltip": "Payment conversion rate by experience.",
            },
        ],
        "default_metric": "Registered Applicants",
        "default_chart": "pie",
        "sort_by": "Registered Applicants",
        "date_col": None,
        "group": "Demographics",
        "notes": None,
    },

    # ── NRI / International ────────────────────────────────────────────────────

    "nri_status": {
        "file": "nri_data.csv",
        "label": "NRI Applicant Status",
        "description": "NRI vs. domestic applicant split.",
        "dimension_col": "NRI_candidate",
        "metrics": [
            {
                "col": "Registered Applicants",
                "label": "Registered Applicants",
                "unit": "count",
                "tooltip": "Total registrations by NRI status.",
            },
            {
                "col": "Paid Applicants",
                "label": "Paid Applicants",
                "unit": "count",
                "tooltip": "Paid applicants by NRI status.",
            },
            {
                "col": "%",
                "label": "Conversion Rate (%)",
                "unit": "percent",
                "tooltip": "Payment conversion rate by NRI status.",
            },
        ],
        "default_metric": "Registered Applicants",
        "default_chart": "pie",
        "sort_by": "Registered Applicants",
        "date_col": None,
        "group": "NRI / International",
        "notes": None,
    },

    "admission_nri": {
        "file": "admission_nri.csv",
        "label": "NRI Admission Quota",
        "description": "Applicants under the NRI admission quota vs. general applications.",
        "dimension_col": "Admission_under_NRI",
        "metrics": [
            {
                "col": "Registered Applicants",
                "label": "Registered Applicants",
                "unit": "count",
                "tooltip": "Registrations under NRI quota flag.",
            },
            {
                "col": "Paid Applicants",
                "label": "Paid Applicants",
                "unit": "count",
                "tooltip": "Paid applicants under NRI quota flag.",
            },
            {
                "col": "%",
                "label": "Conversion Rate (%)",
                "unit": "percent",
                "tooltip": "Conversion rate for NRI quota vs. general.",
            },
        ],
        "default_metric": "Registered Applicants",
        "default_chart": "pie",
        "sort_by": "Registered Applicants",
        "date_col": None,
        "group": "NRI / International",
        "notes": "NRI quota eligibility is determined by the source system.",
    },
}


# ── Accessor helpers ───────────────────────────────────────────────────────────

def get_dataset_meta(dataset_id: str) -> dict:
    if dataset_id not in DATASET_REGISTRY:
        raise KeyError(f"Unknown dataset: {dataset_id}")
    return DATASET_REGISTRY[dataset_id]


def list_datasets_by_group() -> dict[str, list[tuple[str, str]]]:
    """Return {group_name: [(dataset_id, label), ...]} for UI navigation."""
    groups: dict[str, list] = {}
    for ds_id, meta in DATASET_REGISTRY.items():
        g = meta["group"]
        groups.setdefault(g, []).append((ds_id, meta["label"]))
    return groups


def get_metric_labels(dataset_id: str) -> dict[str, str]:
    """Return {col_name: display_label} for a dataset's metrics."""
    meta = get_dataset_meta(dataset_id)
    return {m["col"]: m["label"] for m in meta["metrics"]}


def get_metric_cols(dataset_id: str) -> list[str]:
    """Return list of metric column names for a dataset."""
    meta = get_dataset_meta(dataset_id)
    return [m["col"] for m in meta["metrics"]]

"""
Admissions Analytics — Phase 1: Dynamic Report Builder
=======================================================
Entry point for the Streamlit application.

Run with:
    streamlit run app.py

Architecture overview
---------------------
  app.py              ← You are here (UI orchestration)
  config/metadata.py  ← Dataset registry (metadata layer)
  engine/loader.py    ← CSV loading + caching (data layer)
  engine/charts.py    ← Chart generation (report engine)
  ui/components.py    ← Reusable UI widgets (presentation layer)
  data/               ← CSV files (source of record)

Adding a new dataset
--------------------
1. Drop the CSV into data/.
2. Add an entry to config/metadata.py DATASET_REGISTRY.
3. Done — no other code changes needed.
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path when run directly
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import streamlit as st

from config.metadata import (
    DATASET_REGISTRY,
    get_dataset_meta,
    get_metric_labels,
    list_datasets_by_group,
)
from engine.charts import CHART_TYPES, build_chart, build_summary_stats
from engine.loader import clear_cache, load_dataset
from ui.components import (
    render_chart_or_table,
    render_dataset_info,
    render_empty_state,
    render_error,
    render_export_button,
    render_kpi_strip,
)

# ── Page configuration ─────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Admissions Analytics",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS (minimal — production professional) ─────────────────────────────

st.markdown(
    """
    <style>
    /* Tighten sidebar padding */
    section[data-testid="stSidebar"] > div { padding-top: 1rem; }

    /* Section dividers */
    .report-section-header {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #888;
        margin: 1.2rem 0 0.3rem 0;
    }

    /* KPI metric delta suppression (we use our own labels) */
    [data-testid="stMetricDelta"] { display: none; }

    /* Subtle chart border */
    [data-testid="stImage"] {
        border: 1px solid #e8e8e8;
        border-radius: 4px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Sidebar — Report Builder Controls ─────────────────────────────────────────

def render_sidebar() -> dict:
    """
    Render all sidebar controls and return the user's selections as a dict.

    Returns
    -------
    {
        "dataset_id"  : str,
        "metric_col"  : str,
        "chart_type"  : str,
        "show_table"  : bool,
        "filter_zeros": bool,
        "top_n"       : int | None,
    }
    """
    st.sidebar.image(
        'ui/symbiosis_logo2.png',
        width=200,
    )

    st.sidebar.title("Report Builder")
    st.sidebar.markdown("---")

    # ── 1. Dataset selection (grouped) ────────────────────────────────────────
    st.sidebar.markdown('<p class="report-section-header">1 · Select Dataset</p>', unsafe_allow_html=True)

    groups = list_datasets_by_group()
    group_names = list(groups.keys())

    selected_group = st.sidebar.selectbox(
        "Category",
        options=group_names,
        key="selected_group",
    )

    datasets_in_group = groups[selected_group]
    dataset_options   = {label: ds_id for ds_id, label in datasets_in_group}

    selected_label = st.sidebar.selectbox(
        "Dataset",
        options=list(dataset_options.keys()),
        key="selected_dataset_label",
    )
    dataset_id = dataset_options[selected_label]
    meta       = get_dataset_meta(dataset_id)

    st.sidebar.caption(meta["description"])
    if meta.get("notes"):
        st.sidebar.caption(f"📌 {meta['notes']}")

    # ── 2. Metric selection ────────────────────────────────────────────────────
    st.sidebar.markdown('<p class="report-section-header">2 · Select Metric</p>', unsafe_allow_html=True)

    metric_labels = get_metric_labels(dataset_id)  # {col: label}
    metric_list   = list(metric_labels.keys())

    default_metric = meta.get("default_metric", metric_list[0])
    default_idx    = metric_list.index(default_metric) if default_metric in metric_list else 0

    metric_col = st.sidebar.radio(
        "Metric",
        options=metric_list,
        index=default_idx,
        format_func=lambda c: metric_labels[c],
        key=f"metric_{dataset_id}",
    )

    # ── 3. Chart type ──────────────────────────────────────────────────────────
    st.sidebar.markdown('<p class="report-section-header">3 · Chart Type</p>', unsafe_allow_html=True)

    chart_type_options = list(CHART_TYPES.keys())
    default_chart      = meta.get("default_chart", "bar")
    default_chart_idx  = chart_type_options.index(default_chart) if default_chart in chart_type_options else 0

    chart_type = st.sidebar.radio(
        "Chart Type",
        options=chart_type_options,
        index=default_chart_idx,
        format_func=lambda k: CHART_TYPES[k],
        key=f"chart_{dataset_id}",
    )

    # ── 4. Display options ─────────────────────────────────────────────────────
    st.sidebar.markdown('<p class="report-section-header">4 · Options</p>', unsafe_allow_html=True)

    show_table   = st.sidebar.checkbox("Show underlying data table", value=True)
    filter_zeros = st.sidebar.checkbox("Hide zero-value rows", value=False)

    top_n_enabled = st.sidebar.checkbox("Limit to top N rows", value=False)
    top_n = None
    if top_n_enabled:
        top_n = st.sidebar.slider("Top N", min_value=5, max_value=30, value=10, step=5)

    # ── Refresh cache ──────────────────────────────────────────────────────────
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Refresh Data"):
        clear_cache()
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.caption("Admissions Analytics v1.0 · Phase 1")

    return {
        "dataset_id":   dataset_id,
        "metric_col":   metric_col,
        "chart_type":   chart_type,
        "show_table":   show_table,
        "filter_zeros": filter_zeros,
        "top_n":        top_n,
        "meta":         meta,
    }


# ── Main report page ───────────────────────────────────────────────────────────

def render_report(config: dict) -> None:
    """
    Load data, apply filters, build chart, render everything.
    Separated from sidebar so it can be reused by future dashboard pages.
    """
    dataset_id   = config["dataset_id"]
    metric_col   = config["metric_col"]
    chart_type   = config["chart_type"]
    show_table   = config["show_table"]
    filter_zeros = config["filter_zeros"]
    top_n        = config["top_n"]
    meta         = config["meta"]

    # ── Load data ──────────────────────────────────────────────────────────────
    try:
        df = load_dataset(meta["file"])
    except FileNotFoundError as e:
        render_error("Data file not found.", str(e))
        return
    except Exception as e:
        render_error("Failed to load dataset.", str(e))
        return

    if df.empty:
        render_empty_state("Dataset is empty.")
        return

    # ── Validate metric column ─────────────────────────────────────────────────
    if metric_col not in df.columns:
        render_error(
            f"Metric column '{metric_col}' not found in this dataset.",
            f"Available columns: {list(df.columns)}",
        )
        return

    dimension_col = meta["dimension_col"]
    metric_label  = get_metric_labels(dataset_id).get(metric_col, metric_col)
    is_percent    = (metric_col == "%")
    date_col      = meta.get("date_col")

    # ── Apply filters ──────────────────────────────────────────────────────────
    plot_df = df.copy()

    if filter_zeros:
        before = len(plot_df)
        plot_df = plot_df[pd.to_numeric(plot_df[metric_col], errors="coerce") > 0]
        after = len(plot_df)
        if before != after:
            st.caption(f"ℹ️ {before - after} zero-value rows hidden.")

    if top_n is not None:
        plot_df = plot_df.sort_values(
            by=metric_col,
            ascending=False,
            key=lambda s: pd.to_numeric(s, errors="coerce"),
        ).head(top_n)

    if plot_df.empty:
        render_empty_state("No data after applying filters.")
        return

    # ── Page header ────────────────────────────────────────────────────────────
    chart_title = (
        f"{meta['label']} — {metric_label}"
        + (f" (Top {top_n})" if top_n else "")
    )

    st.title(f"🎓 {meta['label']}")
    st.markdown(f"**{meta['description']}**")
    st.markdown("---")

    # ── KPI Strip ──────────────────────────────────────────────────────────────
    stats = build_summary_stats(plot_df, metric_col, dimension_col)
    render_kpi_strip(stats, metric_label, is_percent)

    st.markdown("---")

    # ── Chart ──────────────────────────────────────────────────────────────────
    try:
        fig = build_chart(
            df           = plot_df,
            dimension_col= dimension_col,
            metric_col   = metric_col,
            metric_label = metric_label,
            chart_type   = chart_type,
            title        = chart_title,
            is_percent   = is_percent,
            date_col     = date_col if chart_type == "line" else None,
        )
    except ValueError as e:
        render_error("Chart generation failed.", str(e))
        return

    render_chart_or_table(
        fig           = fig,
        df            = plot_df,
        dimension_col = dimension_col,
        metric_col    = metric_col,
        metric_label  = metric_label,
        chart_type    = chart_type,
        show_data_table = show_table,
    )

    st.markdown("---")

    # ── Export ─────────────────────────────────────────────────────────────────
    col_exp, col_info = st.columns([1, 3])
    with col_exp:
        render_export_button(
            df            = plot_df,
            dimension_col = dimension_col,
            metric_col    = metric_col,
            metric_label  = metric_label,
            dataset_label = meta["label"],
        )

    # ── Dataset info (collapsible) ─────────────────────────────────────────────
    st.markdown("---")
    render_dataset_info(meta, df)


# ── Application entry point ────────────────────────────────────────────────────

def main() -> None:
    config = render_sidebar()
    render_report(config)


if __name__ == "__main__":
    main()
else:
    # When imported by streamlit run, main() executes at module level
    main()

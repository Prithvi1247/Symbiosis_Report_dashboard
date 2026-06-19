"""
UI Components
=============
Reusable Streamlit UI primitives.

Updated for Plotly: st.pyplot() → st.plotly_chart()
"""

from __future__ import annotations

import io
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# ── KPI Strip ─────────────────────────────────────────────────────────────────

def render_kpi_strip(stats: dict, metric_label: str, is_percent: bool = False) -> None:
    if not stats:
        return

    fmt = (lambda v: f"{v:.1f}%") if is_percent else (lambda v: f"{int(v):,}")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total", fmt(stats.get("total", 0)))
    with col2:
        st.metric("Avg per Category", fmt(stats.get("average", 0)))
    with col3:
        st.metric("# Categories", str(stats.get("count", 0)))
    with col4:
        top_label = str(stats.get("top_dimension", "—"))
        if len(top_label) > 24:
            top_label = top_label[:22] + "…"
        st.metric(f"Top: {top_label}", fmt(stats.get("top_value", 0)))


# ── Chart + Table ──────────────────────────────────────────────────────────────

def render_chart_or_table(
    fig: Optional[go.Figure],
    df: pd.DataFrame,
    dimension_col: str,
    metric_col: str,
    metric_label: str,
    chart_type: str,
    show_data_table: bool = True,
) -> None:
    if chart_type != "table" and fig is not None:
        st.plotly_chart(fig, use_container_width=True)

    if show_data_table or chart_type == "table":
        with st.expander("📋 Underlying Data", expanded=(chart_type == "table")):
            display_df = _format_display_table(df, dimension_col, metric_col, metric_label)
            st.dataframe(display_df, use_container_width=True, hide_index=True)


def _format_display_table(
    df: pd.DataFrame,
    dimension_col: str,
    metric_col: str,
    metric_label: str,
) -> pd.DataFrame:
    cols = [c for c in df.columns if c in [dimension_col, metric_col] or
            c in ["Registered Applicants", "Paid Applicants", "%"]]
    display = df[cols].copy().rename(columns={metric_col: metric_label})
    if metric_label in display.columns:
        try:
            display = display.sort_values(metric_label, ascending=False)
        except Exception:
            pass
    return display.reset_index(drop=True)


# ── Export ─────────────────────────────────────────────────────────────────────

def render_export_button(
    df: pd.DataFrame,
    dimension_col: str,
    metric_col: str,
    metric_label: str,
    dataset_label: str,
) -> None:
    export_df = df[[c for c in [dimension_col, metric_col] if c in df.columns]].copy()
    export_df = export_df.rename(columns={metric_col: metric_label})
    export_df = export_df.sort_values(metric_label, ascending=False, ignore_index=True)

    buf = io.BytesIO()
    export_df.to_csv(buf, index=False)
    buf.seek(0)

    st.download_button(
        label="⬇️ Export as CSV",
        data=buf.getvalue(),
        file_name=f"{dataset_label.lower().replace(' ', '_')}_export.csv",
        mime="text/csv",
        use_container_width=True,
    )


# ── Dataset Info ───────────────────────────────────────────────────────────────

def render_dataset_info(meta: dict, df: pd.DataFrame) -> None:
    with st.expander("ℹ️ Dataset Information", expanded=False):
        st.markdown(f"**Source file:** `{meta['file']}`")
        st.markdown(f"**Description:** {meta['description']}")
        st.markdown(f"**Rows loaded:** {len(df):,}")
        st.markdown(f"**Columns:** {', '.join(df.columns.tolist())}")
        if meta.get("notes"):
            st.info(f"📌 **Note:** {meta['notes']}")
        nulls = df.isnull().sum()
        if nulls.any():
            st.warning("⚠️ Null values detected:")
            st.dataframe(nulls[nulls > 0].rename("Null Count"), use_container_width=True)


# ── Error States ───────────────────────────────────────────────────────────────

def render_error(message: str, detail: Optional[str] = None) -> None:
    st.error(f"❌ {message}")
    if detail:
        with st.expander("Technical details"):
            st.code(detail)


def render_empty_state(message: str = "No data available for the selected filters.") -> None:
    st.info(f"📭 {message}")

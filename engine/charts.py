"""
Report Engine
=============
Generic, dataset-agnostic chart and summary generation.

All chart functions return a Plotly Figure (go.Figure) or None for
tables. The engine has no Streamlit dependency.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import plotly.graph_objects as go

# ── Design tokens ──────────────────────────────────────────────────────────────
PRIMARY    = "#13458D"
ACCENT     = "#86BDE4"
HIGHLIGHT  = "#ed7d31"
GRID_COLOR = "#bbbbbb"
TEXT_COLOR = "#000000"  # Crisp, high-contrast black for all text elements

PALETTE_CATEGORICAL = [
    "#1f4e79", "#2e75b6", "#ed7d31", "#70ad47",
    "#ffc000", "#7030a0", "#c00000", "#00b0f0",
]

FONT = dict(family="Inter, Arial, sans-serif", size=13, color=TEXT_COLOR)

CHART_TYPES = {
    "bar":   "Bar Chart",
    "line":  "Line Chart",
    "pie":   "Pie Chart",
    "table": "Data Table",
}

# Shared layout defaults applied to every chart
_BASE_LAYOUT = dict(
    font=FONT,
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(t=70, b=60, l=120, r=50), # Safe padding margins to prevent text clipping
    hoverlabel=dict(
        bgcolor="white", 
        font_size=13, 
        font_family="Inter, Arial, sans-serif", 
        font_color=TEXT_COLOR
    ),
)


# ── Public API ─────────────────────────────────────────────────────────────────

def build_chart(
    df: pd.DataFrame,
    dimension_col: str,
    metric_col: str,
    metric_label: str,
    chart_type: str,
    title: str,
    max_categories: int = 30,
    is_percent: bool = False,
    date_col: Optional[str] = None,
    sort_ascending: bool = False,
) -> Optional[go.Figure]:
    if chart_type == "table":
        return None

    if metric_col not in df.columns or dimension_col not in df.columns:
        raise ValueError(
            f"Required columns missing: {dimension_col!r} or {metric_col!r}"
        )

    plot_df = _prepare_plot_data(
        df, dimension_col, metric_col, chart_type,
        max_categories, sort_ascending, date_col,
    )

    if chart_type == "bar":
        return _bar_chart(plot_df, dimension_col, metric_col, metric_label, title, is_percent)
    elif chart_type == "line":
        return _line_chart(plot_df, dimension_col, metric_col, metric_label, title, is_percent)
    elif chart_type == "pie":
        return _pie_chart(plot_df, dimension_col, metric_col, metric_label, title)
    else:
        raise ValueError(f"Unsupported chart type: {chart_type!r}")


def build_summary_stats(
    df: pd.DataFrame,
    metric_col: str,
    dimension_col: str,
) -> dict:
    if metric_col not in df.columns:
        return {}

    numeric = pd.to_numeric(df[metric_col], errors="coerce").dropna()
    if numeric.empty:
        return {}

    top_idx = df[metric_col].idxmax() if not df[metric_col].empty else None
    top_dim = df.loc[top_idx, dimension_col] if top_idx is not None else "—"
    top_val = df.loc[top_idx, metric_col]    if top_idx is not None else 0

    return {
        "total":         int(numeric.sum()),
        "top_dimension": str(top_dim),
        "top_value":     float(top_val),
        "average":       round(float(numeric.mean()), 1),
        "count":         int(len(numeric)),
    }


def prepare_export_df(
    df: pd.DataFrame,
    dimension_col: str,
    metric_col: str,
) -> pd.DataFrame:
    cols   = [c for c in [dimension_col, metric_col] if c in df.columns]
    export = df[cols].copy().dropna(subset=[metric_col])
    return export.sort_values(metric_col, ascending=False)


# ── Internal helpers ───────────────────────────────────────────────────────────

def _prepare_plot_data(
    df: pd.DataFrame,
    dimension_col: str,
    metric_col: str,
    chart_type: str,
    max_categories: int,
    sort_ascending: bool,
    date_col: Optional[str],
) -> pd.DataFrame:
    plot_df = df[[dimension_col, metric_col]].copy()
    plot_df[metric_col] = pd.to_numeric(plot_df[metric_col], errors="coerce")
    plot_df = plot_df.dropna(subset=[metric_col])

    # For time-series visualizations, parse and sort by genuine timeline logic
    if (chart_type == "line" or date_col) and date_col:
        try:
            plot_df[dimension_col] = pd.to_datetime(
                plot_df[dimension_col], format="%b-%d-%Y", errors="coerce"
            )
            plot_df = plot_df.dropna(subset=[dimension_col]).sort_values(dimension_col)
            # Revert back to original layout string presentation format for clean ticks
            plot_df[dimension_col] = plot_df[dimension_col].dt.strftime("%b-%d-%Y")
        except Exception:
            pass  
    elif chart_type == "bar":
        plot_df = plot_df.sort_values(metric_col, ascending=sort_ascending)
        if len(plot_df) > max_categories:
            plot_df = (
                plot_df.tail(max_categories) if not sort_ascending
                else plot_df.head(max_categories)
            )

    return plot_df.reset_index(drop=True)


def _bar_chart(
    df: pd.DataFrame,
    dimension_col: str,
    metric_col: str,
    metric_label: str,
    title: str,
    is_percent: bool,
) -> go.Figure:
    tick_suffix = "%" if is_percent else ""
    hover_fmt   = "%{x:.1f}%" if is_percent else "%{x:,}"

    height = max(380, min(len(df) * 36 + 100, 750)) 

    fig = go.Figure(
        go.Bar(
            x=df[metric_col],
            y=df[dimension_col].astype(str),
            orientation="h",
            marker_color=PRIMARY,
            text=[
                f"{v:.1f}%" if is_percent else f"{int(v):,}"
                for v in df[metric_col]
            ],
            textposition="outside",
            textfont=dict(size=12, color=TEXT_COLOR, weight="bold"), 
            hovertemplate=(
                f"<b>%{{y}}</b><br>{metric_label}: {hover_fmt}<extra></extra>"
            ),
            cliponaxis=False,
        )
    )
    fig.update_layout(**_BASE_LAYOUT)
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color=TEXT_COLOR, weight="bold"), x=0.02, y=0.96),
        height=height,
        xaxis=dict(
            title=metric_label,
            title_font=dict(color=TEXT_COLOR, size=13, weight="bold"),
            ticksuffix=tick_suffix,
            gridcolor=GRID_COLOR,
            linecolor=GRID_COLOR,
            tickfont=dict(color=TEXT_COLOR, size=12), # Clear label color
            zeroline=False,
        ),
        yaxis=dict(
            automargin=True,
            linecolor=GRID_COLOR,
            tickfont=dict(color=TEXT_COLOR, size=12), # Clear label color
            gridcolor=GRID_COLOR,
            type="category" # Locks ordered sequencing
        ),
        bargap=0.25,
    )
    return fig


def _line_chart(
    df: pd.DataFrame,
    dimension_col: str,
    metric_col: str,
    metric_label: str,
    title: str,
    is_percent: bool,
) -> go.Figure:
    tick_suffix = "%" if is_percent else ""
    hover_fmt   = "%{y:.1f}%" if is_percent else "%{y:,}"

    x_vals = df[dimension_col]
    y_vals = df[metric_col]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        fill="tozeroy",
        fillcolor="rgba(19, 69, 141, 0.08)", 
        line=dict(color=PRIMARY, width=3),   
        mode="lines+markers",
        marker=dict(size=8, color=PRIMARY, line=dict(width=1.5, color="white")),
        hovertemplate=f"<b>%{{x}}</b><br>{metric_label}: {hover_fmt}<extra></extra>",
        name=metric_label,
    ))
    fig.update_layout(**_BASE_LAYOUT)
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color=TEXT_COLOR, weight="bold"), x=0.02, y=0.95),
        height=420,
        xaxis=dict(
            title=dimension_col,
            title_font=dict(color=TEXT_COLOR, size=13, weight="bold"),
            gridcolor=GRID_COLOR,
            linecolor=GRID_COLOR,
            tickfont=dict(color=TEXT_COLOR, size=12), # Clear label color
            tickangle=-30,
        ),
        yaxis=dict(
            title=metric_label,
            title_font=dict(color=TEXT_COLOR, size=13, weight="bold"),
            ticksuffix=tick_suffix,
            gridcolor=GRID_COLOR,
            linecolor=GRID_COLOR,
            tickfont=dict(color=TEXT_COLOR, size=12), # Clear label color
            zeroline=True,
            zerolinecolor=GRID_COLOR,
        ),
        showlegend=False,
    )
    return fig


def _pie_chart(
    df: pd.DataFrame,
    dimension_col: str,
    metric_col: str,
    metric_label: str,
    title: str,
) -> go.Figure:
    if len(df) > 8:
        df = df.sort_values(metric_col, ascending=False)
        top        = df.head(7).copy()
        others_val = df.iloc[7:][metric_col].sum()
        if others_val > 0:
            others_row = pd.DataFrame([{dimension_col: "Others", metric_col: others_val}])
            df = pd.concat([top, others_row], ignore_index=True)
        else:
            df = top

    labels = df[dimension_col].astype(str).tolist()
    values = df[metric_col].tolist()

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.4, 
            marker=dict(
                colors=PALETTE_CATEGORICAL[: len(labels)],
                line=dict(color="white", width=2),
            ),
            textinfo="percent",
            textfont=dict(size=13, color="#FFFFFF", weight="bold"), 
            hovertemplate=(
                "<b>%{label}</b><br>"
                f"{metric_label}: %{{value:,}}<br>"
                "Share: %{percent}<extra></extra>"
            ),
            sort=False,
        )
    )
    fig.update_layout(**_BASE_LAYOUT)
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color=TEXT_COLOR, weight="bold"), x=0.02, y=0.95),
        height=450,
        legend=dict(
            orientation="v",
            x=1.05,
            y=0.5,
            font=dict(size=12, color=TEXT_COLOR), 
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(t=70, b=40, l=40, r=180),
    )
    return fig
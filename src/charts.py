import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import plotly.graph_objects as go
from plotly.subplots import make_subplots

SEGMENTS   = ["Human Expression", "Flame for Life", "Blade Excellence"]
SEG_COLORS = ["#2196F3", "#FF9800", "#4CAF50"]

def _mpl_style():
    plt.rcParams.update({
        "figure.facecolor": "#0f1117",
        "axes.facecolor":   "#0f1117",
        "axes.edgecolor":   "#333333",
        "axes.labelcolor":  "#cccccc",
        "xtick.color":      "#cccccc",
        "ytick.color":      "#cccccc",
        "text.color":       "#cccccc",
        "grid.color":       "#222222",
        "grid.linestyle":   "--",
        "grid.linewidth":   0.6,
        "legend.facecolor": "#1a1a2e",
        "legend.edgecolor": "#333333",
        "font.family":      "monospace",
    })

def chart_revenue_by_segment(sales_filepath: str = "data/bic_sales_data.csv"):
    _mpl_style()
    raw = pd.read_csv(sales_filepath)
    raw["revenue"] = raw["units_millions"] * raw["unit_price_eur"]
    df = raw.groupby(["year", "quarter", "segment"])["revenue"].sum().reset_index()
    df["period"] = df["year"].astype(str) + " " + df["quarter"]
    pivot = df.pivot_table(index="period", columns="segment", values="revenue", aggfunc="sum").fillna(0)

    fig, ax = plt.subplots(figsize=(12, 6))
    bottom = pd.Series([0] * len(pivot), index=pivot.index)
    for seg, color in zip(SEGMENTS, SEG_COLORS):
        if seg in pivot.columns:
            ax.bar(pivot.index, pivot[seg], bottom=bottom, label=seg, color=color, alpha=0.85)
            bottom += pivot[seg]

    ax.set_title("Revenue by Segment per Quarter", fontsize=14, pad=15)
    ax.set_xlabel("Period")
    ax.set_ylabel("Revenue (€M)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{x:.0f}M"))
    ax.legend()
    ax.grid(axis="y")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("output/charts/01_revenue_by_segment.png", dpi=150)
    plt.show()

def chart_margins(income_q: pd.DataFrame):
    _mpl_style()
    df = income_q.copy()
    df["period"] = df["year"].astype(str) + " " + df["quarter"]
    margins = df.groupby("period")[["gross_profit_margin", "ebit_margin"]].mean().reset_index()

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(margins["period"], margins["gross_profit_margin"],
            label="Gross Profit Margin", color="#2196F3", linewidth=2.5, marker="o")
    ax.plot(margins["period"], margins["ebit_margin"],
            label="EBIT Margin", color="#FF9800", linewidth=2.5, marker="o")

    ax.set_title("Gross Profit Margin vs EBIT Margin", fontsize=14, pad=15)
    ax.set_xlabel("Period")
    ax.set_ylabel("Margin %")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x*100:.1f}%"))
    ax.legend()
    ax.grid(axis="y")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("output/charts/02_margins.png", dpi=150)
    plt.show()

def chart_units_sold_vs_produced(prod_quarterly: pd.DataFrame):
    _mpl_style()
    df = prod_quarterly.copy()
    df["period"] = df["year"].astype(str) + " " + df["quarter"]

    periods = sorted(df["period"].unique())
    x       = np.arange(len(periods))
    width   = 0.13

    fig, ax = plt.subplots(figsize=(14, 6))
    for i, seg in enumerate(SEGMENTS):
        sub    = df[df["segment"] == seg].set_index("period").reindex(periods).fillna(0)
        offset = (i - len(SEGMENTS)) * width
        ax.bar(x + offset,         sub["units_sold"],       width, label=f"{seg} — Sold",     color=SEG_COLORS[i], alpha=0.9)
        ax.bar(x + offset + width, sub["units_to_produce"], width, label=f"{seg} — Produced", color=SEG_COLORS[i], alpha=0.4)

    ax.set_title("Units Sold vs Units to Produce by Segment", fontsize=14, pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(periods, rotation=45)
    ax.set_ylabel("Units (millions)")
    ax.legend(fontsize=7)
    ax.grid(axis="y")
    plt.tight_layout()
    plt.savefig("output/charts/03_units_sold_vs_produced.png", dpi=150)
    plt.show()

def chart_inventory(prod_quarterly: pd.DataFrame):
    _mpl_style()
    df = prod_quarterly.copy()
    df["period"] = df["year"].astype(str) + " " + df["quarter"]
    inv = df.groupby("period")[["beg_inv", "end_inv"]].sum().reset_index()

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(inv["period"], inv["beg_inv"], label="Beginning Inventory", color="#2196F3", alpha=0.85)
    ax.bar(inv["period"], inv["end_inv"], label="Ending Inventory",    color="#FF9800", alpha=0.85, bottom=inv["beg_inv"])

    ax.set_title("Beginning vs Ending Inventory per Quarter", fontsize=14, pad=15)
    ax.set_ylabel("Units (millions)")
    ax.legend()
    ax.grid(axis="y")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("output/charts/04_inventory.png", dpi=150)
    plt.show()

def chart_cost_breakdown(cost_quarterly: pd.DataFrame):
    _mpl_style()
    df = cost_quarterly.copy()
    df["period"] = df["year"].astype(str) + " " + df["quarter"]
    cost = df.groupby("period")[["material_cost", "labour_cost", "var_overhead", "fix_overhead"]].sum().reset_index()

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = ["#2196F3", "#4CAF50", "#FF9800", "#F44336"]
    labels = ["Material", "Labour", "Variable Overhead", "Fixed Overhead"]
    cols   = ["material_cost", "labour_cost", "var_overhead", "fix_overhead"]
    bottom = [0] * len(cost)

    for col, label, color in zip(cols, labels, colors):
        ax.bar(cost["period"], cost[col], bottom=bottom, label=label, color=color, alpha=0.85)
        bottom = [b + v for b, v in zip(bottom, cost[col])]

    ax.set_title("Production Cost Breakdown per Quarter", fontsize=14, pad=15)
    ax.set_ylabel("Cost (€M)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{x:.0f}M"))
    ax.legend()
    ax.grid(axis="y")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("output/charts/05_cost_breakdown.png", dpi=150)
    plt.show()

def chart_waterfall(income_y: pd.DataFrame):
    df = income_y.groupby("year")[["revenue", "total_cost", "total_opex", "gross_profit", "ebit"]].sum().reset_index()

    for _, row in df.iterrows():
        fig = go.Figure(go.Waterfall(
            name         = "P&L",
            orientation  = "v",
            measure      = ["absolute", "relative", "total", "relative", "total"],
            x            = ["Revenue", "− Production Cost", "Gross Profit", "− OpEx", "EBIT"],
            y            = [row["revenue"], -row["total_cost"], 0, -row["total_opex"], 0],
            connector    = {"line": {"color": "#555555"}},
            increasing   = {"marker": {"color": "#4CAF50"}},
            decreasing   = {"marker": {"color": "#F44336"}},
            totals       = {"marker": {"color": "#2196F3"}},
            texttemplate = "%{y:.1f}M",
            textposition = "outside",
        ))
        fig.update_layout(
            title        = f"P&L Waterfall — {int(row['year'])}",
            plot_bgcolor = "#0f1117",
            paper_bgcolor= "#0f1117",
            font_color   = "#cccccc",
            yaxis_title  = "€ Millions",
            showlegend   = False,
        )
        fig.write_html(f"output/charts/06_waterfall_{int(row['year'])}.html")
        fig.show()

def chart_cash_position(net_cash: pd.DataFrame):
    df = net_cash.copy()
    df["period"] = df["year"].astype(str) + " " + df["quarter"]

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=df["period"], y=df["cash_inflow"],  name="Cash Inflows",  marker_color="#4CAF50", opacity=0.85), secondary_y=False)
    fig.add_trace(go.Bar(x=df["period"], y=df["cash_outflow"], name="Cash Outflows", marker_color="#F44336", opacity=0.85), secondary_y=False)
    fig.add_trace(go.Scatter(x=df["period"], y=df["net_cash"], name="Net Cash",
                             mode="lines+markers", line=dict(color="#FF9800", width=2.5),
                             marker=dict(size=7)), secondary_y=True)

    fig.update_layout(
        title         = "Cash Inflows vs Outflows with Net Cash Position",
        barmode       = "group",
        plot_bgcolor  = "#0f1117",
        paper_bgcolor = "#0f1117",
        font_color    = "#cccccc",
        legend        = dict(bgcolor="#1a1a2e"),
    )
    fig.update_yaxes(title_text="€ Millions",    secondary_y=False)
    fig.update_yaxes(title_text="Net Cash (€M)", secondary_y=True)
    fig.write_html("output/charts/07_cash_position.html")
    fig.show()

def chart_collections_by_segment(collections_df: pd.DataFrame):
    _mpl_style()
    df = collections_df.copy()
    df["period"] = df["year"].astype(str) + " " + df["quarter"]
    pivot = df.pivot_table(index="period", columns="segment", values="cash_inflow", aggfunc="sum").fillna(0)

    fig, ax = plt.subplots(figsize=(12, 6))
    bottom = pd.Series([0] * len(pivot), index=pivot.index)
    for seg, color in zip(SEGMENTS, SEG_COLORS):
        if seg in pivot.columns:
            ax.bar(pivot.index, pivot[seg], bottom=bottom, label=seg, color=color, alpha=0.85)
            bottom += pivot[seg]

    ax.set_title("Cash Collections by Segment per Quarter", fontsize=14, pad=15)
    ax.set_ylabel("Cash Inflow (€M)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{x:.0f}M"))
    ax.legend()
    ax.grid(axis="y")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("output/charts/08_collections_by_segment.png", dpi=150)
    plt.show()
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go

SEGMENTS   = ["Human Expression", "Flame for Life", "Blade Excellence"]
SEG_COLORS = ["#3395F6", "#4440B5", "#0523B8"]

def _add_semester(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["semester"] = df["quarter"].apply(lambda q: "H1" if q in ["Q1", "Q2"] else "H2")
    return df

# ------------------------------------------------------------------ #
#  UNITS SOLD — STACKED BAR — SEMESTER LEVEL (side by side)          #
# ------------------------------------------------------------------ #
def chart_sales_units_stacked(sales_filepath: str = "data/bic_sales_data.csv"):
    raw = pd.read_csv(sales_filepath)
    raw = _add_semester(raw)
    sem = raw.groupby(["year", "semester", "segment"])["units_millions"].sum().reset_index()

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=["2023", "2024"],
        shared_yaxes=True
    )

    for col, year in enumerate([2023, 2024], start=1):
        sub   = sem[sem["year"] == year].sort_values("semester")
        pivot = sub.pivot_table(
            index="semester", columns="segment",
            values="units_millions", aggfunc="sum"
        ).fillna(0)

        for seg, color in zip(SEGMENTS, SEG_COLORS):
            if seg in pivot.columns:
                fig.add_trace(
                    go.Bar(
                        name=seg,
                        x=pivot.index.tolist(),
                        y=pivot[seg].values.tolist(),
                        marker_color=color,
                        opacity=0.85,
                        text=[f"{v:.1f}M" for v in pivot[seg].values],
                        textposition="inside",
                        showlegend=(col == 1),
                    ),
                    row=1, col=col
                )

    fig.update_layout(
        title_text="Units Sold by Segment — Semester Level",
        barmode="stack",
        plot_bgcolor="#0f1117",
        paper_bgcolor="#0f1117",
        font_color="#cccccc",
        legend=dict(bgcolor="#1a1a2e"),
    )
    fig.update_yaxes(title_text="Units Sold (millions)", col=1)
    fig.write_html("output/charts/S1_units_sold_stacked_semester.html")
    fig.show()

# ------------------------------------------------------------------ #
#  REVENUE — STACKED BAR — MONTHLY LEVEL (side by side)              #
# ------------------------------------------------------------------ #
def chart_sales_revenue_monthly(sales_filepath: str = "data/bic_sales_data.csv"):
    raw = pd.read_csv(sales_filepath).sort_values(["year", "month_num"])
    raw["revenue"] = raw["units_millions"] * raw["unit_price_eur"]

    monthly = (
        raw.groupby(["year", "month_num", "month", "segment"])["revenue"]
        .sum()
        .reset_index()
    )

    # build ordered month labels from data
    month_labels = (
        raw.drop_duplicates("month_num")
        .sort_values("month_num")["month"]
        .tolist()
    )

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=["2023", "2024"],
        shared_yaxes=True
    )

    for col, year in enumerate([2023, 2024], start=1):
        sub   = monthly[monthly["year"] == year]
        pivot = sub.pivot_table(
            index="month_num", columns="segment",
            values="revenue", aggfunc="sum"
        ).fillna(0)
        pivot.index = month_labels

        for seg, color in zip(SEGMENTS, SEG_COLORS):
            if seg in pivot.columns:
                fig.add_trace(
                    go.Bar(
                        name=seg,
                        x=pivot.index.tolist(),
                        y=pivot[seg].values.tolist(),
                        marker_color=color,
                        opacity=0.85,
                        text=[f"€{v:.1f}M" for v in pivot[seg].values],
                        textposition="inside",
                        showlegend=(col == 1),
                    ),
                    row=1, col=col
                )

    fig.update_layout(
        title_text="Revenue by Segment — Monthly Level",
        barmode="stack",
        plot_bgcolor="#0f1117",
        paper_bgcolor="#0f1117",
        font_color="#cccccc",
        legend=dict(bgcolor="#1a1a2e"),
    )
    fig.update_yaxes(title_text="Revenue (€M)", col=1)
    fig.update_xaxes(tickangle=45)
    fig.write_html("output/charts/S2_revenue_monthly.html")
    fig.show()

# ------------------------------------------------------------------ #
#  VOLUME VS PRICE CONTRIBUTION — SALES VARIANCE ANALYSIS            #
# ------------------------------------------------------------------ #
def chart_volume_price_contribution(sales_filepath: str = "data/bic_sales_data.csv"):
    raw = pd.read_csv(sales_filepath)
    raw["revenue"] = raw["units_millions"] * raw["unit_price_eur"]

    # yearly aggregation per segment
    yearly = (
        raw.groupby(["year", "segment"])
        .agg(units=("units_millions", "sum"), revenue=("revenue", "sum"))
        .reset_index()
    )
    yearly["avg_price"] = yearly["revenue"] / yearly["units"]

    results = []
    for seg in SEGMENTS:
        y2023 = yearly[(yearly["year"] == 2023) & (yearly["segment"] == seg)].iloc[0]
        y2024 = yearly[(yearly["year"] == 2024) & (yearly["segment"] == seg)].iloc[0]

        # base price × volume change = volume effect
        volume_effect = (y2024["units"] - y2023["units"]) * y2023["avg_price"]
        # base volume × price change = price effect
        price_effect  = (y2024["avg_price"] - y2023["avg_price"]) * y2023["units"]
        # total revenue change
        total_change  = y2024["revenue"] - y2023["revenue"]

        results.append({
            "segment":       seg,
            "volume_effect": round(volume_effect, 4),
            "price_effect":  round(price_effect, 4),
            "total_change":  round(total_change, 4),
        })

    df = pd.DataFrame(results)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Volume Effect",
        x=df["segment"],
        y=df["volume_effect"],
        marker_color="#3395F6",
        opacity=0.85,
        text=[f"€{v:.2f}M" for v in df["volume_effect"]],
        textposition="outside",
    ))
    fig.add_trace(go.Bar(
        name="Price Effect",
        x=df["segment"],
        y=df["price_effect"],
        marker_color="#4440B5",
        opacity=0.85,
        text=[f"€{v:.2f}M" for v in df["price_effect"]],
        textposition="outside",
    ))
    fig.add_trace(go.Scatter(
        name="Total Revenue Change",
        x=df["segment"],
        y=df["total_change"],
        mode="markers",
        marker=dict(color="#FF9800", size=12, symbol="diamond"),
    ))

    fig.update_layout(
        title_text="Volume vs Price Contribution to Revenue Change (2023 → 2024)",
        barmode="relative",
        plot_bgcolor="#0f1117",
        paper_bgcolor="#0f1117",
        font_color="#cccccc",
        legend=dict(bgcolor="#1a1a2e"),
        yaxis_title="Revenue Effect (€M)",
    )
    fig.write_html("output/charts/S3_volume_price_contribution.html")
    fig.show()

# ------------------------------------------------------------------ #
#  SEGMENT GROWTH RATE — 2023 VS 2024                                 #
# ------------------------------------------------------------------ #
def chart_segment_growth_rate(sales_filepath: str = "data/bic_sales_data.csv"):
    raw = pd.read_csv(sales_filepath)
    raw["revenue"] = raw["units_millions"] * raw["unit_price_eur"]

    yearly = (
        raw.groupby(["year", "segment"])
        .agg(
            units   = ("units_millions", "sum"),
            revenue = ("revenue",        "sum")
        )
        .reset_index()
    )

    results = []
    for seg in SEGMENTS:
        y2023 = yearly[(yearly["year"] == 2023) & (yearly["segment"] == seg)].iloc[0]
        y2024 = yearly[(yearly["year"] == 2024) & (yearly["segment"] == seg)].iloc[0]

        revenue_growth = (y2024["revenue"] - y2023["revenue"]) / y2023["revenue"] * 100
        volume_growth  = (y2024["units"]   - y2023["units"])   / y2023["units"]   * 100

        results.append({
            "segment":       seg,
            "revenue_growth": round(revenue_growth, 2),
            "volume_growth":  round(volume_growth,  2),
        })

    df = pd.DataFrame(results).sort_values("revenue_growth", ascending=False)

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=["Revenue Growth Rate (%)", "Volume Growth Rate (%)"],
        shared_yaxes=True
    )

    # color bars green if positive, red if negative
    def bar_colors(values):
        return ["#4CAF50" if v >= 0 else "#F44336" for v in values]

    fig.add_trace(go.Bar(
        name="Revenue Growth",
        x=df["segment"],
        y=df["revenue_growth"],
        marker_color=bar_colors(df["revenue_growth"]),
        opacity=0.85,
        text=[f"{v:.1f}%" for v in df["revenue_growth"]],
        textposition="outside",
        showlegend=False,
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        name="Volume Growth",
        x=df["segment"],
        y=df["volume_growth"],
        marker_color=bar_colors(df["volume_growth"]),
        opacity=0.85,
        text=[f"{v:.1f}%" for v in df["volume_growth"]],
        textposition="outside",
        showlegend=False,
    ), row=1, col=2)

    fig.add_hline(y=0, line_color="#ffffff", line_width=0.8,
                  line_dash="dash", row=1, col=1)
    fig.add_hline(y=0, line_color="#ffffff", line_width=0.8,
                  line_dash="dash", row=1, col=2)

    fig.update_layout(
        title_text="Segment Growth Rate 2023 → 2024",
        plot_bgcolor="#0f1117",
        paper_bgcolor="#0f1117",
        font_color="#cccccc",
    )
    fig.update_yaxes(title_text="Growth (%)", col=1)
    fig.write_html("output/charts/S4_segment_growth_rate.html")
    fig.show()

#PRODUCTION BDG#
# ------------------------------------------------------------------ #
#  BEGINNING VS ENDING INVENTORY PER QUARTER                         #
# ------------------------------------------------------------------ #
def chart_inventory_position(
    sales_filepath:      str = "data/bic_sales_data.csv",
    production_filepath: str = "data/bic_production_data.csv"
):
    from src.production_bdg import compute_production_bdg

    _, quarterly = compute_production_bdg(sales_filepath, production_filepath)
    quarterly["period"] = quarterly["year"].astype(str) + " " + quarterly["quarter"]

    inv = (
        quarterly
        .groupby("period")[["beg_inv", "end_inv"]]
        .sum()
        .reset_index()
    )
    # preserve chronological order
    period_order = (
        quarterly[["year", "quarter"]]
        .drop_duplicates()
        .sort_values(["year", "quarter"])
        .apply(lambda r: f"{int(r['year'])} {r['quarter']}", axis=1)
        .tolist()
    )
    inv = inv.set_index("period").reindex(period_order).reset_index()
    inv["net_position"] = inv["end_inv"] - inv["beg_inv"]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Bar(
        name="Beginning Inventory",
        x=inv["period"],
        y=inv["beg_inv"],
        marker_color="#3395F6",
        opacity=0.85,
        text=[f"{v:.2f}M" for v in inv["beg_inv"]],
        textposition="inside",
    ), secondary_y=False)

    fig.add_trace(go.Bar(
        name="Ending Inventory",
        x=inv["period"],
        y=inv["end_inv"],
        marker_color="#4440B5",
        opacity=0.85,
        text=[f"{v:.2f}M" for v in inv["end_inv"]],
        textposition="inside",
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        name="Net Position (End − Beg)",
        x=inv["period"],
        y=inv["net_position"],
        mode="lines+markers",
        line=dict(color="#FF9800", width=2.5),
        marker=dict(
            size=8,
            color=["#4CAF50" if v >= 0 else "#F44336" for v in inv["net_position"]]
        ),
    ), secondary_y=True)

    fig.update_layout(
        title_text="Beginning vs Ending Inventory per Quarter",
        barmode="group",
        plot_bgcolor="#0f1117",
        paper_bgcolor="#0f1117",
        font_color="#cccccc",
        legend=dict(bgcolor="#1a1a2e"),
    )
    fig.update_yaxes(title_text="Units (millions)",        secondary_y=False)
    fig.update_yaxes(title_text="Net Inventory Position",  secondary_y=True)
    fig.update_xaxes(tickangle=45)
    fig.write_html("output/charts/P1_inventory_position.html")
    fig.show()


# ------------------------------------------------------------------ #
#  UNITS SOLD VS UNITS TO PRODUCE — GROUPED BAR PER SEGMENT          #
# ------------------------------------------------------------------ #
def chart_units_sold_vs_produced(
    sales_filepath:      str = "data/bic_sales_data.csv",
    production_filepath: str = "data/bic_production_data.csv"
):
    from src.production_bdg import compute_production_bdg

    _, quarterly = compute_production_bdg(sales_filepath, production_filepath)
    quarterly["period"] = quarterly["year"].astype(str) + " " + quarterly["quarter"]

    period_order = (
        quarterly[["year", "quarter"]]
        .drop_duplicates()
        .sort_values(["year", "quarter"])
        .apply(lambda r: f"{int(r['year'])} {r['quarter']}", axis=1)
        .tolist()
    )

    fig = make_subplots(
        rows=1, cols=len(SEGMENTS),
        subplot_titles=SEGMENTS,
        shared_yaxes=True
    )

    for col, (seg, color) in enumerate(zip(SEGMENTS, SEG_COLORS), start=1):
        sub = (
            quarterly[quarterly["segment"] == seg]
            .set_index("period")
            .reindex(period_order)
            .reset_index()
        )

        # production buffer = units_to_produce - units_sold
        sub["buffer"] = sub["units_to_produce"] - sub["units_sold"]

        fig.add_trace(go.Bar(
            name="Units Sold",
            x=sub["period"],
            y=sub["units_sold"],
            marker_color=color,
            opacity=0.9,
            text=[f"{v:.1f}M" for v in sub["units_sold"]],
            textposition="inside",
            showlegend=(col == 1),
        ), row=1, col=col)

        fig.add_trace(go.Bar(
            name="Production Buffer",
            x=sub["period"],
            y=sub["buffer"],
            marker_color="#FF9800",
            opacity=0.75,
            text=[f"{v:.2f}M" for v in sub["buffer"]],
            textposition="inside",
            showlegend=(col == 1),
        ), row=1, col=col)

    fig.update_layout(
        title_text="Units Sold vs Production Buffer by Segment",
        barmode="stack",
        plot_bgcolor="#0f1117",
        paper_bgcolor="#0f1117",
        font_color="#cccccc",
        legend=dict(bgcolor="#1a1a2e"),
    )
    fig.update_yaxes(title_text="Units (millions)", col=1)
    fig.update_xaxes(tickangle=45)
    fig.write_html("output/charts/P2_units_sold_vs_produced.html")
    fig.show()


# ------------------------------------------------------------------ #
#  PRODUCTION PRESSURE HEATMAP — 2023 VS 2024 SIDE BY SIDE           #
# ------------------------------------------------------------------ #
def chart_production_heatmap(
    sales_filepath:      str = "data/bic_sales_data.csv",
    production_filepath: str = "data/bic_production_data.csv"
):
    from src.production_bdg import compute_production_bdg

    monthly, _ = compute_production_bdg(sales_filepath, production_filepath)
    monthly["diff"] = monthly["units_to_produce"] - monthly["units_millions"]

    month_labels = (
        monthly.drop_duplicates("month_num")
        .sort_values("month_num")["month"]
        .tolist()
    )

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=["2023", "2024"],
        shared_yaxes=True
    )

    for col, year in enumerate([2023, 2024], start=1):
        sub   = monthly[monthly["year"] == year]
        pivot = (
            sub.pivot_table(index="segment", columns="month_num", values="diff")
            .reindex(columns=range(1, 13))
            .fillna(0)
        )

        fig.add_trace(go.Heatmap(
            z=pivot.values.tolist(),
            x=month_labels,
            y=pivot.index.tolist(),
            colorscale=[
                [0.0,  "#F44336"],   # red   — strong under-production
                [0.5,  "#FFEB3B"],   # yellow — neutral
                [1.0,  "#4CAF50"],   # green  — strong over-production
            ],
            zmid=0,
            text=[[f"{v:.2f}M" for v in row] for row in pivot.values],
            texttemplate="%{text}",
            textfont=dict(size=8),
            colorbar=dict(
                title="Units (M)",
                x=1.02 if col == 2 else 0.45,
                len=0.9
            ),
            showscale=(col == 2),
        ), row=1, col=col)

    fig.update_layout(
        title_text="Production Pressure Heatmap: Units to Produce − Units Sold",
        plot_bgcolor="#0f1117",
        paper_bgcolor="#0f1117",
        font_color="#cccccc",
        height=350,
    )
    fig.update_xaxes(tickangle=45)
    fig.write_html("output/charts/P3_production_heatmap.html")
    fig.show()

#Production Cost Budget
# ------------------------------------------------------------------ #
#  COST BREAKDOWN STACKED BAR — PER QUARTER SIDE BY SIDE             #
# ------------------------------------------------------------------ #
def chart_cost_breakdown_quarterly(
    production_filepath: str = "data/bic_production_data.csv",
    sales_filepath:      str = "data/bic_sales_data.csv",
    cost_filepath:       str = "data/bic_cost_drivers.csv"
):
    from src.costs_bdg import compute_production_cost_bdg

    cost_q, _ = compute_production_cost_bdg(production_filepath, sales_filepath, cost_filepath)
    cost_q["period"] = cost_q["year"].astype(str) + " " + cost_q["quarter"]

    period_order = (
        cost_q[["year", "quarter"]]
        .drop_duplicates()
        .sort_values(["year", "quarter"])
        .apply(lambda r: f"{int(r['year'])} {r['quarter']}", axis=1)
        .tolist()
    )

    cost_components = {
        "material_cost": {"label": "Material Cost",       "color": "#3395F6"},
        "labour_cost":   {"label": "Labour Cost",         "color": "#4440B5"},
        "var_overhead":  {"label": "Variable Overhead",   "color": "#FF9800"},
        "fix_overhead":  {"label": "Fixed Overhead",      "color": "#F44336"},
    }

    fig = make_subplots(
        rows=1, cols=len(SEGMENTS),
        subplot_titles=SEGMENTS,
        shared_yaxes=True
    )

    for col, seg in enumerate(SEGMENTS, start=1):
        sub = (
            cost_q[cost_q["segment"] == seg]
            .set_index("period")
            .reindex(period_order)
            .reset_index()
        )

        for comp, meta in cost_components.items():
            fig.add_trace(go.Bar(
                name=meta["label"],
                x=sub["period"],
                y=sub[comp].round(2),
                marker_color=meta["color"],
                opacity=0.85,
                text=[f"€{v:.2f}M" for v in sub[comp]],
                textposition="inside",
                textfont=dict(size=7),
                showlegend=(col == 1),
            ), row=1, col=col)

    fig.update_layout(
        title_text="Production Cost Breakdown by Segment — Quarterly",
        barmode="stack",
        plot_bgcolor="#0f1117",
        paper_bgcolor="#0f1117",
        font_color="#cccccc",
        legend=dict(bgcolor="#1a1a2e"),
        height=500,
    )
    fig.update_yaxes(title_text="Cost (€M)", col=1)
    fig.update_xaxes(tickangle=45)
    fig.write_html("output/charts/C1_cost_breakdown_quarterly.html")
    fig.show()


# ------------------------------------------------------------------ #
#  COST PER UNIT BY SEGMENT OVER QUARTERS — SIDE BY SIDE             #
# ------------------------------------------------------------------ #
def chart_cost_per_unit_trend(
    production_filepath: str = "data/bic_production_data.csv",
    sales_filepath:      str = "data/bic_sales_data.csv",
    cost_filepath:       str = "data/bic_cost_drivers.csv"
):
    from src.costs_bdg import compute_production_cost_bdg

    cost_q, _ = compute_production_cost_bdg(production_filepath, sales_filepath, cost_filepath)
    cost_q["period"]        = cost_q["year"].astype(str) + " " + cost_q["quarter"]
    cost_q["cost_per_unit"] = cost_q["total_cost"] / cost_q["units_to_produce"]

    # also split cost per unit by component
    cost_q["mat_per_unit"]   = cost_q["material_cost"] / cost_q["units_to_produce"]
    cost_q["lab_per_unit"]   = cost_q["labour_cost"]   / cost_q["units_to_produce"]
    cost_q["var_per_unit"]   = cost_q["var_overhead"]  / cost_q["units_to_produce"]
    cost_q["fix_per_unit"]   = cost_q["fix_overhead"]  / cost_q["units_to_produce"]

    period_order = (
        cost_q[["year", "quarter"]]
        .drop_duplicates()
        .sort_values(["year", "quarter"])
        .apply(lambda r: f"{int(r['year'])} {r['quarter']}", axis=1)
        .tolist()
    )

    # --- Chart 1: total cost per unit all segments on same plot ---
    fig1 = go.Figure()
    for seg, color in zip(SEGMENTS, SEG_COLORS):
        sub = (
            cost_q[cost_q["segment"] == seg]
            .set_index("period")
            .reindex(period_order)
            .reset_index()
        )
        fig1.add_trace(go.Scatter(
            name=seg,
            x=sub["period"],
            y=sub["cost_per_unit"].round(4),
            mode="lines+markers",
            line=dict(color=color, width=2.5),
            marker=dict(size=7),
            text=[f"€{v:.4f}" for v in sub["cost_per_unit"]],
            hovertemplate="%{x}<br>Cost/Unit: %{text}<extra></extra>",
        ))

    fig1.update_layout(
        title_text="Total Cost per Unit by Segment over Quarters",
        plot_bgcolor="#0f1117",
        paper_bgcolor="#0f1117",
        font_color="#cccccc",
        legend=dict(bgcolor="#1a1a2e"),
        yaxis_title="Cost per Unit (€)",
    )
    fig1.update_xaxes(tickangle=45)
    fig1.write_html("output/charts/C2a_cost_per_unit_total.html")
    fig1.show()

    # --- Chart 2: cost per unit decomposed per segment side by side ---
    components = {
        "mat_per_unit": {"label": "Material/Unit",        "color": "#3395F6"},
        "lab_per_unit": {"label": "Labour/Unit",          "color": "#4440B5"},
        "var_per_unit": {"label": "Variable Overhead/Unit","color": "#FF9800"},
        "fix_per_unit": {"label": "Fixed Overhead/Unit",  "color": "#F44336"},
    }

    fig2 = make_subplots(
        rows=1, cols=len(SEGMENTS),
        subplot_titles=SEGMENTS,
        shared_yaxes=True
    )

    for col, seg in enumerate(SEGMENTS, start=1):
        sub = (
            cost_q[cost_q["segment"] == seg]
            .set_index("period")
            .reindex(period_order)
            .reset_index()
        )
        for comp, meta in components.items():
            fig2.add_trace(go.Bar(
                name=meta["label"],
                x=sub["period"],
                y=sub[comp].round(4),
                marker_color=meta["color"],
                opacity=0.85,
                text=[f"€{v:.4f}" for v in sub[comp]],
                textposition="inside",
                textfont=dict(size=7),
                showlegend=(col == 1),
            ), row=1, col=col)

    fig2.update_layout(
        title_text="Cost per Unit Decomposition by Segment — Quarterly",
        barmode="stack",
        plot_bgcolor="#0f1117",
        paper_bgcolor="#0f1117",
        font_color="#cccccc",
        legend=dict(bgcolor="#1a1a2e"),
        height=500,
    )
    fig2.update_yaxes(title_text="Cost per Unit (€)", col=1)
    fig2.update_xaxes(tickangle=45)
    fig2.write_html("output/charts/C2b_cost_per_unit_decomposed.html")
    fig2.show()

# ------------------------------------------------------------------ #
#  REVENUE VS TOTAL COST VS EBIT — GROUPED BAR (side by side)        #
# ------------------------------------------------------------------ #
def chart_revenue_cost_ebit(
    sales_filepath:      str = "data/bic_sales_data.csv",
    production_filepath: str = "data/bic_production_data.csv",
    cost_filepath:       str = "data/bic_cost_drivers.csv",
    opex_filepath:       str = "data/operating_expenses.csv"
):
    from src.income_bdg import compute_income_bdg

    _, income_y = compute_income_bdg(
        sales_filepath, production_filepath, cost_filepath, opex_filepath
    )

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=["2023", "2024"],
        shared_yaxes=True
    )

    metrics = [
        ("revenue",    "Revenue",    "#3395F6"),
        ("total_cost", "Total Cost", "#F44336"),
        ("ebit",       "EBIT",       "#4CAF50"),
    ]

    for col, year in enumerate([2023, 2024], start=1):
        sub = income_y[income_y["year"] == year].sort_values("segment")
        for column, label, color in metrics:
            fig.add_trace(go.Bar(
                name=label,
                x=sub["segment"].tolist(),
                y=sub[column].tolist(),
                marker_color=color,
                opacity=0.85,
                text=[f"€{v:.1f}M" for v in sub[column]],
                textposition="outside",
                showlegend=(col == 1),
            ), row=1, col=col)

    # add cost-to-revenue ratio as a line on secondary axis
    fig2 = make_subplots(
        rows=1, cols=2,
        subplot_titles=["2023", "2024"],
        shared_yaxes=True,
        specs=[[{"secondary_y": True}, {"secondary_y": True}]]
    )

    for col, year in enumerate([2023, 2024], start=1):
        sub = income_y[income_y["year"] == year].sort_values("segment")
        sub = sub.copy()
        sub["cost_to_revenue"] = sub["total_cost"] / sub["revenue"] * 100

        for column, label, color in metrics:
            fig2.add_trace(go.Bar(
                name=label,
                x=sub["segment"].tolist(),
                y=sub[column].tolist(),
                marker_color=color,
                opacity=0.85,
                text=[f"€{v:.1f}M" for v in sub[column]],
                textposition="outside",
                showlegend=(col == 1),
            ), row=1, col=col, secondary_y=False)

        fig2.add_trace(go.Scatter(
            name="Cost / Revenue %",
            x=sub["segment"].tolist(),
            y=sub["cost_to_revenue"].tolist(),
            mode="lines+markers",
            line=dict(color="#FF9800", width=2, dash="dot"),
            marker=dict(size=8, symbol="diamond"),
            text=[f"{v:.1f}%" for v in sub["cost_to_revenue"]],
            hovertemplate="%{text}<extra>Cost/Revenue</extra>",
            showlegend=(col == 1),
        ), row=1, col=col, secondary_y=True)

    fig2.update_layout(
        title_text="Revenue vs Total Cost vs EBIT by Segment",
        barmode="group",
        plot_bgcolor="#0f1117",
        paper_bgcolor="#0f1117",
        font_color="#cccccc",
        legend=dict(bgcolor="#1a1a2e"),
    )
    fig2.update_yaxes(title_text="€ Millions",       secondary_y=False, col=1)
    fig2.update_yaxes(title_text="Cost / Revenue %", secondary_y=True,  col=2)
    fig2.update_xaxes(tickangle=15)
    fig2.write_html("output/charts/C3_revenue_cost_ebit.html")
    fig2.show()

if __name__ == "__main__":
    chart_sales_units_stacked()
    chart_sales_revenue_monthly()
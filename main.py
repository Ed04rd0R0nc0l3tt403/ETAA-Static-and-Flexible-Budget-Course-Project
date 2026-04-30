from src.sales_bdg      import compute_sales_bdg, export_sales_bdg_excel
from src.production_bdg import compute_production_bdg, export_production_bdg_excel
from src.costs_bdg      import compute_production_cost_bdg, export_production_cost_bdg_excel
from src.cash_flow_bdg  import compute_cash_flow_bdg
from src.income_bdg     import compute_income_bdg

from src.charts import (
    chart_sales_units_stacked,
    chart_sales_revenue_monthly,
    chart_volume_price_contribution,
    chart_segment_growth_rate,
    chart_inventory_position,
    chart_units_sold_vs_produced,
    chart_production_heatmap,
    chart_cost_breakdown_quarterly,
    chart_cost_per_unit_trend,
    chart_revenue_cost_ebit,
)

def main():
    # --- Sales ---
    sales_quarterly, sales_yearly, total_revenue = compute_sales_bdg()
    print("=== Sales Budget — Quarterly ===")
    print(sales_quarterly.to_string(index=False))
    print("\n=== Sales Budget — Yearly Revenue ===")
    print(sales_yearly.to_string(index=False))
    print(f"\nTotal Revenue (all years): €{total_revenue:.2f}M")

    # --- Production ---
    _, prod_quarterly = compute_production_bdg()
    prod_yearly = (
        prod_quarterly
        .groupby(["year", "segment"])
        .agg(
            units_sold       = ("units_sold",       "sum"),
            beg_inv          = ("beg_inv",           "first"),
            end_inv          = ("end_inv",           "last"),
            units_to_produce = ("units_to_produce",  "sum")
        )
        .reset_index()
    )
    print("\n=== Production Budget — Quarterly ===")
    print(prod_quarterly.to_string(index=False))
    print("\n=== Production Budget — Yearly ===")
    print(prod_yearly.to_string(index=False))

    # --- Production Cost ---
    cost_quarterly, cost_yearly = compute_production_cost_bdg()
    print("\n=== Production Cost Budget — Quarterly ===")
    print(cost_quarterly.to_string(index=False))
    print("\n=== Production Cost Budget — Yearly ===")
    print(cost_yearly.to_string(index=False))

    # --- Cash Flow ---
    collections, payments, net_cash = compute_cash_flow_bdg()
    print("\n=== Cash Collections by Segment ===")
    print(collections.to_string(index=False))
    print("\n=== Cash Payments by Segment & Category ===")
    print(payments.to_string(index=False))
    print("\n=== Net Cash Position — Quarterly ===")
    print(net_cash.to_string(index=False))

    # --- Budgeted Income ---
    income_q, income_y = compute_income_bdg()
    print("\n=== Budgeted Income Statement — Quarterly ===")
    cols = ["year", "quarter", "segment",
            "revenue", "total_cost", "gross_profit", "gross_profit_margin",
            "marketing", "rd", "admin", "total_opex",
            "ebit", "ebit_margin"]
    print(income_q[cols].to_string(index=False))
    print("\n=== Budgeted Income Statement — Yearly ===")
    print(income_y.to_string(index=False))

    # --- Charts: Sales ---
    chart_sales_units_stacked()
    chart_sales_revenue_monthly()
    chart_volume_price_contribution()
    chart_segment_growth_rate()

    # --- Charts: Production ---
    chart_inventory_position()
    chart_units_sold_vs_produced()
    chart_production_heatmap()

    # --- Charts: Production Cost ---
    chart_cost_breakdown_quarterly()
    chart_cost_per_unit_trend()
    chart_revenue_cost_ebit()

    # --- Excel Export ---
    export_sales_bdg_excel()
    export_production_bdg_excel()
    export_production_cost_bdg_excel()

if __name__ == "__main__":
    main()
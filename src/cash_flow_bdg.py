import pandas as pd
from src.costs_bdg import compute_production_cost_bdg

def compute_cash_flow_bdg(
    sales_filepath:      str = "data/bic_sales_data.csv",
    production_filepath: str = "data/bic_production_data.csv",
    cost_filepath:       str = "data/bic_cost_drivers.csv",
    policies_filepath:   str = "data/bic_cash_policies.csv"
):
    # --- Load data ---
    policies_df = pd.read_csv(policies_filepath)

    raw_sales = pd.read_csv(sales_filepath)
    raw_sales["revenue_eur_millions"] = raw_sales["units_millions"] * raw_sales["unit_price_eur"]
    sales_df = (
        raw_sales
        .groupby(["year", "quarter", "segment"])["revenue_eur_millions"]
        .sum()
        .reset_index()
    )

    cost_q, _ = compute_production_cost_bdg(production_filepath, sales_filepath, cost_filepath)

    # Split policies by type
    collection = policies_df[policies_df["policy_type"] == "Collection"].set_index("category")
    payment    = policies_df[policies_df["policy_type"] == "Payment"].set_index("category")

    def offset_quarter(q, y, offset):
        """Return (quarter_label, year) shifted by offset quarters."""
        new_q = q + offset
        extra_years, new_q = divmod(new_q - 1, 4)
        return f"Q{new_q + 1}", y + extra_years

    # ------------------------------------------------------------------ #
    #  CASH COLLECTIONS                                                    #
    # ------------------------------------------------------------------ #
    collection_rows = []

    for _, row in sales_df.iterrows():
        seg     = row["segment"]
        year    = int(row["year"])
        q_num   = int(row["quarter"][1])
        revenue = row["revenue_eur_millions"]
        p       = collection.loc[seg]

        q0, y0 = offset_quarter(q_num, year, 0)
        q1, y1 = offset_quarter(q_num, year, 1)
        q2, y2 = offset_quarter(q_num, year, 2)

        collection_rows += [
            {"year": y0, "quarter": q0, "segment": seg, "cash_inflow": revenue * p["current_month_pct"]},
            {"year": y1, "quarter": q1, "segment": seg, "cash_inflow": revenue * p["following_month_pct"]},
            {"year": y2, "quarter": q2, "segment": seg, "cash_inflow": revenue * p["two_months_out_pct"]},
        ]

    collections_df = (
        pd.DataFrame(collection_rows)
        .groupby(["year", "quarter", "segment"])["cash_inflow"]
        .sum()
        .reset_index()
    )

    # ------------------------------------------------------------------ #
    #  CASH PAYMENTS                                                       #
    # ------------------------------------------------------------------ #
    payment_rows = []

    for _, row in cost_q.iterrows():
        year  = int(row["year"])
        q_num = int(row["quarter"][1])
        seg   = row["segment"]

        mat_p = payment.loc["Direct Materials"]
        loh_p = payment.loc["Labor & Overhead"]

        q0, y0 = offset_quarter(q_num, year, 0)
        q1, y1 = offset_quarter(q_num, year, 1)

        mat = row["material_cost"]
        loh = row["labour_cost"] + row["total_overhead"]

        payment_rows += [
            {"year": y0, "quarter": q0, "segment": seg, "category": "Direct Materials",
             "cash_outflow": mat * mat_p["current_month_pct"]},
            {"year": y1, "quarter": q1, "segment": seg, "category": "Direct Materials",
             "cash_outflow": mat * mat_p["following_month_pct"]},
            {"year": y0, "quarter": q0, "segment": seg, "category": "Labor & Overhead",
             "cash_outflow": loh * loh_p["current_month_pct"]},
        ]

    payments_df = (
        pd.DataFrame(payment_rows)
        .groupby(["year", "quarter", "segment", "category"])["cash_outflow"]
        .sum()
        .reset_index()
    )

    # ------------------------------------------------------------------ #
    #  NET CASH POSITION                                                   #
    # ------------------------------------------------------------------ #
    total_inflows  = collections_df.groupby(["year", "quarter"])["cash_inflow"].sum().reset_index()
    total_outflows = payments_df.groupby(["year", "quarter"])["cash_outflow"].sum().reset_index()

    net_cash = (
        total_inflows
        .merge(total_outflows, on=["year", "quarter"], how="outer")
        .fillna(0)
        .assign(net_cash=lambda df: df["cash_inflow"] - df["cash_outflow"])
        .sort_values(["year", "quarter"])
        .reset_index(drop=True)
    )

    return collections_df, payments_df, net_cash
import pandas as pd
from src.costs_bdg import compute_production_cost_bdg

def compute_income_bdg(
    sales_filepath:      str = "data/bic_sales_data.csv",
    production_filepath: str = "data/bic_production_data.csv",
    cost_filepath:       str = "data/bic_cost_drivers.csv",
    opex_filepath:       str = "data/operating_expenses.csv"
):
    # --- Load data ---
    opex_df = pd.read_csv(opex_filepath).set_index("segment")

    raw_sales = pd.read_csv(sales_filepath)
    raw_sales["revenue"] = raw_sales["units_millions"] * raw_sales["unit_price_eur"]
    sales_q = (
        raw_sales
        .groupby(["year", "quarter", "segment"])["revenue"]
        .sum()
        .reset_index()
    )

    cost_q, _ = compute_production_cost_bdg(production_filepath, sales_filepath, cost_filepath)

    # --- Merge revenue and production cost ---
    df = sales_q.merge(
        cost_q[["year", "quarter", "segment", "total_cost"]],
        on=["year", "quarter", "segment"],
        how="left"
    )

    # ------------------------------------------------------------------ #
    #  GROSS PROFIT                                                        #
    # ------------------------------------------------------------------ #
    df["gross_profit"]        = df["revenue"] - df["total_cost"]
    df["gross_profit_margin"] = df["gross_profit"] / df["revenue"]

    # ------------------------------------------------------------------ #
    #  OPERATING EXPENSES                                                  #
    # ------------------------------------------------------------------ #
    df["marketing"]  = df["revenue"] * df.apply(lambda r: opex_df.loc[r["segment"], "marketing_rate_revenue"], axis=1)
    df["rd"]         = df["revenue"] * df.apply(lambda r: opex_df.loc[r["segment"], "rd_rate_revenue"], axis=1)
    df["admin"]      = df.apply(lambda r: opex_df.loc[r["segment"], "admin_fixed_monthly"] * 3, axis=1)  # 3 months per quarter
    df["total_opex"] = df["marketing"] + df["rd"] + df["admin"]

    # ------------------------------------------------------------------ #
    #  OPERATING INCOME (EBIT)                                            #
    # ------------------------------------------------------------------ #
    df["ebit"]        = df["gross_profit"] - df["total_opex"]
    df["ebit_margin"] = df["ebit"] / df["revenue"]

    quarterly_df = df.sort_values(["year", "quarter", "segment"]).reset_index(drop=True)

    # --- Yearly aggregation ---
    yearly_df = (
        quarterly_df
        .groupby(["year", "segment"])
        .agg(
            revenue          = ("revenue",          "sum"),
            total_cost       = ("total_cost",        "sum"),
            gross_profit     = ("gross_profit",      "sum"),
            marketing        = ("marketing",         "sum"),
            rd               = ("rd",               "sum"),
            admin            = ("admin",             "sum"),
            total_opex       = ("total_opex",        "sum"),
            ebit             = ("ebit",              "sum"),
        )
        .assign(
            gross_profit_margin = lambda d: d["gross_profit"] / d["revenue"],
            ebit_margin         = lambda d: d["ebit"]         / d["revenue"],
        )
        .reset_index()
    )

    return quarterly_df, yearly_df
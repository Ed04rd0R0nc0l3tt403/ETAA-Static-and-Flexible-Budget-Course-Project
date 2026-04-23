import pandas as pd
from src.production_bdg import compute_production_bdg

def compute_production_cost_bdg(
    production_filepath: str = "data/bic_production_data.csv",
    sales_filepath:      str = "data/bic_sales_data.csv",
    cost_filepath:       str = "data/bic_cost_drivers.csv"
):
    _, quarterly = compute_production_bdg(sales_filepath, production_filepath)
    cost_df      = pd.read_csv(cost_filepath).set_index("segment")

    rows = []
    for _, row in quarterly.iterrows():
        seg      = row["segment"]
        units    = row["units_to_produce"]          # millions of units
        months   = 3                                 # months per quarter

        mat_cost      = units * cost_df.loc[seg, "mat_cost_unit"]
        labour_cost   = units * cost_df.loc[seg, "labor_cost_unit"]
        var_overhead  = units * cost_df.loc[seg, "var_overhead_unit"]
        fix_overhead  = cost_df.loc[seg, "fixed_overhead_monthly"] * months   # €, not scaled

        total_overhead     = var_overhead + fix_overhead
        total_cost         = mat_cost + labour_cost + total_overhead

        rows.append({
            "year":             row["year"],
            "quarter":          row["quarter"],
            "segment":          seg,
            "units_to_produce": units,
            "material_cost":    mat_cost,
            "labour_cost":      labour_cost,
            "var_overhead":     var_overhead,
            "fix_overhead":     fix_overhead,
            "total_overhead":   total_overhead,
            "total_cost":       total_cost,
        })

    quarterly_df = pd.DataFrame(rows)

    # Yearly aggregation
    yearly_df = (
        quarterly_df
        .groupby(["year", "segment"])
        .agg(
            units_to_produce = ("units_to_produce", "sum"),
            material_cost    = ("material_cost",    "sum"),
            labour_cost      = ("labour_cost",      "sum"),
            var_overhead     = ("var_overhead",     "sum"),
            fix_overhead     = ("fix_overhead",     "sum"),
            total_overhead   = ("total_overhead",   "sum"),
            total_cost       = ("total_cost",       "sum"),
        )
        .reset_index()
    )

    return quarterly_df, yearly_df
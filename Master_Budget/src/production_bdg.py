import pandas as pd

def compute_production_bdg(
    sales_filepath: str = "data/bic_sales_data.csv",
    production_filepath: str = "data/bic_production_data.csv"
):
    sales_df = pd.read_csv(sales_filepath).sort_values(["segment", "year", "month_num"]).reset_index(drop=True)
    rates_df = pd.read_csv(production_filepath).set_index("segment")

    # Last month of each quarter → last month of next quarter
    quarter_end_to_next = {3: 6, 6: 9, 9: 12, 12: 3}
    quarter_end_months = set(quarter_end_to_next.keys())

    results = []

    for segment, group in sales_df.groupby("segment"):
        group = group.sort_values(["year", "month_num"]).reset_index(drop=True)
        end_inv_rate = rates_df.loc[segment, "end_inv_rate"]
        beg_inv_rate = rates_df.loc[segment, "beg_inv_rate"]

        def get_qty(year, month):
            """Lookup quantity for a specific year/month within this segment."""
            match = group[(group["year"] == year) & (group["month_num"] == month)]
            return float(match["units_millions"].values[0]) if not match.empty else None

        # --- Ending Inventory ---
        end_inv_list = []
        for _, row in group.iterrows():
            month = int(row["month_num"])
            year  = int(row["year"])

            if month in quarter_end_months:
                # Last month of quarter → use last month of next quarter
                next_end_month = quarter_end_to_next[month]
                next_year = year + 1 if month == 12 else year
                qty = get_qty(next_year, next_end_month)
            else:
                # Regular month → next month
                qty = get_qty(year, month + 1)

            # Fallback: if next month has no data for this segment, use current qty
            end_inv_list.append((qty if qty is not None else row["units_millions"]) * end_inv_rate)

        group["end_inv"] = end_inv_list

        # --- Beginning Inventory ---
        beg_inv_list = []
        for i in range(len(group)):
            if i == 0:
                beg_inv_list.append(group.iloc[0]["units_millions"] * beg_inv_rate)
            else:
                beg_inv_list.append(group.iloc[i - 1]["end_inv"])   # prev month end_inv

        group["beg_inv"] = beg_inv_list

        # --- Units to Produce ---
        group["units_to_produce"] = group["units_millions"] + group["end_inv"] - group["beg_inv"]

        results.append(group)

    monthly_df = (
        pd.concat(results)
        .sort_values(["year", "month_num", "segment"])
        .reset_index(drop=True)
    )

    # --- Quarterly Aggregation ---
    quarterly_rows = []
    for (year, quarter, segment), g in monthly_df.groupby(["year", "quarter", "segment"]):
        g = g.sort_values("month_num")
        quarterly_rows.append({
            "year":             year,
            "quarter":          quarter,
            "segment":          segment,
            "units_sold":       g["units_millions"].sum(),
            "beg_inv":          g["beg_inv"].iloc[0],    # first month of quarter
            "end_inv":          g["end_inv"].iloc[-1],   # last month of quarter
            "units_to_produce": g["units_millions"].sum() + g["end_inv"].iloc[-1] - g["beg_inv"].iloc[0],
        })

    quarterly_df = (
        pd.DataFrame(quarterly_rows)
        .sort_values(["year", "quarter", "segment"])
        .reset_index(drop=True)
    )

    return monthly_df, quarterly_df
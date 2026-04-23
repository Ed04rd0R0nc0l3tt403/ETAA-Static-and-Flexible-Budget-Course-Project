import pandas as pd

def compute_sales_bdg(filepath: str = "data/bic_sales_data.csv"):
    df = pd.read_csv(filepath)
    df["revenue"] = df["units_millions"] * df["unit_price_eur"]

    quarterly = (
        df.groupby(["year", "quarter"])["revenue"]
        .sum()
        .reset_index()
    )
    # rename AFTER reset_index, when the column is called "revenue"
    quarterly.rename(columns={"revenue": "revenue_eur_millions"}, inplace=True)

    total_revenue = quarterly["revenue_eur_millions"].sum()

    return quarterly, total_revenue
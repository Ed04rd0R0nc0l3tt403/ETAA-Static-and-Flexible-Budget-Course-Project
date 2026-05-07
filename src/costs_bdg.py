import pandas as pd
from src.production_bdg import compute_production_bdg

from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

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
        units    = row["units_to_produce"]          
        months   = 3                                

        mat_cost      = units * cost_df.loc[seg, "mat_cost_unit"]
        labour_cost   = units * cost_df.loc[seg, "labor_cost_unit"]
        var_overhead  = units * cost_df.loc[seg, "var_overhead_unit"]
        fix_overhead  = cost_df.loc[seg, "fixed_overhead_monthly"] * months / 1_000_000  # €, not scaled

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

def export_production_cost_bdg_excel(
    production_filepath: str = "data/bic_production_data.csv",
    sales_filepath:      str = "data/bic_sales_data.csv",
    cost_filepath:       str = "data/bic_cost_drivers.csv",
    output_path:         str = "output/sales_budget.xlsx"
):
    quarterly_df, yearly_df = compute_production_cost_bdg(
        production_filepath, sales_filepath, cost_filepath
    )

    wb = load_workbook(output_path)

    if "Production Cost Budget" in wb.sheetnames:
        del wb["Production Cost Budget"]
    ws = wb.create_sheet("Production Cost Budget")

    # --- Styles ---
    header_font  = Font(name="Arial", bold=True, color="FFFFFF")
    header_fill  = PatternFill("solid", start_color="1F4E79")
    section_fill = PatternFill("solid", start_color="2E75B6")
    total_fill   = PatternFill("solid", start_color="D6E4F0")
    total_font   = Font(name="Arial", bold=True, color="000000")
    center       = Alignment(horizontal="center")
    thin         = Side(style="thin", color="CCCCCC")
    border       = Border(left=thin, right=thin, top=thin, bottom=thin)

    def style_cell(cell, font=None, fill=None, alignment=None, number_format=None):
        if font:          cell.font          = font
        if fill:          cell.fill          = fill
        if alignment:     cell.alignment     = alignment
        if number_format: cell.number_format = number_format
        cell.border = border

    # --- Title ---
    ws.merge_cells("A1:J1")
    ws["A1"] = "BIC Corporation — Production Cost Budget"
    ws["A1"].font      = Font(name="Arial", bold=True, size=14, color="1F4E79")
    ws["A1"].alignment = Alignment(horizontal="center")
    ws.row_dimensions[1].height = 25

    # ------------------------------------------------------------------ #
    #  SECTION 1 — QUARTERLY DETAIL                                        #
    # ------------------------------------------------------------------ #
    ws.append([])
    ws.append(["QUARTERLY DETAIL"] + [""] * 9)
    ws[f"A{ws.max_row}"].font = Font(name="Arial", bold=True, color="FFFFFF")
    ws[f"A{ws.max_row}"].fill = section_fill

    q_headers = [
        "Year", "Quarter", "Segment", "Units to Produce (M)",
        "Material Cost (€M)", "Labour Cost (€M)",
        "Var. Overhead (€M)", "Fix. Overhead (€M)",
        "Total Overhead (€M)", "Total Cost (€M)"
    ]
    ws.append(q_headers)
    for col in range(1, len(q_headers) + 1):
        style_cell(ws.cell(ws.max_row, col),
                   font=header_font, fill=header_fill, alignment=center)

    q_sorted = quarterly_df.sort_values(["year", "quarter", "segment"])
    for _, row in q_sorted.iterrows():
        r = ws.max_row + 1
        ws.cell(r, 1).value  = int(row["year"])
        ws.cell(r, 2).value  = row["quarter"]
        ws.cell(r, 3).value  = row["segment"]
        ws.cell(r, 4).value  = round(row["units_to_produce"], 4)
        ws.cell(r, 5).value  = round(row["material_cost"],    4)
        ws.cell(r, 6).value  = round(row["labour_cost"],      4)
        ws.cell(r, 7).value  = round(row["var_overhead"],     4)
        ws.cell(r, 8).value  = round(row["fix_overhead"],     4)
        ws.cell(r, 9).value  = round(row["total_overhead"],   4)
        ws.cell(r, 10).value = round(row["total_cost"],       4)
        for col in range(1, 11):
            style_cell(ws.cell(r, col),
                       number_format='#,##0.0000;(#,##0.0000);-')

    # ------------------------------------------------------------------ #
    #  SECTION 2 — YEARLY SUMMARY                                          #
    # ------------------------------------------------------------------ #
    ws.append([])
    ws.append(["YEARLY SUMMARY"] + [""] * 8)
    ws[f"A{ws.max_row}"].font = Font(name="Arial", bold=True, color="FFFFFF")
    ws[f"A{ws.max_row}"].fill = section_fill

    y_headers = [
        "Year", "Segment", "Units to Produce (M)",
        "Material Cost (€M)", "Labour Cost (€M)",
        "Var. Overhead (€M)", "Fix. Overhead (€M)",
        "Total Overhead (€M)", "Total Cost (€M)"
    ]
    ws.append(y_headers)
    for col in range(1, len(y_headers) + 1):
        style_cell(ws.cell(ws.max_row, col),
                   font=header_font, fill=header_fill, alignment=center)

    y_sorted = yearly_df.sort_values(["year", "segment"])
    for _, row in y_sorted.iterrows():
        r = ws.max_row + 1
        ws.cell(r, 1).value = int(row["year"])
        ws.cell(r, 2).value = row["segment"]
        ws.cell(r, 3).value = round(row["units_to_produce"], 4)
        ws.cell(r, 4).value = round(row["material_cost"],    4)
        ws.cell(r, 5).value = round(row["labour_cost"],      4)
        ws.cell(r, 6).value = round(row["var_overhead"],     4)
        ws.cell(r, 7).value = round(row["fix_overhead"],     4)
        ws.cell(r, 8).value = round(row["total_overhead"],   4)
        ws.cell(r, 9).value = round(row["total_cost"],       4)
        for col in range(1, 10):
            style_cell(ws.cell(r, col),
                       number_format='#,##0.0000;(#,##0.0000);-')

    # ------------------------------------------------------------------ #
    #  SECTION 3 — YEARLY TOTALS ACROSS SEGMENTS                           #
    # ------------------------------------------------------------------ #
    ws.append([])
    ws.append(["YEARLY TOTALS"] + [""] * 4)
    ws[f"A{ws.max_row}"].font = Font(name="Arial", bold=True, color="FFFFFF")
    ws[f"A{ws.max_row}"].fill = section_fill

    t_headers = [
        "Year", "Total Material (€M)", "Total Labour (€M)",
        "Total Overhead (€M)", "Total Cost (€M)"
    ]
    ws.append(t_headers)
    for col in range(1, len(t_headers) + 1):
        style_cell(ws.cell(ws.max_row, col),
                   font=header_font, fill=header_fill, alignment=center)

    for year in sorted(yearly_df["year"].unique()):
        sub = yearly_df[yearly_df["year"] == year]
        r   = ws.max_row + 1
        ws.cell(r, 1).value = int(year)
        ws.cell(r, 2).value = round(sub["material_cost"].sum(),  4)
        ws.cell(r, 3).value = round(sub["labour_cost"].sum(),    4)
        ws.cell(r, 4).value = round(sub["total_overhead"].sum(), 4)
        ws.cell(r, 5).value = round(sub["total_cost"].sum(),     4)
        for col in range(1, 6):
            style_cell(ws.cell(r, col),
                       font=total_font, fill=total_fill,
                       number_format='#,##0.0000;(#,##0.0000);-')

    # --- Column widths ---
    col_widths = [8, 10, 22, 22, 20, 20, 20, 20, 22, 18]
    for i, width in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = width

    wb.save(output_path)
    print(f"Production cost budget exported to '{output_path}' — sheet: Production Cost Budget")
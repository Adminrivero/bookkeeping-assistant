from src.export import SpreadsheetExporter

def test_add_annual_summary_section_basic():
    exporter = SpreadsheetExporter()
    totals_row = 100

    # Call the helper
    exporter.add_annual_summary_section(totals_row, separation=1)

    start = totals_row + 2
    top_row = start
    bottom_row = start + 1

    # Merged left cell exists and contains label
    merged_range = f"G{top_row}:G{bottom_row}"
    assert any(str(rng) == merged_range for rng in exporter.ws.merged_cells.ranges)
    assert exporter.ws[f"G{top_row}"].value is not None and "ANNUAL" in exporter.ws[f"G{top_row}"].value

    # Headers present
    assert exporter.ws[f"H{top_row}"].value == "INCOME"
    assert exporter.ws[f"I{top_row}"].value == "EXPENSES"
    assert exporter.ws[f"J{top_row}"].value == "NET"

    # Formulas reference totals_row
    assert exporter.ws[f"H{bottom_row}"].value == f"=H{totals_row}"
    assert exporter.ws[f"I{bottom_row}"].value == f"=SUM(I{totals_row}:W{totals_row})"
    assert exporter.ws[f"J{bottom_row}"].value == f"=H{bottom_row}-I{bottom_row}"

    # NET cell has double bottom border
    net = exporter.ws[f"J{bottom_row}"]
    assert getattr(net.border.bottom, "style") == "double"

    # Conditional formatting targets the NET cell (rough membership check)
    cf_dict = getattr(exporter.ws.conditional_formatting, "_cf_rules", {})
    cf_keys = [str(k) for k in cf_dict.keys()]
    assert any(f"J{bottom_row}" in k for k in cf_keys)

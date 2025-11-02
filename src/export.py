"""
export.py

Handles exporting classified transactions into a formatted Excel workbook
based on the schema defined in spreadsheet_schema.py.
"""

from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from spreadsheet_schema import get_schema

class SpreadsheetExporter:
    """
    Builds and populates the bookkeeping spreadsheet.
    """
    
    wb: Workbook
    ws: Worksheet

    def __init__(self):
        self.wb = Workbook()
        self.ws = self.wb.active # type: ignore
        self.ws.title = "Bookkeeping"

    def build_headers(self):
        """Create header row using schema definitions."""
        schema = get_schema()
        for idx, col in enumerate(schema, start=1):
            cell = self.ws.cell(row=3, column=idx, value=col.name)
            # Apply header style (simplified for now)
            cell.font = Font(bold=True, name="Calibri", size=12, color="000000")
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.fill = PatternFill("solid", fgColor="9BC2E6")
            thin = Side(border_style="thin", color="000000")
            cell.border = Border(top=thin, bottom=thin, left=thin, right=thin)

    def write_transaction(self, row_idx: int, transaction: dict):
        """
        Write a single classified transaction into the spreadsheet.
        transaction: dict with keys matching schema column names.
        """
        schema = get_schema()
        for idx, col in enumerate(schema, start=1):
            value = transaction.get(col.name)
            if col.formula_template and value is None:
                # Insert formula dynamically
                formula = col.formula_template.format(row=row_idx)
                self.ws.cell(row=row_idx, column=idx, value=formula)
            else:
                self.ws.cell(row=row_idx, column=idx, value=value)

    def finalize_totals_row(self, start_row: int, end_row: int):
        """Add totals row at the bottom for numeric columns (C through AA)."""
        schema = get_schema()
        totals_row = end_row + 1
        for idx, col in enumerate(schema, start=1):
            if col.letter >= "C" and col.letter <= "AA":
                formula = f"=SUM({col.letter}{start_row}:{col.letter}{end_row})"
                self.ws.cell(row=totals_row, column=idx, value=formula)

    def save(self, filename: str):
        """Save the workbook to disk."""
        self.wb.save(filename)

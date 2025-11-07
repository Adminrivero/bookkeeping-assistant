"""
export.py

Handles exporting classified transactions into a formatted Excel workbook
based on the schema defined in spreadsheet_schema.py.
"""

from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from src.spreadsheet_schema import get_schema

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
        self.highlight_fill = PatternFill("solid", fgColor="FFFF99")
        self.thin_border = Border(
            top=Side(border_style="thin", color="000000"),
            bottom=Side(border_style="thin", color="000000"),
            left=Side(border_style="thin", color="000000"),
            right=Side(border_style="thin", color="000000")
        )

    def build_headers(self):
        """Create header row using schema definitions."""
        schema = get_schema()
        for idx, col in enumerate(schema, start=1):
            self.ws.column_dimensions[col.letter].width = col.width if col.width else 15.0
            cell = self.ws.cell(row=3, column=idx, value=col.name)
            # Apply header style (simplified for now)
            cell.font = Font(bold=True, name="Calibri", size=12, color="000000")
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.fill = PatternFill("solid", fgColor="9BC2E6")
            thin = Side(border_style="thin", color="000000")
            thick = Side(border_style="thick", color="000000")
            double = Side(border_style="double", color="000000")
            cell.border = Border(top=double, bottom=thick, left=thin, right=thin)

    def write_transaction(self, row_idx: int, transaction: dict):
        """
        Write a single classified transaction into the spreadsheet.
        transaction: dict with keys matching schema column names.
        """
        schema = get_schema()
        for idx, col in enumerate(schema, start=1):
            value = transaction.get(col.name)
            cell = self.ws.cell(row=row_idx, column=idx)
            if col.formula_template and value is None:
                # Insert formula dynamically
                formula = col.formula_template.format(row=row_idx)
                self.ws.cell(row=row_idx, column=idx, value=formula)
            else:
                self.ws.cell(row=row_idx, column=idx, value=value)
            # Apply highlighting and borders if manual review flag is set
            if transaction.get("highlight"):
                cell.fill = self.highlight_fill
            cell.border = self.thin_border

    def finalize_totals_row(self, start_row: int, end_row: int):
        """Add totals row at the bottom for numeric columns (C through AA)."""
        schema = get_schema()
        totals_row = end_row + 1
        for idx, col in enumerate(schema, start=1):
            if col.letter >= "C" and col.letter <= "AA":
                formula = f"=SUM({col.letter}{start_row}:{col.letter}{end_row})"
                cell = self.ws.cell(row=totals_row, column=idx, value=formula)
                # Apply bold font for visibility
                cell.font = Font(bold=True)
            elif col.name == "Item":
                # Add "Totals" label for visibility
                cell = self.ws.cell(row=totals_row, column=idx, value="Totals")
                cell.font = Font(bold=True)

    def save(self, filename: str):
        """Save the workbook to disk."""
        self.wb.save(filename)

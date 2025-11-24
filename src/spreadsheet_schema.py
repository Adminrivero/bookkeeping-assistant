"""
spreadsheet_schema.py

Defines the bookkeeping spreadsheet schema (28 columns) with formatting metadata.
This schema is consumed by the exporter to generate headers, apply styles,
and insert formulas dynamically.
"""

from dataclasses import dataclass
from typing import Optional, Dict, List

@dataclass
class ColumnSchema:
    letter: str
    name: str
    explanation: str
    data_format: Dict
    formula_template: Optional[str] = None  # For TOTAL column
    width: Optional[float] = None  # Column width in Excel units

# --------------------------
# Shared Styles
# --------------------------

HEADER_STYLE = {
    "number": {"category": "Text"},
    "font": {"family": "Calibri (Body)", "style": "Bold", "size": 12, "color": "#000000"},
    "text_alignment": {"horizontal": "Center", "vertical": "Bottom"},
    "text_control": "Wrap text",
    "border": "Top and Thick Bottom Border",
    "fill_color": "#9BC2E6",
}

EXPENSE_STYLE = {
    "number": {"category": "Currency", "decimal_places": 2, "symbol": "$"},
    "font": {"family": "Calibri (Body)", "style": "Bold", "size": 11, "color": "#000000"},
    "text_alignment": {"horizontal": "Center", "vertical": "Bottom"},
    "border": "Outside Borders",
    "fill_color": "No Color",
}

TEXT_STYLE = {
    "number": {"category": "Text"},
    "font": {"family": "Calibri (Body)", "style": "Bold", "size": 11, "color": "#000000"},
    "text_alignment": {"horizontal": "Center", "vertical": "Bottom"},
    "border": "Outside Borders",
    "fill_color": "No Color",
}

DATE_STYLE = {
    "number": {"category": "Date", "type": "March 14, 2012"},
    "font": {"family": "Calibri (Body)", "style": "Bold", "size": 11, "color": "#000000"},
    "text_alignment": {"horizontal": "Center", "vertical": "Bottom"},
    "border": "Outside Borders",
    "fill_color": "No Color",
}

# --------------------------
# Schema Definition
# --------------------------

COLUMNS: List[ColumnSchema] = [
    ColumnSchema("A", "Date", "Transaction date", DATE_STYLE, width=12.0),
    ColumnSchema("B", "Item", "Transaction description", TEXT_STYLE, width=30.0),
    ColumnSchema("C", "Withdrawals CR", "Liability / General Credit", EXPENSE_STYLE, width=15.0),
    ColumnSchema("D", "Deposits DR", "Asset / General Debit", EXPENSE_STYLE, width=15.0),
    ColumnSchema("E", "A/R DR", "Accounts Receivable (Asset)", EXPENSE_STYLE, width=15.0),
    ColumnSchema("F", "Shareholder Contribution (CR)", "Equity / Source of Funds", EXPENSE_STYLE, width=15.0),
    ColumnSchema("G", "Shareholder Drawings (DR)", "Equity / Withdrawal", EXPENSE_STYLE, width=15.0),
    ColumnSchema("H", "Revenue CR", "Income", EXPENSE_STYLE, width=15.0),
    ColumnSchema("I", "Office Expenses", "Expense", EXPENSE_STYLE, width=15.0),
    ColumnSchema("J", "Office Rent", "Expense", EXPENSE_STYLE, width=15.0),
    ColumnSchema("K", "Office Utilities", "Expense", EXPENSE_STYLE, width=15.0),
    ColumnSchema("L", "Vehicle Expenses", "Expense", EXPENSE_STYLE, width=15.0),
    ColumnSchema("M", "Accounting Fees", "Expense", EXPENSE_STYLE, width=15.0),
    ColumnSchema("N", "Telephone", "Expense", EXPENSE_STYLE, width=15.0),
    ColumnSchema("O", "Internet", "Expense", EXPENSE_STYLE, width=15.0),
    ColumnSchema("P", "Bank Fees", "Expense", EXPENSE_STYLE, width=15.0),
    ColumnSchema("Q", "Professional Fees", "Expense", EXPENSE_STYLE, width=15.0),
    ColumnSchema("R", "Dental / Medical", "Expense", EXPENSE_STYLE, width=15.0),
    ColumnSchema("S", "Supplies", "Expense", EXPENSE_STYLE, width=15.0),
    ColumnSchema("T", "Food Expenses from Business Meetings", "Expense", EXPENSE_STYLE, width=15.0),
    ColumnSchema("U", "Business Trip", "Expense", EXPENSE_STYLE, width=15.0),
    ColumnSchema("V", "Client Gifts", "Expense", EXPENSE_STYLE, width=15.0),
    ColumnSchema("W", "Marketing Costs", "Expense", EXPENSE_STYLE, width=15.0),
    ColumnSchema("X", "Misc", "Expense", EXPENSE_STYLE, width=15.0),
    ColumnSchema("Y", "Insurance", "Expense", EXPENSE_STYLE, width=15.0),
    ColumnSchema("Z", "Donations", "Expense", EXPENSE_STYLE, width=15.0),
    ColumnSchema(
        "AA",
        "TOTAL",
        "Row balance formula",
        EXPENSE_STYLE,
        formula_template="=+D{row}+SUM(I{row}:Z{row})+E{row}-C{row}-F{row}+G{row}-H{row}",
        width=12.0,
    ),
    ColumnSchema("AB", "Notes", "Manual notes or unclassified transactions", TEXT_STYLE, width=60.0),
]

def get_schema() -> List[ColumnSchema]:
    """Return the full spreadsheet schema."""
    return COLUMNS

def get_column_by_name(name: str) -> ColumnSchema:
    """Lookup a column by its name."""
    for col in COLUMNS:
        if col.name == name:
            return col
    raise KeyError(f"Column not found: {name}")

def get_column_by_letter(letter: str) -> ColumnSchema:
    """Lookup a column by its Excel letter."""
    for col in COLUMNS:
        if col.letter == letter:
            return col
    raise KeyError(f"Column not found: {letter}")

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
    ColumnSchema("A", "Date", "Transaction date", DATE_STYLE),
    ColumnSchema("B", "Item", "Transaction description", TEXT_STYLE),
    ColumnSchema("C", "Withdrawals CR", "Liability / General Credit", EXPENSE_STYLE),
    ColumnSchema("D", "Deposits DR", "Asset / General Debit", EXPENSE_STYLE),
    ColumnSchema("E", "A/R DR", "Accounts Receivable (Asset)", EXPENSE_STYLE),
    ColumnSchema("F", "Shareholder Contribution (CR)", "Equity / Source of Funds", EXPENSE_STYLE),
    ColumnSchema("G", "Shareholder Drawings (DR)", "Equity / Withdrawal", EXPENSE_STYLE),
    ColumnSchema("H", "Revenue CR", "Income", EXPENSE_STYLE),
    ColumnSchema("I", "Office Expenses", "Expense", EXPENSE_STYLE),
    ColumnSchema("J", "Office Rent", "Expense", EXPENSE_STYLE),
    ColumnSchema("K", "Office Utilities", "Expense", EXPENSE_STYLE),
    ColumnSchema("L", "Vehicle Expenses", "Expense", EXPENSE_STYLE),
    ColumnSchema("M", "Accounting Fees", "Expense", EXPENSE_STYLE),
    ColumnSchema("N", "Telephone", "Expense", EXPENSE_STYLE),
    ColumnSchema("O", "Internet", "Expense", EXPENSE_STYLE),
    ColumnSchema("P", "Bank Fees", "Expense", EXPENSE_STYLE),
    ColumnSchema("Q", "Professional Fees", "Expense", EXPENSE_STYLE),
    ColumnSchema("R", "Dental / Medical", "Expense", EXPENSE_STYLE),
    ColumnSchema("S", "Supplies", "Expense", EXPENSE_STYLE),
    ColumnSchema("T", "Food Expenses from Business Meetings", "Expense", EXPENSE_STYLE),
    ColumnSchema("U", "Business Trip", "Expense", EXPENSE_STYLE),
    ColumnSchema("V", "Client Gifts", "Expense", EXPENSE_STYLE),
    ColumnSchema("W", "Marketing Costs", "Expense", EXPENSE_STYLE),
    ColumnSchema("X", "Misc", "Expense", EXPENSE_STYLE),
    ColumnSchema("Y", "Insurance", "Expense", EXPENSE_STYLE),
    ColumnSchema("Z", "Donations", "Expense", EXPENSE_STYLE),
    ColumnSchema(
        "AA",
        "TOTAL",
        "Row balance formula",
        EXPENSE_STYLE,
        formula_template="=+D{row}+SUM(I{row}:Z{row})+E{row}-C{row}-F{row}+G{row}-H{row}"
    ),
    ColumnSchema("AB", "Notes", "Manual notes or unclassified transactions", TEXT_STYLE),
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

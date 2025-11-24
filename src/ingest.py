"""
ingest.py

Handles ingestion of transaction data from CSV files.
Supports two common patterns:
1. Simple Ledger Format (no headers, fixed column positions)
2. Headered Format (with headers, possibly extra columns)

Normalizes into internal structure:
    {"Date": ..., "Description": ..., "Debit": float, "Credit": float}
"""

import csv
from typing import List, Dict, Union
from datetime import datetime

DEFAULT_HEADERS = ["Date", "Description", "Debit", "Credit", "Balance"]

def load_csv(path: str) -> List[Dict]:
    """
    Load transactions from a CSV file and normalize them.
    Detects whether the file has headers or not.
    """
    transactions = []
    with open(path, newline='', encoding="utf-8") as f:
        # Peek at first line
        first_line = f.readline().strip()
        f.seek(0)

        # Heuristic: if first cell looks like a date, assume no headers
        first_cell = first_line.split(",")[0]
        has_headers = not looks_like_date(first_cell)

        if has_headers:
            reader = csv.DictReader(f)
        else:
            reader = csv.DictReader(f, fieldnames=DEFAULT_HEADERS)

        for row in reader:
            tx = normalize_row(row)
            if tx:  # skip empty or malformed rows
                transactions.append(tx)
    return transactions

def normalize_row(row: Dict[str, str]) -> Dict[str, Union[str, float, None]]:
    """
    Normalize a row into expected format.
    Handles both separate Debit/Credit columns and single Amount column.
    """
    date = parse_date(row.get("Date"))
    desc = clean_description(row.get("Description"))

    debit = credit = 0.0

    # Case 1: Separate Debit/Credit columns
    if "Debit" in row or "Credit" in row:
        debit = parse_amount(row.get("Debit"))
        credit = parse_amount(row.get("Credit"))

    # Case 2: Single Amount column (positive=credit, negative=debit)
    elif "Amount" in row:
        amt = parse_amount(row.get("Amount"))
        if amt < 0:
            debit = abs(amt)
        else:
            credit = amt

    return {
        "Date": date,
        "Description": desc,
        "Debit": debit,
        "Credit": credit,
    }

def parse_date(value: Union[str, None]):
    """Try multiple date formats, return ISO string YYYY-MM-DD."""
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%y", "%d-%m-%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return value.strip()  # fallback: return raw

def clean_description(value: Union[str, None]) -> str:
    """Normalize description text."""
    if not value:
        return ""
    return " ".join(value.strip().split())

def parse_amount(value: Union[str, None]) -> float:
    """Convert amount string to float, handle commas, blanks."""
    if not value:
        return 0.0
    try:
        return float(value.replace(",", "").strip())
    except ValueError:
        return 0.0

def looks_like_date(value: str) -> bool:
    """Heuristic: check if a string looks like a date."""
    if not value:
        return False
    return value[0].isdigit() and any(sep in value for sep in ("-", "/", "."))

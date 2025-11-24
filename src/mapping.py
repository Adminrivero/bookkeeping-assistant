"""
mapping.py

Provides functions to map classified transactions into the spreadsheet schema.
"""

from src.spreadsheet_schema import get_schema
from typing import Any

def map_transaction_to_row(raw_tx: dict, classification: dict, row_idx: int) -> dict:
    """
    Map a raw transaction and its classification result into a row dict
    keyed by schema column names.

    Args:
        raw_tx: dict with raw transaction fields (e.g., {"Date": ..., "Description": ..., "Debit": ..., "Credit": ...})
        classification: dict returned by TransactionClassifier.classify()
        row_idx: int row number (used for formulas in TOTAL column)

    Returns:
        dict mapping schema column names -> values (or None if not applicable).
    """
    schema = get_schema()
    row = {col.name: None for col in schema}
    row: dict[str, Any] = row

    # Always map base fields
    row["Date"] = raw_tx.get("Date")
    row["Item"] = raw_tx.get("Description")

    # Handle dual-entry mapping
    dual_entry = classification.get("dual_entry")
    tx_type = classification.get("transaction_type")

    # Determine amount (Debit or Credit from raw_tx)
    amount = None
    if tx_type in ["EXPENSE", "MANUAL_CR"]:
        amount = raw_tx.get("Debit")
    elif tx_type in ["INCOME", "MANUAL_DR", "INCOME_TO_OFFSET_EXPENSE"]:
        amount = raw_tx.get("Credit")

    if amount is not None and dual_entry:
        apply_pct = dual_entry.get("APPLY_PERCENTAGE", 1.0)
        adjusted_amount = float(amount) * float(apply_pct)

        dr_col = dual_entry.get("DR_COLUMN")
        cr_col = dual_entry.get("CR_COLUMN")

        if dr_col:
            row[dr_col["name"]] = adjusted_amount
        if cr_col:
            row[cr_col["name"]] = adjusted_amount

    # Notes column for unclassified or manual review
    if classification["transaction_type"] in ["MANUAL_CR", "MANUAL_DR"]:
        row["Notes"] = f"Please, review unclassified transaction: {raw_tx.get('Description')}"
        row["highlight"] = True
    
    # Notes column for ignored transactions
    if classification["transaction_type"] == "IGNORE_TRANSACTION":
        row["Notes"] = f"Ignored transaction: {raw_tx.get('Description', 'item') + ' -> ' + str(raw_tx.get('Debit') or raw_tx.get('Credit'))}"
        row["ignore"] = True

    # TOTAL column formula will be inserted by exporter (formula_template)
    return row

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
    
    # Distinguish credit-card vs bank-account visually in Item text
    description = raw_tx.get("Description", "")
    source = raw_tx.get("source")
    is_credit_card_source = source == "credit_card"

    if is_credit_card_source:
        row["Item"] = f"{description} (Credit-Card)"
        row["credit_card_source"] = True
    else:
        row["Item"] = description

    # Handle dual-entry mapping
    dual_entry = classification.get("dual_entry")
    tx_type = classification.get("transaction_type")
    tx_category = classification.get("category")

    # Determine amount (Debit or Credit from raw_tx)
    amount = None
    if tx_type in ["EXPENSE", "MANUAL_CR"]:
        amount = raw_tx.get("Debit")
    elif tx_type in ["INCOME", "MANUAL_DR", "INCOME_TO_OFFSET_EXPENSE"]:
        amount = raw_tx.get("Credit")

    # Primary path: dual_entry present
    if amount is not None and dual_entry:
        apply_pct = dual_entry.get("APPLY_PERCENTAGE", 1.0)
        adjusted_amount = float(amount) * float(apply_pct)

        dr_col = dual_entry.get("DR_COLUMN")
        cr_col = dual_entry.get("CR_COLUMN")

        if dr_col:
            row[dr_col["name"]] = adjusted_amount
        if cr_col:
            row[cr_col["name"]] = adjusted_amount
    
    # Fallback path: no dual_entry but we still have an amount to book
    elif amount is not None and not dual_entry:
        if tx_type == "MANUAL_CR" and tx_category == "Unclassified":
            # Manual credit (expense)
            row["Withdrawals CR"] = float(amount)
        elif tx_type == "MANUAL_DR" and tx_category == "Unclassified":
            # Manual debit (income)
            row["Deposits DR"] = float(amount)

    # Notes column for unclassified or manual review
    if classification["transaction_type"] in ["MANUAL_CR", "MANUAL_DR"]:
        row["Notes"] = f"Please, review unclassified transaction: {raw_tx.get('Description')}"
        row["highlight"] = True
    
    # Notes column for ignored transactions
    if classification["transaction_type"] == "IGNORE_TRANSACTION":
        row["Notes"] = (
            "Ignored transaction: "
            + raw_tx.get("Description", "item")
            + " -> "
            + str(raw_tx.get("Debit") or raw_tx.get("Credit"))
        )
        row["ignore"] = True

    # TOTAL column formula will be inserted by exporter (formula_template)
    return row

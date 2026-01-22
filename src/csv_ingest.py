"""
csv_ingest.py
-------------
CSV ingestion pipeline for bank statements.

This module handles CSV inputs, validates them against the bank profile config,
and normalizes transactions into a unified dict structure consistent with PDF ingestion.
"""
import csv
import logging
from datetime import datetime
from src.utils import normalize_tx_to_canonical_shape


def parse_csv(file_path, profile):
    """
    Parse a CSV statement into normalized transactions.

    Args:
        file_path (Path or str): Path to the CSV file.
        profile (dict): Bank profile config (with optional 'csv_format').

    Returns:
        list[dict]: Normalized transaction dictionaries.
    """
    transactions = []

    csv_config = profile.get("csv_format")
    if not csv_config:
        raise ValueError(f"Bank profile {profile['bank_name']} does not support CSV ingestion")

    cols = csv_config["columns"]
    date_format = csv_config.get("date_format", "YYYY-MM-DD")

    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or len(row) < len(cols):
                continue

            try:
                tx = {
                    "source": profile["bank_name"],
                    "section": "Transactions"
                }

                for field, idx in cols.items():
                    if idx >= len(row):
                        continue
                    value = row[idx].strip()

                    # Normalize date
                    if field == "transaction_date":
                        if date_format == "MM/DD/YYYY":
                            tx[field] = datetime.strptime(value, "%m/%d/%Y").strftime("%Y-%m-%d")
                        else:
                            tx[field] = value

                    # Normalize debit/credit to unified amount
                    elif field in ("debit", "credit"):
                        tx[field] = float(value) if value else 0.0

                    elif field == "amount":
                        tx[field] = float(value.replace(",", "").replace("$", "")) if value else 0.0

                    elif field == "balance":
                        tx[field] = float(value) if value else None

                    else:
                        tx[field] = value

                # If debit/credit present, compute unified amount
                if "debit" in tx or "credit" in tx:
                    debit = tx.get("debit", 0.0)
                    credit = tx.get("credit", 0.0)
                    tx["amount"] = debit - credit

                # Skip footer rows if flagged
                if csv_config.get("skip_footer_rows", False):
                    desc = tx.get("description", "").upper()
                    if "TOTAL" in desc or "BALANCE" in desc:
                        continue

                transactions.append(tx)

            except Exception as e:
                logging.warning("Skipping malformed row: %s | Error: %s", row, e)

    logging.info("Parsed %d transactions from CSV for %s", len(transactions), profile["bank_name"])
    
    # Normalize to canonical raw_tx shape
    source_type = profile.get("source_type", "credit_card")
    normalized = [
        normalize_tx_to_canonical_shape(tx, source_type=source_type)
        for tx in transactions
    ]
    
    return normalized

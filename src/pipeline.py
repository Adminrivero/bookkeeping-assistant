"""
pipeline.py

Defines the orchestration pipeline for bookkeeping automation:
1. Load rules
2. Classify transactions
3. Map to spreadsheet schema
4. Export to Excel workbook
"""

from src.rules import RuleLoader
from src.classify import TransactionClassifier
from src.mapping import map_transaction_to_row
from src.export import SpreadsheetExporter

def run_pipeline(transactions, rules_file, start_row: int = 4):
    """
    Full pipeline: classify transactions and export to Excel workbook.

    Args:
        transactions: list of dicts (raw CSV rows normalized)
        rules_file: path to allocation_rules.json
        start_row: row index where data begins (default: 4)

    Returns:
        openpyxl Workbook object
    """
    # Load rules
    loader = RuleLoader(rules_file)
    rules = loader.load()
    classifier = TransactionClassifier(rules)

    # Build exporter
    exporter = SpreadsheetExporter()
    exporter.build_headers()

    # Process transactions
    for idx, tx in enumerate(transactions, start=start_row):
        classification = classifier.classify(tx)
        row = map_transaction_to_row(tx, classification, idx)
        exporter.write_transaction(idx, row)

    # Add totals row
    exporter.finalize_totals_row(start_row, idx) # type: ignore

    return exporter.wb

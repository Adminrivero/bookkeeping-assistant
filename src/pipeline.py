"""
pipeline.py

Defines the orchestration pipeline for bookkeeping automation:
1. Load rules
2. Classify transactions
3. Map to spreadsheet schema
4. Export to Excel workbook
"""

from tqdm import tqdm
from src.rules import RuleLoader
from src.classify import TransactionClassifier
from src.mapping import map_transaction_to_row
from src.export import SpreadsheetExporter

def run_pipeline(transactions, rules_file, start_row: int = 4, show_progress: bool = True):
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
    if show_progress:
        print("[1/4] Loading rules...")
    loader = RuleLoader(rules_file)
    rules = loader.load()
    classifier = TransactionClassifier(rules)
    if show_progress:
        print("    ✅ Rules loaded")

    # Build exporter
    if show_progress:
        print("[2/4] Building exporter...")
    exporter = SpreadsheetExporter()
    exporter.build_headers()
    if show_progress:
        print("    ✅ Exporter ready")

    # Process transactions
    if show_progress:
        print("[3/4] Classifying and mapping transactions...")
    iterator = tqdm(transactions, desc="Processing", unit="tx") if show_progress else transactions
    for idx, tx in enumerate(iterator, start=start_row):
        classification = classifier.classify(tx)
        row = map_transaction_to_row(tx, classification, idx)
        exporter.write_transaction(idx, row)
    if show_progress:
        print("    ✅ Transactions classified and mapped")

    # Add totals row
    if show_progress:
        print("[4/4] Finalizing totals row...")
    exporter.finalize_totals_row(start_row, idx) # type: ignore
    if show_progress:
        print("    ✅ Totals row complete")

    return exporter.wb

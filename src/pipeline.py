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
from src.utils import notify

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
        notify("[1/4] Loading rules...", level="info")
    loader = RuleLoader(rules_file)
    rules = loader.load()
    classifier = TransactionClassifier(rules)
    if show_progress:
        notify("    ✅ Rules loaded", level="info")

    # Build exporter
    if show_progress:
        notify("[2/4] Building exporter...", level="info")
    exporter = SpreadsheetExporter()
    exporter.build_headers()
    if show_progress:
        notify("    ✅ Exporter ready", level="info")

    # Process transactions
    if show_progress:
        notify("[3/4] Classifying and mapping transactions...", level="info")
    iterator = tqdm(transactions, desc="Processing", unit="tx") if show_progress else transactions
    end_row = start_row - 1
    for idx, tx in enumerate(iterator, start=start_row):
        classification = classifier.classify(tx)
        row = map_transaction_to_row(tx, classification, idx)
        exporter.write_transaction(idx, row)
        end_row = idx
    if show_progress:
        notify("    ✅ Transactions classified and mapped", level="info")

    # Add totals row
    if show_progress:
        notify("[4/4] Finalizing totals row...", level="info")
    if end_row >= start_row:
        exporter.finalize_totals_row(start_row, end_row)
        if show_progress:
            notify("    ✅ Totals row complete", level="info")
    else:
        if show_progress:
            notify("    ⚠️ No transactions, skipping totals row", level="warning")

    return exporter.wb

"""
pipeline.py
-----------
Pipeline entrypoint for statement ingestion.
Routes input files to the correct ingestor (CSV or PDF), ensures normalized output, and handles errors gracefully.
Defines the orchestration pipeline for bookkeeping automation:
1. Load rules
2. Classify transactions
3. Map to spreadsheet schema
4. Export to Excel workbook
"""
import pathlib
from tqdm import tqdm
from typing import Optional
from src.rules import RuleLoader
from src.classify import TransactionClassifier
from src.mapping import map_transaction_to_row
from src.export import SpreadsheetExporter
from src.utils import notify, load_bank_profile
from src import pdf_ingest, csv_ingest
from src import ingest as ingest_module


def ingest_statement(file_path, bank: str, tax_year: Optional[int] = None):
    """
    Ingest a statement file (CSV or PDF) and normalize to unified transactions.
    """
    path = pathlib.Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Statement file not found: {file_path}")

    suffix = path.suffix.lower()
    
    # Special case: root account CSVs
    if bank == "account" and suffix == ".csv":
        notify("Detected account CSV input", level="info")
        return ingest_module.load_csv(str(path))
    
    # Credit card banks: require profile
    profile = load_bank_profile(bank)

    if suffix == ".csv":
        notify(f"Detected CSV input for {bank}", level="info")
        return csv_ingest.parse_csv(path, profile)

    elif suffix == ".pdf":
        notify(f"Detected PDF input for {bank}", level="info")
        return pdf_ingest.parse_pdf(path, bank, tax_year=tax_year)

    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def run_pipeline(transactions, rules_file, start_row: int = 4, show_progress: bool = True, tax_year: Optional[int] = None):
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
    exporter.set_tax_year(tax_year or "N/A")
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
        # Add totals only if there are transactions
        exporter.finalize_totals_row(start_row, end_row)
        # Add color guide 5 rows below last transaction row
        exporter.add_color_legend(end_row, separation=5)
        if show_progress:
            notify("    ✅ Totals row complete", level="info")
    else:
        if show_progress:
            notify("    ⚠️ No transactions, skipping totals row", level="warning")

    return exporter.wb

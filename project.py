"""
Bookkeeping Assistant - Main Entry Point (project.py)

This script provides a command-line interface (CLI) to run the bookkeeping
pipeline. It handles:
- Parsing command-line arguments (year, rules path).
- Validating the environment (input directories and files).
- Loading allocation rules.
- Orchestrating the pipeline (ingest -> classify -> map -> export).
"""

# --- Standard Libraries ---
import argparse
import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, List
# --- Third-Party Libraries ---
from pathlib import Path
# -- Local Project Imports ---
from src.ingest import load_csv
from src.pipeline import ingest_statement, run_pipeline
from src.utils import notify, use_logging, load_rules, setup_paths

def main():
    """
    Orchestrates the bookkeeping pipeline from the command line.
    1. Parses arguments.
    2. Sets up environment paths and validates inputs.
    3. Loads allocation rules.
    4. Ingests CSV transactions.
    5. Executes the pipeline and saves output.
    """
    args = get_cli_args()
    
    # Enable logging if flag is set
    if args.log:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[logging.StreamHandler()]
        )
        # Toggle global flag
        use_logging = True
    
    # Load rules
    try:
        rules = load_rules(args.rules)
    except (FileNotFoundError, json.JSONDecodeError, TypeError) as e:
        notify(f"RulesError: {e}", level="error")
        sys.exit(1)
    
    # Discover files
    try:
        file_list = discover_files(args.year, args.bank)
    except FileNotFoundError as e:
        notify(f"EnvironmentError: {e}", level="error")
        sys.exit(1)
    
    # Ingest transactions
    transactions = []
    for file_path, bank in file_list:
        try:
            txs = ingest_statement(file_path, bank, tax_year=args.year)
            transactions.extend(txs)
            notify(f"    ✅ Ingested {len(txs)} from {file_path}", level="info")
        except Exception as e:
            notify(f"Error ingesting {file_path}: {e}", level="error")
            sys.exit(1)
    
    # Define output path
    output_dir = Path("output") / str(args.year)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"bookkeeping_{args.year}.xlsx"
    
    # Conditionally show progress
    if not args.no_progress:
        notify(f"Starting pipeline for year {args.year}...", level="info")
        notify(f"Input files found: {len(file_list)}", level="info")
        notify(f"Transactions loaded: {len(transactions)}", level="info")
        notify(f"Rules loaded from: {args.rules}", level="info")
        notify(f"Output will be saved to: {output_file}", level="info")

    # Run pipeline
    wb = run_pipeline(transactions, args.rules, show_progress=(not args.no_progress))
    wb.save(output_file)

    notify(f"\n✅ Success! Pipeline complete. File saved to {output_file}", level="info")


def get_cli_args() -> argparse.Namespace:
    """Parse and return command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Bookkeeping Assistant: Process bank CSVs into a final bookkeeping spreadsheet.",
        epilog="Example: python project.py --year 2025 --rules config/my_rules.json"
    )
    parser.add_argument(
        "-y",
        "--year",
        type=int,
        default=datetime.now().year,
        help="Target financial year to process (default: current year)."
    )
    parser.add_argument(
        "-b",
        "--bank",
        nargs="+",
        default=[],
        help="List of bank profile IDs (e.g., 'triangle cibc td_visa')")
    parser.add_argument(
        "-r",
        "--rules",
        type=Path,
        default=Path("config/allocation_rules.json"),
        help="Path to the JSON allocation rules file (default: config/allocation_rules.json)."
    )
    parser.add_argument(
        "-l",
        "--log",
        dest="log",
        action="store_true",
        help="Enable logging output instead of print statements."
    )
    parser.add_argument(
        "-q",
        "--no-progress",
        action="store_true",
        help="Disable progress bars and verbose status messages."
    )
    return parser.parse_args()


def discover_files(year: int, banks: list[str]) -> list[tuple[Path, str]]:
    """
    Discover statement files for the given year and banks.

    Returns:
        list of (file_path, bank_id) tuples
    """
    input_dir, _, csv_files = setup_paths(year)
    files = []

    # Ingest root CSVs (bank accounts activity)
    for f in csv_files:
        files.append((f, "account"))

    # Ingest statements for each bank subfolders (credit card statements)
    for bank in banks:
        bank_dir = input_dir / bank
        if not bank_dir.exists():
            notify(f"⚠️ Bank directory not found: {bank_dir}", level="warning")
            continue
        for f in bank_dir.glob("*.*"):
            if f.suffix.lower() in [".csv", ".pdf"]:
                files.append((f, bank))

    return files


if __name__ == "__main__":
    main()
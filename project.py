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
# --- Third-Party / External ---
from pathlib import Path
# -- Local Project Imports ---
from src.ingest import load_csv
from src.pipeline import run_pipeline
from src.utils import notify, use_logging, load_rules

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
    
    try:
        input_dir, output_dir, input_files = setup_paths(args.year)
    except FileNotFoundError as e:
        notify(f"EnvironmentError: {e}", level="error")
        # print("Please ensure the required data directory exists and contains CSV files.")
        sys.exit(1)
    
    try:
        rules = load_rules(args.rules)
    except (FileNotFoundError, json.JSONDecodeError, TypeError) as e:
        notify(f"RulesError: {e}", level="error")
        # print("Please ensure the rules file exists and is a valid JSON.")
        sys.exit(1)
    
    # Ingest transactions from all CSV files
    transactions = []
    for csv_file in input_files:
        try:
            txs = load_csv(str(csv_file))
            transactions.extend(txs)
        except Exception as e:
            notify(f"Error loading CSV {csv_file}: {e}", level="error")
            sys.exit(1)
    
    # Define the final output file path
    output_file = output_dir / f"bookkeeping_{args.year}.xlsx"
    
    # Conditionally show progress
    if not args.no_progress:
        notify(f"Starting pipeline for year {args.year}...", level="info")
        notify(f"Input files found: {len(input_files)}", level="info")
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
        "-r",
        "--rules",
        type=Path,
        default=Path("config/allocation_rules.json"),
        help="Path to the JSON allocation rules file (default: config/allocation_rules.json)."
    )
    parser.add_argument(
        "-q",
        "--no-progress",
        action="store_true",
        help="Disable progress bars and verbose status messages."
    )
    parser.add_argument(
        "-l",
        "--log",
        dest="log",
        action="store_true",
        help="Enable logging output instead of print statements."
    )
    return parser.parse_args()


def setup_paths(year: int) -> tuple[Path, Path, List[Path]]:
    """Validate input directory, find CSVs, and create output directory."""
    input_dir = Path(f"data/{year}")
    if not input_dir.exists() or not input_dir.is_dir():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    input_files = list(input_dir.glob("*.csv"))
    if not input_files:
        raise FileNotFoundError(f"No CSV files found in input directory: {input_dir}")
    
    output_dir = Path(f"output/{year}")
    output_dir.mkdir(parents=True, exist_ok=True)

    return input_dir, output_dir, input_files


if __name__ == "__main__":
    main()